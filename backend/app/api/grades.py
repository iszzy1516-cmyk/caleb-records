"""Grade/academic record endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import apply_staff_scope, require_roles
from app.crud.records import log_action
from app.models import AcademicRecord, Course, Student, User
from app.schemas import AcademicRecordOut, GradeCreate

router = APIRouter(prefix="/api/grades", tags=["Grades"])


@router.post("", response_model=AcademicRecordOut)
def create_grade(
    data: GradeCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("lecturer", "admin", "hod", "dean"))
):
    student_query = apply_staff_scope(db.query(Student).filter(Student.id == data.student_id), user)
    student = student_query.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    rec = AcademicRecord(
        student_id=data.student_id,
        course_id=data.course_id,
        grade=data.grade.upper(),
        session=data.session,
        semester=data.semester,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    log_action(db, user.username, "CREATE", "academic_records", rec.id, f"Grade {data.grade} for {student.matric_number} in {course.code}")
    return rec
