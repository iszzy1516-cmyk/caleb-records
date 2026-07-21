"""Authentication endpoints for staff and students."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.models import Student, User
from app.schemas import StudentToken, Token

router = APIRouter(tags=["Auth"])


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "type": "staff"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "college_id": user.college_id,
        "college_name": (
            user.college.name
            if user.college
            else ("All Colleges" if user.role in ("admin", "registrar") else None)
        ),
        "department_id": user.department_id,
        "department_name": user.department_rel.name if user.department_rel else None,
        "force_password_change": user.force_password_change,
    }


@router.post("/token/student", response_model=StudentToken)
@limiter.limit("5/minute")
def student_login(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.matric_number == form_data.username.upper()).first()
    if not student or not student.hashed_password:
        raise HTTPException(status_code=400, detail="Invalid matric number or password")
    if not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid matric number or password")
    if student.status != "active":
        raise HTTPException(status_code=400, detail="Student account is inactive")

    access_token = create_access_token(data={"sub": student.matric_number, "type": "student"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "matric_number": student.matric_number,
        "full_name": f"{student.first_name} {student.last_name}",
    }
