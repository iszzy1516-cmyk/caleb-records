"""Student self-service endpoints under /api/me."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_student, verify_password
from app.crud.records import (
    calculate_cgpa,
    check_deadline_and_fee,
    log_action,
    paginate,
)
from app.models import AcademicRecord, Alert, Document, Student, StudentPayment
from app.schemas import (
    AcademicRecordOut,
    AlertOut,
    DocumentOut,
    PasswordChange,
    StudentDetailOut,
    StudentPaymentCreate,
    StudentPaymentOut,
)
from app.schemas.records import CollegeOut, DepartmentOut, ProgramOut
from app.services.documents import save_upload_file, verify_and_create_document

router = APIRouter(prefix="/api/me", tags=["Me"])


@router.get("", response_model=StudentDetailOut)
def get_me(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    student = (
        db.query(Student)
        .options(
            joinedload(Student.college),
            joinedload(Student.department),
            joinedload(Student.program),
            joinedload(Student.documents),
            joinedload(Student.academic_records).joinedload(AcademicRecord.course),
        )
        .filter(Student.id == student.id)
        .first()
    )
    cgpa = calculate_cgpa(db, student.id)
    return StudentDetailOut(
        id=student.id,
        matric_number=student.matric_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        phone=student.phone,
        college_id=student.college_id,
        department_id=student.department_id,
        program_id=student.program_id,
        admission_year=student.admission_year,
        current_level=student.current_level,
        gender=student.gender,
        date_of_birth=student.date_of_birth,
        status=student.status,
        created_at=student.created_at,
        college=CollegeOut.model_validate(student.college) if student.college else None,
        department=DepartmentOut.model_validate(student.department) if student.department else None,
        program=ProgramOut.model_validate(student.program) if student.program else None,
        documents=[DocumentOut.model_validate(d) for d in student.documents],
        academic_records=[AcademicRecordOut.model_validate(r) for r in student.academic_records],
        cgpa=cgpa,
    )


@router.post("/documents", response_model=DocumentOut)
def upload_my_document(
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    session: Optional[str] = Form(None),
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    late_fee = check_deadline_and_fee(db, student.id, document_type, level)
    if late_fee and late_fee > 0:
        paid = db.query(StudentPayment).filter(
            StudentPayment.student_id == student.id,
            StudentPayment.payment_type == f"late_fee_{document_type}_{level or 'none'}",
        ).first()
        if not paid:
            raise HTTPException(
                status_code=400,
                detail=f"Document upload deadline has passed. A late fee of ₦{late_fee:,.2f} must be paid before uploading.",
            )

    saved = save_upload_file(file, student, document_type, level, session)
    return verify_and_create_document(db, student, document_type, level, session, file, saved, student.matric_number)


@router.get("/grades")
def get_my_grades(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    cgpa = calculate_cgpa(db, student.id)
    records = db.query(AcademicRecord).filter(AcademicRecord.student_id == student.id).all()
    return {
        "cgpa": cgpa,
        "records": [AcademicRecordOut.model_validate(r) for r in records],
    }


@router.post("/change-password", response_model=dict)
def change_student_password(
    data: PasswordChange,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, student.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    from app.core.security import get_password_hash

    student.hashed_password = get_password_hash(data.new_password)
    db.commit()
    log_action(db, student.matric_number, "PASSWORD_CHANGE", "students", student.id, "Password changed by student")
    return {"message": "Password changed successfully"}


@router.get("/alerts", response_model=List[AlertOut])
def get_my_alerts(
    student: Student = Depends(get_current_student),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    from app.crud.records import generate_missing_document_alerts

    generate_missing_document_alerts(db)
    alerts = paginate(
        db.query(Alert).filter(Alert.student_id == student.id).order_by(Alert.created_at.desc()),
        skip,
        limit,
    ).all()
    return [AlertOut.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/read", response_model=dict)
def mark_alert_read(
    alert_id: int, student: Student = Depends(get_current_student), db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.student_id == student.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}


@router.post("/payments", response_model=StudentPaymentOut)
def make_payment(
    data: StudentPaymentCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    payment = StudentPayment(
        student_id=student.id,
        amount=data.amount,
        payment_type=data.payment_type,
        reference=data.reference,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
