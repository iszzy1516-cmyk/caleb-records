"""Student password reset endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_password_hash
from app.crud.records import log_action
from app.models import PasswordReset, Student
from app.schemas import PasswordResetConfirm, PasswordResetRequest
from app.services.email import generate_reset_token, send_email

router = APIRouter(tags=["Password Reset"])


@router.post("/api/password-reset-request", response_model=dict)
@limiter.limit("3/minute")
def request_password_reset(
    request: Request, data: PasswordResetRequest, db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.matric_number == data.matric_number.upper()).first()
    if not student or not student.email:
        return {"message": "If your matric number is registered with an email, you will receive a reset link."}

    token = generate_reset_token()
    expires = datetime.utcnow() + timedelta(hours=1)

    reset = PasswordReset(
        student_id=student.id,
        token=token,
        expires_at=expires,
    )
    db.add(reset)
    db.commit()

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = f"""Hello {student.first_name},

You requested a password reset for your CU-Records account.

Matric Number: {student.matric_number}
Reset Link: {reset_url}

This link expires in 1 hour.

If you did not request this, please ignore this email.

Caleb University Records Team
For God and Humanity
"""

    sent = send_email(student.email, "CU-Records Password Reset", body)
    if sent:
        log_action(db, student.matric_number, "PASSWORD_RESET_REQUEST", "password_resets", reset.id, "Reset requested")

    return {"message": "If your matric number is registered with an email, you will receive a reset link."}


@router.post("/api/password-reset", response_model=dict)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.token == data.token,
            PasswordReset.used == False,
            PasswordReset.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    student = db.query(Student).filter(Student.id == reset.student_id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")

    student.hashed_password = get_password_hash(data.new_password)
    reset.used = True
    db.commit()

    log_action(db, student.matric_number, "PASSWORD_RESET", "students", student.id, "Password reset successfully")
    return {"message": "Password reset successfully. You can now log in with your new password."}
