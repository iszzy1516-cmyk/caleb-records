"""FastAPI application factory and startup logic."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded

from app.api import (
    alerts,
    auth,
    deadlines,
    documents,
    grades,
    health,
    me,
    password_reset,
    public,
    reference,
    reports,
    stats,
    students,
    users,
)
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.limiter import limiter
from app.core.middleware import OptionsCorsMiddleware, SecurityHeadersMiddleware
from app.core.security import get_password_hash
from app.crud.records import recalculate_student_levels
from app.models import College, Department, Program, User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_reference_data(db)
        _seed_default_user(db)
        recalculate_student_levels(db)
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

    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=500)

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS middleware (handles preflight and actual requests for web + mobile webviews)
    app.add_middleware(OptionsCorsMiddleware)

    # Routers
    app.include_router(auth.router)
    app.include_router(reference.router)
    app.include_router(students.router)
    app.include_router(documents.router)
    app.include_router(grades.router)
    app.include_router(reports.router)
    app.include_router(public.router)
    app.include_router(me.router)
    app.include_router(users.router)
    app.include_router(password_reset.router)
    app.include_router(stats.router)
    app.include_router(alerts.router)
    app.include_router(deadlines.router)
    app.include_router(health.router)

    return app


def _rate_limit_exceeded_handler(request, exc):
    # Re-use slowapi's default handler
    from slowapi import _rate_limit_exceeded_handler

    return _rate_limit_exceeded_handler(request, exc)


def _seed_reference_data(db):
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
    estate_mgmt = Department(name="Estate Management", college_id=2)
    building = Department(name="Building Technology", college_id=2)
    qs = Department(name="Quantity Surveying", college_id=2)
    education = Department(name="Early Childhood Education", college_id=1)

    for d in [cs_dept, cyber_dept, se_dept, accounting, bizadmin, economics, masscom, law, nursing, architecture, estate_mgmt, building, qs, education]:
        db.add(d)
    db.commit()

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
    db.add(Program(name="B.Sc. Estate Management", department_id=estate_mgmt.id, duration_years=5))
    db.add(Program(name="B.Sc. Building Technology", department_id=building.id, duration_years=5))
    db.add(Program(name="B.Sc. Quantity Surveying", department_id=qs.id, duration_years=5))
    db.add(Program(name="B.Ed. Early Childhood Education", department_id=education.id, duration_years=4))
    db.commit()


def _seed_default_user(db):
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


app = create_app()
