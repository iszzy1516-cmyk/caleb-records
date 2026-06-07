#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL.
Usage: python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Source: SQLite
sqlite_url = os.environ.get("SQLITE_URL", "sqlite:///backend/caleb_records.db")
src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
SrcSession = sessionmaker(bind=src_engine)

# Target: PostgreSQL
pg_url = os.environ.get("DATABASE_URL")
if not pg_url:
    print("Error: Set DATABASE_URL environment variable to your PostgreSQL URL")
    sys.exit(1)

tgt_engine = create_engine(pg_url, pool_pre_ping=True)
TgtSession = sessionmaker(bind=tgt_engine)

# Import models
from main import Base, Student, User, Document, College, Department, Program, AuditLog, Alert, StudentPayment, DocumentDeadline

def migrate():
    print(f"Source: {sqlite_url}")
    print(f"Target: {pg_url}")

    # Create tables in PostgreSQL
    Base.metadata.create_all(bind=tgt_engine)
    print("PostgreSQL tables created.")

    src = SrcSession()
    tgt = TgtSession()

    tables = [
        (College, "Colleges"),
        (Department, "Departments"),
        (Program, "Programs"),
        (User, "Users"),
        (Student, "Students"),
        (Document, "Documents"),
        (DocumentDeadline, "DocumentDeadlines"),
        (StudentPayment, "StudentPayments"),
        (Alert, "Alerts"),
        (AuditLog, "AuditLogs"),
    ]

    for model, name in tables:
        records = src.query(model).all()
        count = len(records)
        for r in records:
            tgt.merge(r)
        print(f"  Migrated {count} {name}")

    tgt.commit()
    src.close()
    tgt.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
