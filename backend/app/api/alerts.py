"""Alert endpoints for staff and students."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    apply_staff_scope,
    get_current_user,
    is_college_user,
    is_global_user,
    require_roles,
)
from app.crud.records import paginate
from app.models import Alert, Student, User
from app.schemas import AlertOut

router = APIRouter(prefix="/api", tags=["Alerts"])


@router.get("/alerts", response_model=List[AlertOut])
def list_all_alerts(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "records_officer", "hod", "dean")),
):
    query = db.query(Alert).order_by(Alert.created_at.desc())
    if not is_global_user(user):
        query = query.join(Student).filter(Student.college_id == user.college_id)
        if not is_college_user(user):
            query = query.filter(Student.department_id == user.department_id)
    alerts = paginate(query, skip, limit).all()
    return [AlertOut.model_validate(a) for a in alerts]
