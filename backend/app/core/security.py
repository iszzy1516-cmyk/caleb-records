"""Authentication, authorization, password hashing, and college-scope helpers."""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Student, User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

GLOBAL_ROLES = {"admin", "registrar"}
COLLEGE_ROLES = {"dean"}
DEPARTMENT_ROLES = {"hod", "records_officer", "lecturer"}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Student:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        matric: str = payload.get("sub")
        token_type: str = payload.get("type")
        if matric is None or token_type != "student":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    student = db.query(Student).filter(Student.matric_number == matric).first()
    if student is None or student.status != "active":
        raise credentials_exception
    return student


def get_current_user_or_student(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        token_type: str = payload.get("type")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if token_type == "student":
        student = db.query(Student).filter(Student.matric_number == sub).first()
        if student is None or student.status != "active":
            raise credentials_exception
        return {"type": "student", "actor": student}

    user = db.query(User).filter(User.email == sub).first()
    if user is None or not user.is_active:
        raise credentials_exception
    require_password_changed(user)
    return {"type": "staff", "actor": user}


def get_current_staff(user: User = Depends(get_current_user)) -> User:
    """Authenticated staff user who has completed any required password change."""
    require_password_changed(user)
    return user


def require_password_changed(user: User) -> None:
    """Raise 403 if the staff user has not changed their temporary password."""
    if user.force_password_change:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must change your password before using this feature.",
            headers={"X-Force-Password-Change": "true"},
        )


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)):
        require_password_changed(user)
        if user.role not in roles and user.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return checker


def is_global_user(user: User) -> bool:
    return user.role in GLOBAL_ROLES


def is_college_user(user: User) -> bool:
    return user.role in COLLEGE_ROLES


def is_department_user(user: User) -> bool:
    return user.role in DEPARTMENT_ROLES


def ensure_college_access(user: User, college_id: Optional[int]):
    """Raise 403 if user is college/department-scoped and college_id does not match."""
    if is_global_user(user):
        return
    if college_id is None or college_id != user.college_id:
        raise HTTPException(status_code=403, detail="You do not have access to this college")


def ensure_department_access(user: User, department_id: Optional[int]):
    """Raise 403 if user is department-scoped and department_id does not match."""
    if is_global_user(user) or is_college_user(user):
        return
    if department_id is None or department_id != user.department_id:
        raise HTTPException(status_code=403, detail="You do not have access to this department")


def apply_college_scope(query, user: User, model=Student):
    """Filter a query by college_id for non-global staff users."""
    if is_global_user(user):
        return query
    return query.filter(model.college_id == user.college_id)


def apply_department_scope(query, user: User, model=Student):
    """Filter a query by department_id for department-scoped staff users."""
    if is_department_user(user):
        return query.filter(model.department_id == user.department_id)
    return query


def apply_staff_scope(query, user: User, model=Student):
    """Apply the appropriate college or department scope based on user role."""
    query = apply_college_scope(query, user, model)
    query = apply_department_scope(query, user, model)
    return query
