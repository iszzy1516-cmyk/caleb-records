"""Document upload, file storage, and vision verification helpers."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.records import log_action
from app.models import Document, Student
from app.services import storage, vision


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


@dataclass
class SavedFile:
    """Result of saving an uploaded file locally before verification."""

    local_path: Path
    safe_name: str
    ext: str


def save_upload_file(
    file: UploadFile,
    student: Student,
    document_type: str,
    level: Optional[int],
    session: Optional[str] = None,
) -> SavedFile:
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

    return SavedFile(local_path=file_path, safe_name=safe_name, ext=ext)


def _cleanup_local_file(file_path: Path) -> None:
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass


def verify_and_create_document(
    db: Session,
    student: Student,
    document_type: str,
    level: Optional[int],
    session: Optional[str],
    file: UploadFile,
    saved: SavedFile,
    actor_name: str,
) -> Document:
    verified = False
    confidence = None
    detected_type = None
    notes = None
    file_path = saved.local_path

    if vision.VISION_VERIFY_UPLOADS:
        try:
            if not vision.is_configured():
                if vision.VISION_REJECT_ON_FAILURE:
                    _cleanup_local_file(file_path)
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
                    _cleanup_local_file(file_path)
                    raise HTTPException(status_code=400, detail=vision.rejection_message(document_type, result))
                verified = result.is_correct
                confidence = result.confidence
                detected_type = result.detected_type
                notes = result.notes
        except HTTPException:
            raise
        except Exception as e:
            _cleanup_local_file(file_path)
            raise HTTPException(status_code=503, detail=f"Document verification service unavailable: {str(e)}")
    else:
        notes = "Verification disabled by configuration."

    # Capture size before any S3 upload/deletion
    file_size = saved.local_path.stat().st_size

    # Determine final storage destination
    storage_provider = "local"
    storage_key: Optional[str] = None
    public_url: Optional[str] = None
    stored_filename = saved.safe_name

    if storage.is_s3_configured():
        try:
            s3_key = f"documents/{student.college_id}/{student.department_id}/{student.id}/{saved.safe_name}"
            public_url = storage.upload_file_to_s3(
                file_path,
                s3_key,
                content_type=file.content_type or "application/octet-stream",
                original_filename=file.filename,
            )
            storage_provider = "s3"
            storage_key = s3_key
            stored_filename = s3_key
            _cleanup_local_file(file_path)
            file_path = Path(public_url)
        except Exception as e:
            _cleanup_local_file(file_path)
            raise HTTPException(status_code=503, detail=f"Failed to upload document to S3: {str(e)}")

    doc = Document(
        student_id=student.id,
        document_type=document_type,
        level=level,
        session=session,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=file_size,
        storage_provider=storage_provider,
        storage_key=storage_key,
        public_url=public_url,
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
