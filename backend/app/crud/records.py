"""Stateless database helper functions (CRUD operations and business logic)."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import AcademicRecord, Alert, AuditLog, Document, DocumentDeadline, Program, Student, StudentPayment, User
from app.schemas import StudentCreate


GRADE_POINTS = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}


def calculate_current_level(admission_year: int, duration_years: int, as_of: Optional[datetime] = None) -> int:
    """Derive the student's current level from admission year and program duration.

    A student admitted in 2022 is in 100L during 2022, 200L during 2023, etc.
    The result is capped at the program's maximum level (duration_years * 100).
    """
    if not admission_year or admission_year <= 0:
        return 100
    if not duration_years or duration_years <= 0:
        duration_years = 4
    as_of = as_of or datetime.utcnow()
    years = as_of.year - admission_year + 1
    level = max(1, years) * 100
    max_level = duration_years * 100
    return min(level, max_level)

REQUIRED_ONE_TIME_DOCUMENTS = [
    "jamb_result",
    "waec_result",
    "jamb_admission_letter",
    "birth_certificate",
    "passport_photo",
]


def paginate(query, skip: int = 0, limit: int = 50, max_limit: int = 500):
    skip = max(0, skip)
    limit = min(max(1, limit), max_limit)
    return query.offset(skip).limit(limit)


def normalize_matric(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def calculate_cgpa(db: Session, student_id: int) -> Optional[float]:
    records = db.query(AcademicRecord).filter(AcademicRecord.student_id == student_id).all()
    if not records:
        return None
    total_points = 0
    total_units = 0
    for rec in records:
        gp = GRADE_POINTS.get(rec.grade.upper(), 0)
        units = rec.course.credit_units if rec.course else 3
        total_points += gp * units
        total_units += units
    return round(total_points / total_units, 2) if total_units > 0 else 0.0


def log_action(db: Session, username: str, action: str, table_name: str, record_id, details: str = ""):
    log = AuditLog(
        username=username,
        action=action,
        table_name=table_name,
        record_id=str(record_id) if record_id is not None else None,
        details=details,
    )
    db.add(log)
    db.commit()


def create_student_internal(db: Session, data: StudentCreate, actor: str = "system") -> Student:
    matric = normalize_matric(data.matric_number)
    if not matric:
        raise ValueError("Matric number is required")
    if "/" not in matric:
        raise ValueError("Matric number must be in the format YEAR/NUMBER (e.g. 22/11220)")
    if db.query(Student).filter(Student.matric_number == matric).first():
        raise ValueError(f"Matric number {matric} already exists")

    program = db.query(Program).filter(Program.id == data.program_id).first()
    duration_years = program.duration_years if program else 4
    current_level = calculate_current_level(data.admission_year, duration_years)

    default_password = f"Caleb{str(data.admission_year)[-2:]}"
    student = Student(
        matric_number=matric,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        college_id=data.college_id,
        department_id=data.department_id,
        program_id=data.program_id,
        admission_year=data.admission_year,
        current_level=current_level,
        gender=data.gender,
        date_of_birth=data.date_of_birth,
        hashed_password=get_password_hash(default_password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    log_action(db, actor, "CREATE", "students", student.id, f"Registered student {matric}")
    student.default_password = default_password
    return student


def recalculate_student_levels(db: Session) -> int:
    """Recompute current_level for all active students based on admission_year and program duration."""
    updated = 0
    students = db.query(Student).filter(Student.status == "active").all()
    for student in students:
        if not student.admission_year:
            continue
        duration_years = student.program.duration_years if student.program else 4
        new_level = calculate_current_level(student.admission_year, duration_years)
        if student.current_level != new_level:
            student.current_level = new_level
            updated += 1
    if updated > 0:
        db.commit()
    return updated


def check_deadline_and_fee(db: Session, student_id: int, document_type: str, level: Optional[int]) -> Optional[float]:
    """Returns late fee amount if deadline has passed and fee is unpaid, else None."""
    deadline = db.query(DocumentDeadline).filter(
        DocumentDeadline.document_type == document_type,
        DocumentDeadline.level == level,
        DocumentDeadline.is_active == True,
    ).first()

    if not deadline:
        return None

    if datetime.utcnow() <= deadline.deadline_date:
        return None  # Deadline not passed

    # Check if student already paid this fee
    paid = db.query(StudentPayment).filter(
        StudentPayment.student_id == student_id,
        StudentPayment.payment_type == f"late_fee_{document_type}_{level or 'none'}",
    ).first()

    if paid:
        return None  # Already paid

    return deadline.late_fee_amount


def generate_missing_document_alerts(db: Session) -> int:
    """Auto-generate alerts for students with missing documents."""
    active_students = db.query(Student).filter(Student.status == "active").all()
    created = 0

    for student in active_students:
        docs = db.query(Document).filter(Document.student_id == student.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []

        for dt in REQUIRED_ONE_TIME_DOCUMENTS:
            if (dt, None) not in doc_types:
                missing.append(dt.replace("_", " ").title())

        if ("clearance_cert", student.current_level) not in doc_types:
            missing.append(f"{student.current_level}L Clearance Certificate")

        if missing:
            existing = db.query(Alert).filter(
                Alert.student_id == student.id,
                Alert.alert_type == "missing_document",
                Alert.is_read == False,
            ).first()

            if not existing:
                msg = (
                    f"You are missing the following required documents: {', '.join(missing)}. "
                    "Please upload them as soon as possible to avoid late fees."
                )
                alert = Alert(
                    student_id=student.id,
                    message=msg,
                    alert_type="missing_document",
                )
                db.add(alert)
                created += 1

    if created > 0:
        db.commit()
    return created


def ensure_upload_dir():
    """Ensure the configured upload directory exists."""
    settings.upload_dir_resolved.mkdir(parents=True, exist_ok=True)
