"""Student management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import (
    apply_staff_scope,
    ensure_college_access,
    ensure_department_access,
    get_current_staff,
    get_current_user,
    require_roles,
)
from app.crud.records import calculate_cgpa, create_student_internal, log_action, paginate
from app.models import AcademicRecord, Department, Document, Student, User
from app.schemas import BulkStudentCreate, BulkStudentResult, StudentCreate, StudentDetailOut, StudentOut
from app.schemas.records import AcademicRecordOut, CollegeOut, DepartmentOut, DocumentOut, ProgramOut

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.post("", response_model=StudentOut)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin", "hod", "dean")),
):
    try:
        ensure_college_access(user, data.college_id)
        ensure_department_access(user, data.department_id)
        return create_student_internal(db, data, actor=user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register", response_model=StudentOut)
@limiter.limit("3/minute")
def student_self_register(request: Request, data: StudentCreate, db: Session = Depends(get_db)):
    try:
        return create_student_internal(db, data, actor="self-registration")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk", response_model=BulkStudentResult)
@limiter.limit("10/minute")
def bulk_create_students(
    request: Request,
    data: BulkStudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin", "hod", "dean")),
):
    created = 0
    failed = 0
    matric_numbers = []
    errors = []
    for student_data in data.students:
        try:
            ensure_college_access(user, student_data.college_id)
            ensure_department_access(user, student_data.department_id)
            student = create_student_internal(db, student_data, actor=user.username)
            created += 1
            matric_numbers.append(student.matric_number)
        except Exception as e:
            failed += 1
            errors.append(f"{student_data.first_name} {student_data.last_name}: {str(e)}")
    log_action(db, user.username, "BULK_CREATE", "students", None, f"Bulk registered {created} students, {failed} failed")
    return BulkStudentResult(created=created, failed=failed, matric_numbers=matric_numbers, errors=errors)


@router.get("/search", response_model=List[StudentOut])
def search_students(
    q: Optional[str] = Query(None, min_length=1),
    college_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    session: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff),
):
    query = db.query(Student)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (Student.matric_number.ilike(search))
            | (Student.first_name.ilike(search))
            | (Student.last_name.ilike(search))
            | (Student.email.ilike(search))
            | (Student.department.has(Department.name.ilike(search)))
        )

    if college_id is not None:
        ensure_college_access(user, college_id)
        query = query.filter(Student.college_id == college_id)
    if department_id is not None:
        ensure_department_access(user, department_id)
        query = query.filter(Student.department_id == department_id)

    if session:
        # Filter students who have a document or academic record for the given session
        student_ids_with_session = (
            db.query(Document.student_id).filter(Document.session == session)
        ).union(
            db.query(AcademicRecord.student_id).filter(AcademicRecord.session == session)
        ).subquery()
        query = query.filter(Student.id.in_(student_ids_with_session))

    query = apply_staff_scope(query, user)
    return paginate(query, skip, limit).all()


@router.get("/{student_id}", response_model=StudentDetailOut)
def get_student(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_staff)):
    query = (
        db.query(Student)
        .options(
            joinedload(Student.college),
            joinedload(Student.department),
            joinedload(Student.program),
            joinedload(Student.documents),
            joinedload(Student.academic_records).joinedload(AcademicRecord.course),
        )
        .filter(Student.id == student_id)
    )
    query = apply_staff_scope(query, user)
    student = query.first()
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


@router.get("/{student_id}/cgpa")
def get_cgpa(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_staff)):
    query = apply_staff_scope(db.query(Student).filter(Student.id == student_id), user)
    student = query.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    cgpa = calculate_cgpa(db, student.id)
    return {"student_id": student_id, "cgpa": cgpa}
