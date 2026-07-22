"""Dashboard statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    apply_college_scope,
    apply_staff_scope,
    get_current_staff,
    is_college_user,
    is_global_user,
)
from app.models import College, Department, Document, Program, Student, User
from app.schemas import StatsOut

router = APIRouter(prefix="/api", tags=["Stats"])

REQUIRED_ONE_TIME_DOCUMENTS = [
    "jamb_result",
    "waec_result",
    "jamb_admission_letter",
    "birth_certificate",
    "passport_photo",
]


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db), user: User = Depends(get_current_staff)):
    student_query = apply_staff_scope(db.query(Student), user)
    document_query = db.query(Document)
    if not is_global_user(user):
        document_query = document_query.join(Student).filter(Student.college_id == user.college_id)
        if not is_college_user(user):
            # Department-scoped staff only see their department's documents
            document_query = document_query.filter(Student.department_id == user.department_id)

    total_students = student_query.count()
    total_documents = document_query.count()
    total_colleges = db.query(College).count() if is_global_user(user) else 1
    total_departments = (
        db.query(Department).count()
        if is_global_user(user)
        else db.query(Department).filter(Department.college_id == user.college_id).count()
    )
    total_programs = (
        db.query(Program).count()
        if is_global_user(user)
        else db.query(Program).join(Department).filter(Department.college_id == user.college_id).count()
    )

    active_students = apply_staff_scope(db.query(Student).filter(Student.status == "active"), user).all()
    total_missing = 0
    for s in active_students:
        docs = db.query(Document).filter(Document.student_id == s.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []
        for dt in REQUIRED_ONE_TIME_DOCUMENTS:
            if (dt, None) not in doc_types:
                missing.append(dt)
        if ("clearance_cert", s.current_level) not in doc_types:
            missing.append(f"clearance_cert_{s.current_level}L")
        if missing:
            total_missing += 1

    students_by_level = {}
    for lvl in [100, 200, 300, 400, 500]:
        students_by_level[str(lvl)] = apply_staff_scope(
            db.query(Student).filter(Student.current_level == lvl), user
        ).count()

    return StatsOut(
        total_students=total_students,
        total_documents=total_documents,
        total_missing=total_missing,
        total_colleges=total_colleges,
        total_departments=total_departments,
        total_programs=total_programs,
        students_by_level=students_by_level,
    )
