"""Application settings loaded from environment variables."""

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Security
    SECRET_KEY: str = "cu-records-secret-CHANGE-IN-PROD"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "sqlite:///./caleb_records.db"

    # Uploads
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost,https://localhost,http://localhost:5173,"
        "http://localhost:5174,http://localhost:8000,https://tauri.localhost,"
        "tauri://localhost,https://culrecords.duckdns.org,"
        "http://141.147.48.186,https://141.147.48.186"
    )

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@calebuniversity.edu.ng"
    FRONTEND_URL: str = "http://localhost:5173"

    # S3-compatible object storage for document uploads
    S3_UPLOAD_BUCKET: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_PUBLIC_URL: Optional[str] = None
    S3_FORCE_PATH_STYLE: bool = False

    # Vision (also read by root vision.py; mirrored here for completeness)
    VISION_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_MODEL: str = "qwen-vl-max"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    VISION_VERIFY_UPLOADS: bool = True
    VISION_MIN_CONFIDENCE: float = 0.7

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def upload_dir_resolved(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
