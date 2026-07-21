"""Document upload and download endpoints for staff."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    apply_staff_scope,
    ensure_college_access,
    ensure_department_access,
    get_current_user_or_student,
    require_roles,
)
from app.crud.records import check_deadline_and_fee
from app.models import Document, Student, StudentPayment, User
from app.schemas import DocumentOut
from app.services.documents import save_upload_file, verify_and_create_document

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=DocumentOut)
def upload_document(
    student_id: int = Form(...),
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    session: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin", "hod", "dean")),
):
    student_query = apply_staff_scope(db.query(Student).filter(Student.id == student_id), user)
    student = student_query.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check deadline
    late_fee = check_deadline_and_fee(db, student_id, document_type, level)
    if late_fee and late_fee > 0:
        paid = db.query(StudentPayment).filter(
            StudentPayment.student_id == student_id,
            StudentPayment.payment_type == f"late_fee_{document_type}_{level or 'none'}",
        ).first()
        if not paid:
            raise HTTPException(
                status_code=400,
                detail=f"Document upload deadline has passed. A late fee of ₦{late_fee:,.2f} must be paid before uploading.",
            )

    file_path = save_upload_file(file, student, document_type, level, session)
    return verify_and_create_document(db, student, document_type, level, session, file, file_path, user.username)


@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    actor: dict = Depends(get_current_user_or_student),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if actor["type"] == "student":
        if doc.student_id != actor["actor"].id:
            raise HTTPException(status_code=403, detail="You can only download your own documents")
    else:
        user = actor["actor"]
        student = db.query(Student).filter(Student.id == doc.student_id).first()
        if student:
            ensure_college_access(user, student.college_id)
            ensure_department_access(user, student.department_id)

    if not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )
