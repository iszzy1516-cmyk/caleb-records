"""
Caleb University Student Records Management System - FastAPI Backend
"""

import os
import uuid
import shutil
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter at module level for decorators
limiter = Limiter(key_func=get_remote_address)
from sqlalchemy import create_engine, event, func, select, Index
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship, joinedload
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, Enum as SQLEnum
from pydantic import BaseModel, Field, ConfigDict
import bcrypt
from jose import JWTError, jwt

# ─── Configuration ───────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "cu-records-secret-CHANGE-IN-PROD")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./caleb_records.db")
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:8000,https://tauri.localhost,http://141.147.48.186,https://141.147.48.186").split(",")

# SMTP Configuration for password reset emails
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@calebuniversity.edu.ng")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ─── Database ────────────────────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# ─── Models ──────────────────────────────────────────────────────────────────

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
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
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
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="records_officer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffRegistration(Base):
    __tablename__ = "staff_registrations"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="records_officer")
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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

# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    email: str
    full_name: Optional[str] = None

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
    original_filename: str
    mime_type: Optional[str]
    file_size: Optional[int]
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
    password: str
    role: str = "records_officer"

class StaffRegisterRequest(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
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

# ─── Auth Utilities ──────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Student:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        matric: str = payload.get("sub")
        token_type: str = payload.get("type")
        if matric is None or token_type != "student":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    student = db.query(Student).filter(Student.matric_number == matric).first()
    if student is None or student.status != "active":
        raise credentials_exception
    return student

def get_current_user_or_student(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        token_type: str = payload.get("type")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if token_type == "student":
        student = db.query(Student).filter(Student.matric_number == sub).first()
        if student is None or student.status != "active":
            raise credentials_exception
        return {"type": "student", "actor": student}

    user = db.query(User).filter(User.email == sub).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return {"type": "staff", "actor": user}

def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles and user.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker

# ─── Email Utilities ─────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, body: str) -> bool:
    if not SMTP_HOST or not SMTP_USER:
        # Dev fallback: print to console
        print(f"\n{'='*60}")
        print(f"EMAIL TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"{'-'*60}")
        print(body)
        print(f"{'='*60}\n")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def generate_otp(length: int = 6) -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(length))

# ─── Audit Logging ───────────────────────────────────────────────────────────

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

# ─── Matric Number Generator ─────────────────────────────────────────────────

def normalize_matric(value: str) -> str:
    return value.strip().upper().replace(" ", "")

# ─── CGPA Calculator ─────────────────────────────────────────────────────────

GRADE_POINTS = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}

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

# ─── App Factory ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_reference_data(db)
        _seed_default_user(db)
    finally:
        db.close()
    yield
    # Shutdown (nothing to clean up)

def create_app() -> FastAPI:
    app = FastAPI(
        title="CU-Records API",
        description="Student Records Management System for Caleb University",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=500)

    # Security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Handle CORS preflight robustly for mobile webviews that send OPTIONS
    # without standard Access-Control-Request-Method headers.
    class OptionsCorsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.method == "OPTIONS":
                origin = request.headers.get("origin", "")
                response = Response(status_code=200)
                allowed_origin = origin if origin in CORS_ORIGINS else (CORS_ORIGINS[0] if CORS_ORIGINS else "*")
                response.headers["Access-Control-Allow-Origin"] = allowed_origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"
                return response
            return await call_next(request)

    app.add_middleware(OptionsCorsMiddleware)

    return app

# ─── Seed Data ───────────────────────────────────────────────────────────────

def _seed_reference_data(db: Session):
    if db.query(College).first():
        return

    colleges_data = [
        ("College of Education", "COLED"),
        ("College of Environmental Sciences and Management", "COLENSMA"),
        ("College of Pure and Applied Sciences", "COPAS"),
        ("College of Arts, Social and Management Sciences", "CASMAS"),
        ("College of Nursing, Basic and Medical Sciences", "CONBAMS"),
        ("College of Business Management and Social Sciences", "COBMAHS"),
        ("College of Computing and Information Sciences", "COCMS"),
        ("College of Law", "COLAW"),
    ]

    for name, code in colleges_data:
        db.add(College(name=name, code=code))
    db.commit()

    # Seed some departments (minimal set)
    cs_dept = Department(name="Computer Science", college_id=7)
    cyber_dept = Department(name="Cyber Security", college_id=7)
    se_dept = Department(name="Software Engineering", college_id=7)
    accounting = Department(name="Accounting", college_id=5)
    bizadmin = Department(name="Business Administration", college_id=5)
    economics = Department(name="Economics", college_id=4)
    masscom = Department(name="Mass Communication", college_id=4)
    law = Department(name="Law", college_id=8)
    nursing = Department(name="Nursing", college_id=6)
    architecture = Department(name="Architecture", college_id=2)
    education = Department(name="Early Childhood Education", college_id=1)

    for d in [cs_dept, cyber_dept, se_dept, accounting, bizadmin, economics, masscom, law, nursing, architecture, education]:
        db.add(d)
    db.commit()

    # Seed programs
    db.add(Program(name="B.Sc. Computer Science", department_id=cs_dept.id, duration_years=4))
    db.add(Program(name="B.Sc. Cyber Security", department_id=cyber_dept.id, duration_years=4))
    db.add(Program(name="B.Sc. Software Engineering", department_id=se_dept.id, duration_years=4))
    db.add(Program(name="B.Sc. Accounting", department_id=accounting.id, duration_years=4))
    db.add(Program(name="B.Sc. Business Administration", department_id=bizadmin.id, duration_years=4))
    db.add(Program(name="B.Sc. Economics", department_id=economics.id, duration_years=4))
    db.add(Program(name="B.Sc. Mass Communication", department_id=masscom.id, duration_years=4))
    db.add(Program(name="LL.B. Law", department_id=law.id, duration_years=5))
    db.add(Program(name="B.NSc. Nursing", department_id=nursing.id, duration_years=5))
    db.add(Program(name="B.Sc. Architecture", department_id=architecture.id, duration_years=5))
    db.add(Program(name="B.Ed. Early Childhood Education", department_id=education.id, duration_years=4))
    db.commit()

def _seed_default_user(db: Session):
    if db.query(User).filter(User.email == "admin@calebuniversity.edu.ng").first():
        return
    admin = User(
        username="admin",
        full_name="System Administrator",
        email="admin@calebuniversity.edu.ng",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()

# ─── Create App Instance ─────────────────────────────────────────────────────

app = create_app()


# ─── Authentication Routes ───────────────────────────────────────────────────

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "type": "staff"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
    }

class StudentToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    matric_number: str
    full_name: str

@app.post("/token/student", response_model=StudentToken)
@limiter.limit("5/minute")
def student_login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.matric_number == form_data.username.upper()).first()
    if not student or not student.hashed_password:
        raise HTTPException(status_code=400, detail="Invalid matric number or password")
    if not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid matric number or password")
    if student.status != "active":
        raise HTTPException(status_code=400, detail="Student account is inactive")

    access_token = create_access_token(data={"sub": student.matric_number, "type": "student"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "matric_number": student.matric_number,
        "full_name": f"{student.first_name} {student.last_name}",
    }

# ─── Reference Data Routes ───────────────────────────────────────────────────

@app.get("/api/colleges", response_model=List[CollegeOut])
def list_colleges(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return paginate(db.query(College), skip, limit).all()

@app.get("/api/departments", response_model=List[DepartmentOut])
def list_departments(college_id: int = Query(...), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return paginate(db.query(Department).filter(Department.college_id == college_id), skip, limit).all()

@app.get("/api/programs", response_model=List[ProgramOut])
def list_programs(department_id: int = Query(...), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return paginate(db.query(Program).filter(Program.department_id == department_id), skip, limit).all()

@app.get("/api/courses", response_model=List[CourseOut])
def list_courses(level: Optional[int] = None, dept_id: Optional[int] = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Course)
    if level:
        q = q.filter(Course.level == level)
    if dept_id:
        q = q.filter(Course.department_id == dept_id)
    return paginate(q, skip, limit).all()

# ─── Student Routes ──────────────────────────────────────────────────────────

def _create_student_internal(db: Session, data: StudentCreate, actor: str = "system") -> Student:
    matric = normalize_matric(data.matric_number)
    if not matric:
        raise ValueError("Matric number is required")
    if "/" not in matric:
        raise ValueError("Matric number must be in the format YEAR/NUMBER (e.g. 22/11220)")
    if db.query(Student).filter(Student.matric_number == matric).first():
        raise ValueError(f"Matric number {matric} already exists")

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
        current_level=data.current_level,
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

@app.post("/api/students", response_model=StudentOut)
def create_student(data: StudentCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("records_officer", "admin", "hod"))):
    try:
        return _create_student_internal(db, data, actor=user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/students/register", response_model=StudentOut)
@limiter.limit("3/minute")
def student_self_register(request: Request, data: StudentCreate, db: Session = Depends(get_db)):
    try:
        return _create_student_internal(db, data, actor="self-registration")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/students/bulk", response_model=BulkStudentResult)
@limiter.limit("10/minute")
def bulk_create_students(request: Request, data: BulkStudentCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("records_officer", "admin", "hod"))):
    created = 0
    failed = 0
    matric_numbers = []
    errors = []
    for student_data in data.students:
        try:
            student = _create_student_internal(db, student_data, actor=user.username)
            created += 1
            matric_numbers.append(student.matric_number)
        except Exception as e:
            failed += 1
            errors.append(f"{student_data.first_name} {student_data.last_name}: {str(e)}")
    log_action(db, user.username, "BULK_CREATE", "students", None, f"Bulk registered {created} students, {failed} failed")
    return BulkStudentResult(created=created, failed=failed, matric_numbers=matric_numbers, errors=errors)

@app.get("/api/students/search", response_model=List[StudentOut])
def search_students(q: str = Query(..., min_length=1), skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    search = f"%{q}%"
    results = paginate(db.query(Student).filter(
        (Student.matric_number.ilike(search)) |
        (Student.first_name.ilike(search)) |
        (Student.last_name.ilike(search))
    ), skip, limit).all()
    return results

@app.get("/api/students/{student_id}", response_model=StudentDetailOut)
def get_student(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    student = db.query(Student).options(
        joinedload(Student.college),
        joinedload(Student.department),
        joinedload(Student.program),
        joinedload(Student.documents),
        joinedload(Student.academic_records).joinedload(AcademicRecord.course),
    ).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    cgpa = calculate_cgpa(db, student.id)

    # Build response manually to include relationships and cgpa
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

@app.get("/api/students/{student_id}/cgpa")
def get_cgpa(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    cgpa = calculate_cgpa(db, student.id)
    return {"student_id": student_id, "cgpa": cgpa}

# ─── Document Routes ─────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

@app.post("/api/documents", response_model=DocumentOut)
def upload_document(
    student_id: int = Form(...),
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin")),
):
    # Validate student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate clearance cert has level
    if document_type == "clearance_cert" and level not in (100, 200, 300, 400, 500):
        raise HTTPException(status_code=400, detail="Level is required for clearance certificates")

    # Read file content to check size
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit")

    # Generate safe filename
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    level_str = f"_{level}" if level else ""
    safe_name = f"{student.matric_number}_{document_type}{level_str}_{timestamp}{ext}"
    safe_name = safe_name.replace("/", "_")
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        student_id=student_id,
        document_type=document_type,
        level=level,
        original_filename=file.filename,
        stored_filename=safe_name,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=len(contents),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    log_action(db, user.username, "UPLOAD", "documents", doc.id, f"Uploaded {document_type} for {student.matric_number}")
    return doc

@app.get("/api/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )

# ─── Grade Routes ────────────────────────────────────────────────────────────

@app.post("/api/grades", response_model=AcademicRecordOut)
def create_grade(data: GradeCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("lecturer", "admin", "hod"))):
    student = db.query(Student).filter(Student.id == data.student_id).first()
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

# ─── Reports & Audit Routes ──────────────────────────────────────────────────

@app.get("/api/reports/missing-documents", response_model=List[MissingDocReport])
def missing_documents_report(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(require_roles("records_officer", "admin", "hod"))):
    students = paginate(db.query(Student).filter(Student.status == "active"), skip, limit).all()
    report = []

    required_one_time = ["jamb_result", "waec_result", "jamb_admission_letter", "birth_certificate", "passport_photo", "medical"]

    for student in students:
        docs = db.query(Document).filter(Document.student_id == student.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []

        for dt in required_one_time:
            if (dt, None) not in doc_types:
                missing.append(dt)

        # Check clearance for current level
        if ("clearance_cert", student.current_level) not in doc_types:
            missing.append(f"clearance_cert_{student.current_level}L")

        if missing:
            report.append(MissingDocReport(
                student_id=student.id,
                matric_number=student.matric_number,
                name=f"{student.first_name} {student.last_name}",
                current_level=student.current_level,
                missing_docs=missing,
            ))

    return report

@app.get("/api/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(skip: int = 0, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return paginate(db.query(AuditLog).order_by(AuditLog.created_at.desc()), skip, limit).all()

# ─── Public Routes ───────────────────────────────────────────────────────────

@app.get("/api/public/students/{matric_number:path}", response_model=StudentDetailOut)
def public_student_lookup(matric_number: str, db: Session = Depends(get_db)):
    student = db.query(Student).options(
        joinedload(Student.college),
        joinedload(Student.department),
        joinedload(Student.program),
        joinedload(Student.documents),
        joinedload(Student.academic_records).joinedload(AcademicRecord.course),
    ).filter(Student.matric_number == matric_number.upper()).first()
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

# ─── Student Self-Service Routes ─────────────────────────────────────────────

@app.get("/api/me", response_model=StudentDetailOut)
def get_me(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    student = db.query(Student).options(
        joinedload(Student.college),
        joinedload(Student.department),
        joinedload(Student.program),
        joinedload(Student.documents),
        joinedload(Student.academic_records).joinedload(AcademicRecord.course),
    ).filter(Student.id == student.id).first()
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

@app.post("/api/me/documents", response_model=DocumentOut)
def upload_my_document(
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    if document_type == "clearance_cert" and level not in (100, 200, 300, 400, 500):
        raise HTTPException(status_code=400, detail="Level is required for clearance certificates")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    level_str = f"_{level}" if level else ""
    safe_name = f"{student.matric_number}_{document_type}{level_str}_{timestamp}{ext}"
    safe_name = safe_name.replace("/", "_")
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        student_id=student.id,
        document_type=document_type,
        level=level,
        original_filename=file.filename,
        stored_filename=safe_name,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=len(contents),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_action(db, student.matric_number, "UPLOAD", "documents", doc.id, f"Student uploaded {document_type}")
    return doc

@app.get("/api/me/grades")
def get_my_grades(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    cgpa = calculate_cgpa(db, student.id)
    records = db.query(AcademicRecord).filter(AcademicRecord.student_id == student.id).all()
    return {
        "cgpa": cgpa,
        "records": [AcademicRecordOut.model_validate(r) for r in records],
    }

# ─── User Management (Admin Only) ────────────────────────────────────────────

@app.post("/api/users", response_model=dict)
def create_user(data: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_email = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        username=data.username,
        full_name=data.full_name,
        email=data.email.lower().strip(),
        phone=data.phone,
        department=data.department,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    log_action(db, user.username, "CREATE", "users", new_user.id, f"Created user {data.username} ({data.email}) with role {data.role}")
    return {"message": "User created successfully", "username": data.username, "email": new_user.email, "role": new_user.role}

@app.post("/api/staff/register-request", response_model=dict)
@limiter.limit("10/minute")
def staff_register_request(request: Request, data: StaffRegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A staff account with this email already exists")
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Remove any pending registration for this email
    db.query(StaffRegistration).filter(StaffRegistration.email == email).delete()

    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=15)
    registration = StaffRegistration(
        username=data.username,
        full_name=data.full_name,
        email=email,
        phone=data.phone,
        department=data.department,
        hashed_password=get_password_hash(data.password),
        role="records_officer",
        otp=otp,
        expires_at=expires,
    )
    db.add(registration)
    db.commit()

    body = f"""Hello {data.full_name or data.username},

You are registering for a CU-Records staff account.

Your one-time verification code is: {otp}

This code expires in 15 minutes.

If you did not request this, please ignore this email.

Caleb University Records Team
For God and Humanity
"""
    send_email(email, "CU-Records Staff Registration OTP", body)
    return {"message": "Verification code sent to your email"}

@app.post("/api/staff/register-verify", response_model=dict)
def staff_register_verify(data: StaffRegisterVerify, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    registration = db.query(StaffRegistration).filter(
        StaffRegistration.email == email,
        StaffRegistration.otp == data.otp.strip(),
        StaffRegistration.verified == False,
        StaffRegistration.expires_at > datetime.utcnow(),
    ).first()

    if not registration:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A staff account with this email already exists")

    new_user = User(
        username=registration.username,
        full_name=registration.full_name,
        email=registration.email,
        phone=registration.phone,
        department=registration.department,
        hashed_password=registration.hashed_password,
        role="records_officer",
        is_active=True,
    )
    db.add(new_user)
    registration.verified = True
    db.commit()
    log_action(db, "system", "CREATE", "users", new_user.id, f"Self-registered staff user {new_user.username} ({new_user.email}) with role records_officer via OTP verification")
    return {"message": "Staff account created successfully", "username": new_user.username, "email": new_user.email}

# ─── Password Reset ──────────────────────────────────────────────────────────

@app.post("/api/password-reset-request", response_model=dict)
@limiter.limit("3/minute")
def request_password_reset(request: Request, data: PasswordResetRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.matric_number == data.matric_number.upper()).first()
    if not student or not student.email:
        # Don't reveal if student exists
        return {"message": "If your matric number is registered with an email, you will receive a reset link."}

    token = generate_reset_token()
    expires = datetime.utcnow() + timedelta(hours=1)

    reset = PasswordReset(
        student_id=student.id,
        token=token,
        expires_at=expires,
    )
    db.add(reset)
    db.commit()

    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    body = f"""Hello {student.first_name},

You requested a password reset for your CU-Records account.

Matric Number: {student.matric_number}
Reset Link: {reset_url}

This link expires in 1 hour.

If you did not request this, please ignore this email.

Caleb University Records Team
For God and Humanity
"""

    sent = send_email(student.email, "CU-Records Password Reset", body)
    if sent:
        log_action(db, student.matric_number, "PASSWORD_RESET_REQUEST", "password_resets", reset.id, "Reset requested")

    return {"message": "If your matric number is registered with an email, you will receive a reset link."}

@app.post("/api/password-reset", response_model=dict)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset = db.query(PasswordReset).filter(
        PasswordReset.token == data.token,
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.utcnow(),
    ).first()

    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    student = db.query(Student).filter(Student.id == reset.student_id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")

    student.hashed_password = get_password_hash(data.new_password)
    reset.used = True
    db.commit()

    log_action(db, student.matric_number, "PASSWORD_RESET", "students", student.id, "Password reset successfully")
    return {"message": "Password reset successfully. You can now log in with your new password."}

@app.post("/api/me/change-password", response_model=dict)
def change_student_password(
    data: PasswordChange,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, student.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    student.hashed_password = get_password_hash(data.new_password)
    db.commit()
    log_action(db, student.matric_number, "PASSWORD_CHANGE", "students", student.id, "Password changed by student")
    return {"message": "Password changed successfully"}

# ─── Stats ───────────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_students = db.query(Student).count()
    total_documents = db.query(Document).count()
    total_colleges = db.query(College).count()
    total_departments = db.query(Department).count()
    total_programs = db.query(Program).count()

    # Count students with missing docs
    active_students = db.query(Student).filter(Student.status == "active").all()
    total_missing = 0
    required_one_time = ["jamb_result", "waec_result", "jamb_admission_letter", "birth_certificate", "passport_photo", "medical"]
    for s in active_students:
        docs = db.query(Document).filter(Document.student_id == s.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []
        for dt in required_one_time:
            if (dt, None) not in doc_types:
                missing.append(dt)
        if ("clearance_cert", s.current_level) not in doc_types:
            missing.append(f"clearance_cert_{s.current_level}L")
        if missing:
            total_missing += 1

    students_by_level = {}
    for lvl in [100, 200, 300, 400, 500]:
        students_by_level[str(lvl)] = db.query(Student).filter(Student.current_level == lvl).count()

    return StatsOut(
        total_students=total_students,
        total_documents=total_documents,
        total_missing=total_missing,
        total_colleges=total_colleges,
        total_departments=total_departments,
        total_programs=total_programs,
        students_by_level=students_by_level,
    )

# ─── Alerts ──────────────────────────────────────────────────────────────────

def generate_missing_document_alerts(db: Session):
    """Auto-generate alerts for students with missing documents."""
    active_students = db.query(Student).filter(Student.status == "active").all()
    required_one_time = ["jamb_result", "waec_result", "jamb_admission_letter", "birth_certificate", "passport_photo", "medical"]
    created = 0

    for student in active_students:
        docs = db.query(Document).filter(Document.student_id == student.id).all()
        doc_types = {(d.document_type, d.level) for d in docs}
        missing = []

        for dt in required_one_time:
            if (dt, None) not in doc_types:
                missing.append(dt.replace("_", " ").title())

        if ("clearance_cert", student.current_level) not in doc_types:
            missing.append(f"{student.current_level}L Clearance Certificate")

        if missing:
            # Check if an unread alert already exists for this student
            existing = db.query(Alert).filter(
                Alert.student_id == student.id,
                Alert.alert_type == "missing_document",
                Alert.is_read == False,
            ).first()

            if not existing:
                msg = f"You are missing the following required documents: {', '.join(missing)}. Please upload them as soon as possible to avoid late fees."
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

@app.get("/api/me/alerts", response_model=List[AlertOut])
def get_my_alerts(student: Student = Depends(get_current_student), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # Auto-generate alerts first
    generate_missing_document_alerts(db)
    alerts = paginate(
        db.query(Alert).filter(Alert.student_id == student.id).order_by(Alert.created_at.desc()),
        skip, limit
    ).all()
    return [AlertOut.model_validate(a) for a in alerts]

@app.post("/api/me/alerts/{alert_id}/read", response_model=dict)
def mark_alert_read(alert_id: int, student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.student_id == student.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}

@app.get("/api/alerts", response_model=List[AlertOut])
def list_all_alerts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "records_officer", "hod"))):
    alerts = paginate(db.query(Alert).order_by(Alert.created_at.desc()), skip, limit).all()
    return [AlertOut.model_validate(a) for a in alerts]

# ─── Document Deadlines ──────────────────────────────────────────────────────

@app.post("/api/document-deadlines", response_model=DocumentDeadlineOut)
def create_deadline(data: DocumentDeadlineCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "records_officer"))):
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

@app.get("/api/document-deadlines", response_model=List[DocumentDeadlineOut])
def list_deadlines(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), actor: dict = Depends(get_current_user_or_student)):
    return [DocumentDeadlineOut.model_validate(d) for d in paginate(
        db.query(DocumentDeadline).filter(DocumentDeadline.is_active == True), skip, limit
    ).all()]

@app.delete("/api/document-deadlines/{deadline_id}", response_model=dict)
def delete_deadline(deadline_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "records_officer"))):
    dd = db.query(DocumentDeadline).filter(DocumentDeadline.id == deadline_id).first()
    if not dd:
        raise HTTPException(status_code=404, detail="Deadline not found")
    dd.is_active = False
    db.commit()
    log_action(db, user.username, "DELETE", "document_deadlines", dd.id, "Deactivated deadline")
    return {"message": "Deadline deactivated"}

# ─── Student Payments ────────────────────────────────────────────────────────

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

@app.post("/api/me/payments", response_model=StudentPaymentOut)
def make_payment(data: StudentPaymentCreate, student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    payment = StudentPayment(
        student_id=student.id,
        amount=data.amount,
        payment_type=data.payment_type,
        reference=data.reference,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

# ─── Updated Document Upload with Deadline Check ─────────────────────────────

@app.post("/api/documents", response_model=DocumentOut)
def upload_document(
    student_id: int = Form(...),
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("records_officer", "admin")),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check deadline
    late_fee = check_deadline_and_fee(db, student_id, document_type, level)
    if late_fee and late_fee > 0:
        # Check if payment was made
        paid = db.query(StudentPayment).filter(
            StudentPayment.student_id == student_id,
            StudentPayment.payment_type == f"late_fee_{document_type}_{level or 'none'}",
        ).first()
        if not paid:
            raise HTTPException(
                status_code=400,
                detail=f"Document upload deadline has passed. A late fee of ₦{late_fee:,.2f} must be paid before uploading."
            )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    if document_type == "clearance_cert" and level not in (100, 200, 300, 400, 500):
        raise HTTPException(status_code=400, detail="Level is required for clearance certificates")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    level_str = f"_{level}" if level else ""
    safe_name = f"{student.matric_number}_{document_type}{level_str}_{timestamp}{ext}"
    safe_name = safe_name.replace("/", "_")
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        student_id=student_id,
        document_type=document_type,
        level=level,
        original_filename=file.filename,
        stored_filename=safe_name,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=len(contents),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_action(db, user.username, "UPLOAD", "documents", doc.id, f"Uploaded {document_type} for {student.matric_number}")
    return doc

@app.post("/api/me/documents", response_model=DocumentOut)
def upload_my_document(
    document_type: str = Form(...),
    level: Optional[int] = Form(None),
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    # Check deadline
    late_fee = check_deadline_and_fee(db, student.id, document_type, level)
    if late_fee and late_fee > 0:
        paid = db.query(StudentPayment).filter(
            StudentPayment.student_id == student.id,
            StudentPayment.payment_type == f"late_fee_{document_type}_{level or 'none'}",
        ).first()
        if not paid:
            raise HTTPException(
                status_code=400,
                detail=f"Document upload deadline has passed. A late fee of ₦{late_fee:,.2f} must be paid before uploading."
            )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    if document_type == "clearance_cert" and level not in (100, 200, 300, 400, 500):
        raise HTTPException(status_code=400, detail="Level is required for clearance certificates")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    level_str = f"_{level}" if level else ""
    safe_name = f"{student.matric_number}_{document_type}{level_str}_{timestamp}{ext}"
    safe_name = safe_name.replace("/", "_")
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        student_id=student.id,
        document_type=document_type,
        level=level,
        original_filename=file.filename,
        stored_filename=safe_name,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=len(contents),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_action(db, student.matric_number, "UPLOAD", "documents", doc.id, f"Student uploaded {document_type}")
    return doc

# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ─── Pagination Helper ───────────────────────────────────────────────────────

def paginate(query, skip: int = 0, limit: int = 50, max_limit: int = 500):
    skip = max(0, skip)
    limit = min(max(1, limit), max_limit)
    return query.offset(skip).limit(limit)

# ─── Main Entrypoint ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
