"""User management and staff registration endpoints."""

from datetime import datetime, timedelta

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import (
    COLLEGE_ROLES,
    DEPARTMENT_ROLES,
    GLOBAL_ROLES,
    get_current_user,
    get_password_hash,
    is_college_user,
    is_department_user,
    is_global_user,
    require_roles,
    verify_password,
)
from app.crud.records import log_action, paginate
from app.models import Department, StaffRegistration, User
from app.schemas import BulkUserCreate, PasswordChange, StaffRegisterRequest, StaffRegisterVerify, UserCreate
from app.schemas.records import UserOut
from app.services.email import generate_otp, send_email

router = APIRouter(tags=["Users"])


@router.post("/api/users", response_model=dict)
def create_user(
    data: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "dean"))
):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_email = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Global admins can create any role; deans can only create department-scoped staff
    if is_college_user(user):
        if data.role not in DEPARTMENT_ROLES:
            raise HTTPException(status_code=403, detail="Deans can only create HOD, records officer, or lecturer accounts")
        if data.college_id is None or data.college_id != user.college_id:
            raise HTTPException(status_code=403, detail="Deans can only create users in their own college")
        dept = db.query(Department).filter(Department.id == data.department_id).first()
        if dept is None or dept.college_id != user.college_id:
            raise HTTPException(status_code=403, detail="Deans can only assign departments within their college")

    # Only global admins can create other global admins or users without a college
    if data.role in GLOBAL_ROLES and data.college_id is None:
        if not is_global_user(user):
            raise HTTPException(status_code=403, detail="Only registrar/admin can create global users")

    # Validate scope fields based on role
    if data.role in DEPARTMENT_ROLES and data.department_id is None:
        raise HTTPException(status_code=400, detail="Department is required for this role")
    if data.role in COLLEGE_ROLES and data.college_id is None:
        raise HTTPException(status_code=400, detail="College is required for this role")

    force_password_change = data.role in ("dean", "hod")

    new_user = User(
        username=data.username,
        full_name=data.full_name,
        email=data.email.lower().strip(),
        phone=data.phone,
        department=data.department,
        college_id=data.college_id,
        department_id=data.department_id,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        is_active=True,
        force_password_change=force_password_change,
    )
    db.add(new_user)
    db.commit()
    log_action(
        db,
        user.username,
        "CREATE",
        "users",
        new_user.id,
        f"Created user {data.username} ({new_user.email}) with role {data.role} college_id={new_user.college_id} department_id={new_user.department_id}",
    )
    return {
        "message": "User created successfully",
        "username": data.username,
        "email": new_user.email,
        "role": new_user.role,
        "college_id": new_user.college_id,
        "department_id": new_user.department_id,
        "force_password_change": new_user.force_password_change,
    }


@router.get("/api/users", response_model=List[UserOut])
def list_users(
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    college_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "dean", "hod", "records_officer", "lecturer")),
):
    query = db.query(User)

    # Scope results based on current user's role
    if is_global_user(current_user):
        pass  # can see all
    elif is_college_user(current_user):
        query = query.filter(User.college_id == current_user.college_id)
    else:
        query = query.filter(User.department_id == current_user.department_id)

    # Apply requested filters (respecting scope)
    if role:
        query = query.filter(User.role == role)
    if college_id is not None:
        if not is_global_user(current_user) and college_id != current_user.college_id:
            raise HTTPException(status_code=403, detail="Cannot filter by that college")
        query = query.filter(User.college_id == college_id)
    if department_id is not None:
        if is_department_user(current_user) and department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Cannot filter by that department")
        query = query.filter(User.department_id == department_id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (User.username.ilike(like))
            | (User.full_name.ilike(like))
            | (User.email.ilike(like))
        )

    return paginate(query.order_by(User.created_at.desc()), skip, limit).all()


@router.post("/api/users/change-password", response_model=dict)
def change_staff_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = get_password_hash(data.new_password)
    user.force_password_change = False
    db.commit()
    log_action(db, user.username, "PASSWORD_CHANGE", "users", user.id, "Password changed by user")
    return {"message": "Password changed successfully"}


