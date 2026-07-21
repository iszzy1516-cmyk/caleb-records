"""Reference data endpoints (colleges, departments, programs, courses)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_staff
from app.crud.records import paginate
from app.models import College, Course, Department, Program, User
from app.schemas import CollegeOut, CourseOut, DepartmentOut, ProgramOut

router = APIRouter(prefix="/api", tags=["Reference Data"])


@router.get("/colleges", response_model=List[CollegeOut])
def list_colleges(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return paginate(db.query(College), skip, limit).all()


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    college_id: int = Query(...), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    return paginate(db.query(Department).filter(Department.college_id == college_id), skip, limit).all()


@router.get("/programs", response_model=List[ProgramOut])
def list_programs(
    department_id: int = Query(...), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    return paginate(db.query(Program).filter(Program.department_id == department_id), skip, limit).all()


@router.get("/courses", response_model=List[CourseOut])
def list_courses(
    level: Optional[int] = None,
    dept_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_staff),
):
    q = db.query(Course)
    if level:
        q = q.filter(Course.level == level)
    if dept_id:
        q = q.filter(Course.department_id == dept_id)
    return paginate(q, skip, limit).all()
