"""Public lookup endpoints (no authentication required)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.crud.records import calculate_cgpa
from app.models import AcademicRecord, Student
from app.schemas import StudentDetailOut
from app.schemas.records import AcademicRecordOut, CollegeOut, DepartmentOut, DocumentOut, ProgramOut

router = APIRouter(prefix="/api/public", tags=["Public"])


@router.get("/students/{matric_number:path}", response_model=StudentDetailOut)
def public_student_lookup(matric_number: str, db: Session = Depends(get_db)):
    student = (
        db.query(Student)
        .options(
            joinedload(Student.college),
            joinedload(Student.department),
            joinedload(Student.program),
            joinedload(Student.documents),
            joinedload(Student.academic_records).joinedload(AcademicRecord.course),
        )
        .filter(Student.matric_number == matric_number.upper())
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

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