@router.post("/api/users/bulk", response_model=dict)
def bulk_create_users(
    data: BulkUserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "dean")),
):
    created = 0
    failed = 0
    usernames = []
    errors = []

    for item in data.users:
        try:
            # Dean restrictions
            if is_college_user(user):
                if item.role not in DEPARTMENT_ROLES:
                    raise ValueError("Deans can only create HOD, records officer, or lecturer accounts")
                if item.college_id != user.college_id:
                    raise ValueError("Deans can only create users in their own college")
                dept = db.query(Department).filter(Department.id == item.department_id).first()
                if dept is None or dept.college_id != user.college_id:
                    raise ValueError("Deans can only assign departments within their college")

            if item.role in DEPARTMENT_ROLES and item.department_id is None:
                raise ValueError("Department is required for this role")
            if item.role in COLLEGE_ROLES and item.college_id is None:
                raise ValueError("College is required for this role")
            if db.query(User).filter(User.username == item.username).first():
                raise ValueError(f"Username {item.username} already exists")
            if db.query(User).filter(User.email == item.email.lower().strip()).first():
                raise ValueError(f"Email {item.email} already exists")

            password = item.password or f"CalebStaff{item.role.title()}"
            new_user = User(
                username=item.username,
                full_name=item.full_name,
                email=item.email.lower().strip(),
                phone=item.phone,
                college_id=item.college_id,
                department_id=item.department_id,
                hashed_password=get_password_hash(password),
                role=item.role,
                is_active=True,
                force_password_change=item.role in ("dean", "hod"),
            )
            db.add(new_user)
            db.commit()
            usernames.append(item.username)
            created += 1
            log_action(
                db,
                user.username,
                "CREATE",
                "users",
                new_user.id,
                f"Bulk created user {item.username} ({item.email}) with role {item.role}",
            )
        except Exception as e:
            db.rollback()
            failed += 1
            errors.append(f"{item.username}: {str(e)}")

    log_action(
        db,
        user.username,
        "BULK_CREATE",
        "users",
        None,
        f"Bulk created {created} users, {failed} failed",
    )
    return {"created": created, "failed": failed, "usernames": usernames, "errors": errors}


@router.post("/api/staff/register-request", response_model=dict)
@limiter.limit("10/minute")
def staff_register_request(request: Request, data: StaffRegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A staff account with this email already exists")
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Remove any pending registration for this email
    db.query(StaffRegistration).filter(StaffRegistration.email == email).delete()

    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=15)
    registration = StaffRegistration(
        username=data.username,
        full_name=data.full_name,
        email=email,
        phone=data.phone,
        department=data.department,
        college_id=data.college_id,
        department_id=data.department_id,
        hashed_password=get_password_hash(data.password),
        role="records_officer",
        otp=otp,
        expires_at=expires,
    )
    db.add(registration)
    db.commit()

    body = f"""Hello {data.full_name or data.username},

You are registering for a CU-Records staff account.

Your one-time verification code is: {otp}

This code expires in 15 minutes.

If you did not request this, please ignore this email.

Caleb University Records Team
For God and Humanity
"""
    send_email(email, "CU-Records Staff Registration OTP", body)
    return {"message": "Verification code sent to your email"}


@router.post("/api/staff/register-verify", response_model=dict)
def staff_register_verify(data: StaffRegisterVerify, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    registration = (
        db.query(StaffRegistration)
        .filter(
            StaffRegistration.email == email,
            StaffRegistration.otp == data.otp.strip(),
            StaffRegistration.verified == False,
            StaffRegistration.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not registration:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A staff account with this email already exists")

    new_user = User(
        username=registration.username,
        full_name=registration.full_name,
        email=registration.email,
        phone=registration.phone,
        department=registration.department,
        college_id=registration.college_id,
        department_id=registration.department_id,
        hashed_password=registration.hashed_password,
        role="records_officer",
        is_active=True,
    )
    db.add(new_user)
    registration.verified = True
    db.commit()
    log_action(
        db,
        "system",
        "CREATE",
        "users",
        new_user.id,
        f"Self-registered staff user {new_user.username} ({new_user.email}) with role records_officer via OTP verification",
    )
    return {"message": "Staff account created successfully", "username": new_user.username, "email": new_user.email}
