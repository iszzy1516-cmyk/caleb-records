"""Document deadline management endpoints."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_or_student, require_roles
from app.crud.records import log_action, paginate
from app.models import DocumentDeadline, User
from app.schemas import DocumentDeadlineCreate, DocumentDeadlineOut

router = APIRouter(prefix="/api/document-deadlines", tags=["Document Deadlines"])


@router.post("", response_model=DocumentDeadlineOut)
def create_deadline(
    data: DocumentDeadlineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "records_officer")),
):
    try:
        deadline_dt = datetime.strptime(data.deadline_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deadline date format. Use YYYY-MM-DD")

    dd = DocumentDeadline(
        document_type=data.document_type,
        level=data.level,
        deadline_date=deadline_dt,
        late_fee_amount=data.late_fee_amount,
        created_by=user.username,
    )
    db.add(dd)
    db.commit()
    db.refresh(dd)
    log_action(db, user.username, "CREATE", "document_deadlines", dd.id, f"Set deadline for {data.document_type}")
    return dd


@router.get("", response_model=List[DocumentDeadlineOut])
def list_deadlines(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    actor: dict = Depends(get_current_user_or_student),
):
    return [
        DocumentDeadlineOut.model_validate(d)
        for d in paginate(db.query(DocumentDeadline).filter(DocumentDeadline.is_active == True), skip, limit).all()
    ]


@router.delete("/{deadline_id}", response_model=dict)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "records_officer")),
):
    dd = db.query(DocumentDeadline).filter(DocumentDeadline.id == deadline_id).first()
    if not dd:
        raise HTTPException(status_code=404, detail="Deadline not found")
    dd.is_active = False
    db.commit()
    log_action(db, user.username, "DELETE", "document_deadlines", dd.id, "Deactivated deadline")
    return {"message": "Deadline deactivated"}
