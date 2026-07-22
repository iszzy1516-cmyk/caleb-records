"""Reports and audit log endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import apply_staff_scope, require_roles
from app.crud.records import paginate
from app.models import AuditLog, Document, Student, User
from app.schemas import AuditLogOut, MissingDocReport

router = APIRouter(tags=["Reports"])

REQUIRED_ONE_TIME_DOCUMENTS = [
    "jamb_result",
    "waec_result",
    "jamb_admission_letter",
    "birth_certificate",
    "passport_photo",
]


@router.get("/api/reports/missing-documents", response_model=List[MissingDocReport])
def missing_documents_report(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin", "hod", "dean")),
):
    query = apply_staff_scope(db.query(Student).filter(Student.status == "active"), user)
    students = paginate(query, skip, limit).all()
    report = []

    for student in students:
        docs = db.query(Document).filter(Document.student_id == student.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []

        for dt in REQUIRED_ONE_TIME_DOCUMENTS:
            if (dt, None) not in doc_types:
                missing.append(dt)

        if ("clearance_cert", student.current_level) not in doc_types:
            missing.append(f"clearance_cert_{student.current_level}L")
        if ("course_form", student.current_level) not in doc_types:
            missing.append(f"course_form_{student.current_level}L")

        if missing:
            report.append(
                MissingDocReport(
                    student_id=student.id,
                    matric_number=student.matric_number,
                    name=f"{student.first_name} {student.last_name}",
                    current_level=student.current_level,
                    missing_docs=missing,
                )
            )

    return report


@router.get("/api/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return paginate(db.query(AuditLog).order_by(AuditLog.created_at.desc()), skip, limit).all()
