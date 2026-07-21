"""Document upload, file storage, and vision verification helpers."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.records import log_action
from app.models import Document, Student
from app.services import vision


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def save_upload_file(
    file: UploadFile,
    student: Student,
    document_type: str,
    level: Optional[int],
    session: Optional[str] = None,
) -> Path:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if document_type == "clearance_cert" and level not in (100, 200, 300, 400, 500):
        raise HTTPException(status_code=400, detail="Level is required for clearance certificates")
    if document_type == "clearance_cert" and not session:
        raise HTTPException(status_code=400, detail="Academic session is required for clearance certificates")

    contents = file.file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {settings.MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit",
        )

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    level_str = f"_{level}" if level else ""
    session_str = f"_{session.replace('/', '_')}" if session else ""
    safe_name = f"{student.matric_number}_{document_type}{level_str}{session_str}_{timestamp}{ext}"
    safe_name = safe_name.replace("/", "_")
    file_path = settings.upload_dir_resolved / safe_name

    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path


def verify_and_create_document(
    db: Session,
    student: Student,
    document_type: str,
    level: Optional[int],
    session: Optional[str],
    file: UploadFile,
    file_path: Path,
    actor_name: str,
) -> Document:
    verified = False
    confidence = None
    detected_type = None
    notes = None

    if vision.VISION_VERIFY_UPLOADS:
        try:
            if not vision.is_configured():
                if vision.VISION_REJECT_ON_FAILURE:
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Document verification is required but no vision provider is configured. "
                            "Please set VISION_PROVIDER and the corresponding API key, or set VISION_REJECT_ON_FAILURE=false."
                        ),
                    )
                # Provider not configured but rejection is disabled; save unverified
                notes = "Vision provider not configured; verification skipped."
            else:
                result = vision.verify_document(str(file_path), document_type)
                if not vision.should_accept(result):
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=400, detail=vision.rejection_message(document_type, result))
                verified = result.is_correct
                confidence = result.confidence
                detected_type = result.detected_type
                notes = result.notes
        except HTTPException:
            raise
        except Exception as e:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=503, detail=f"Document verification service unavailable: {str(e)}")
    else:
        notes = "Verification disabled by configuration."

    doc = Document(
        student_id=student.id,
        document_type=document_type,
        level=level,
        session=session,
        original_filename=file.filename,
        stored_filename=file_path.name,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=file_path.stat().st_size,
        verified=verified,
        verification_confidence=confidence,
        verification_detected_type=detected_type,
        verification_notes=notes,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_action(db, actor_name, "UPLOAD", "documents", doc.id, f"Uploaded {document_type} for {student.matric_number}")
    return doc
