"""SQLAlchemy models for the student records management system."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    college = relationship("College")
    created_at = Column(DateTime, default=datetime.utcnow)


class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    duration_years = Column(Integer, default=4)
    department = relationship("Department")
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    matric_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    admission_year = Column(Integer, nullable=False, index=True)
    current_level = Column(Integer, default=100, index=True)
    gender = Column(String, default="male")
    date_of_birth = Column(String, nullable=True)
    status = Column(String, default="active", index=True)
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    college = relationship("College")
    department = relationship("Department")
    program = relationship("Program")
    documents = relationship("Document", cascade="all, delete-orphan")
    academic_records = relationship("AcademicRecord", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False, index=True)
    level = Column(Integer, nullable=True, index=True)
    session = Column(String, nullable=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    storage_provider = Column(String, default="local", nullable=False)
    storage_key = Column(String, nullable=True)
    public_url = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    verification_confidence = Column(Float, nullable=True)
    verification_detected_type = Column(String, nullable=True)
    verification_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    credit_units = Column(Integer, default=3)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    level = Column(Integer, default=100)
    semester = Column(String, default="First")
    created_at = Column(DateTime, default=datetime.utcnow)
    department = relationship("Department")


class AcademicRecord(Base):
    __tablename__ = "academic_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    grade = Column(String, nullable=False, index=True)
    session = Column(String, nullable=False, index=True)
    semester = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    course = relationship("Course")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="records_officer")
    is_active = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    college = relationship("College", foreign_keys=[college_id])
    department_rel = relationship("Department", foreign_keys=[department_id])


class StaffRegistration(Base):
    __tablename__ = "staff_registrations"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="records_officer")
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    college = relationship("College", foreign_keys=[college_id])
    department_rel = relationship("Department", foreign_keys=[department_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    table_name = Column(String, nullable=False, index=True)
    record_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    message = Column(String, nullable=False)
    alert_type = Column(String, default="missing_document", index=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DocumentDeadline(Base):
    __tablename__ = "document_deadlines"
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String, nullable=False, index=True)
    level = Column(Integer, nullable=True, index=True)
    deadline_date = Column(DateTime, nullable=False, index=True)
    late_fee_amount = Column(Float, default=0.0)
    created_by = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class StudentPayment(Base):
    __tablename__ = "student_payments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_type = Column(String, nullable=False, index=True)
    reference = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
