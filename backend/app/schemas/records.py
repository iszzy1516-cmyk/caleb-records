"""Pydantic request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    email: str
    full_name: Optional[str] = None
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    force_password_change: bool = False


class StudentToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    matric_number: str
    full_name: str


class CollegeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    college_id: int


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    department_id: int
    duration_years: int


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    credit_units: int
    department_id: int
    level: int
    semester: str


class StudentCreate(BaseModel):
    matric_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    college_id: int
    department_id: int
    program_id: int
    admission_year: int = Field(default_factory=lambda: datetime.utcnow().year)
    current_level: int = 100
    gender: str = "male"
    date_of_birth: Optional[str] = None


class BulkStudentCreate(BaseModel):
    students: List[StudentCreate]


class BulkStudentResult(BaseModel):
    created: int
    failed: int
    matric_numbers: List[str]
    errors: List[str]


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    matric_number: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    college_id: int
    department_id: int
    program_id: int
    admission_year: int
    current_level: int
    gender: str
    date_of_birth: Optional[str]
    status: str
    created_at: datetime
    college: Optional[CollegeOut] = None
    department: Optional[DepartmentOut] = None
    program: Optional[ProgramOut] = None
    default_password: Optional[str] = None


class StudentDetailOut(StudentOut):
    documents: List["DocumentOut"] = []
    academic_records: List["AcademicRecordOut"] = []
    cgpa: Optional[float] = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    document_type: str
    level: Optional[int]
    session: Optional[str]
    original_filename: str
    mime_type: Optional[str]
    file_size: Optional[int]
    verified: bool = False
    verification_confidence: Optional[float] = None
    verification_detected_type: Optional[str] = None
    verification_notes: Optional[str] = None
    created_at: datetime


class GradeCreate(BaseModel):
    student_id: int
    course_id: int
    grade: str = Field(pattern=r"^[ABCDEF]$")
    session: str
    semester: str = "First"


class AcademicRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_id: int
    grade: str
    session: str
    semester: str
    course: Optional[CourseOut] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    action: str
    table_name: str
    record_id: Optional[str]
    details: Optional[str]
    created_at: datetime


class MissingDocReport(BaseModel):
    student_id: int
    matric_number: str
    name: str
    current_level: int
    missing_docs: List[str]


class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    college_id: Optional[int] = None
    department_id: Optional[int] = None
    password: str
    role: str = "records_officer"


class BulkUserItem(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    college_id: Optional[int] = None
    department_id: Optional[int] = None
    password: Optional[str] = None
    role: str


class BulkUserCreate(BaseModel):
    users: List[BulkUserItem]


class StaffRegisterRequest(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    college_id: Optional[int] = None
    department_id: Optional[int] = None
    password: str = Field(min_length=6)


class StaffRegisterVerify(BaseModel):
    email: str
    otp: str


class PasswordResetRequest(BaseModel):
    matric_number: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=4)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=4)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    message: str
    alert_type: str
    is_read: bool
    created_at: datetime


class DocumentDeadlineCreate(BaseModel):
    document_type: str
    level: Optional[int] = None
    deadline_date: str
    late_fee_amount: float = 0.0


class DocumentDeadlineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_type: str
    level: Optional[int]
    deadline_date: datetime
    late_fee_amount: float
    created_by: str
    is_active: bool
    created_at: datetime


class StudentPaymentCreate(BaseModel):
    amount: float
    payment_type: str
    reference: Optional[str] = None


class StudentPaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    amount: float
    payment_type: str
    reference: Optional[str]
    created_at: datetime


class StatsOut(BaseModel):
    total_students: int
    total_documents: int
    total_missing: int
    total_colleges: int
    total_departments: int
    total_programs: int
    students_by_level: dict


# Forward refs
StudentDetailOut.model_rebuild()
