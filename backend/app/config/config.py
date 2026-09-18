from base64 import b64decode

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tempfile import gettempdir


class Settings(BaseSettings):
    app_name: str = Field(default="MethodAlign IS API", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="methodalign", alias="POSTGRES_DB")
    postgres_driver: str = Field(default="psycopg", alias="POSTGRES_DRIVER")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_exp_minutes: int = Field(default=480, alias="JWT_EXP_MINUTES")
    auth_whitelist_paths: str = Field(
        default="/health,/docs,/openapi.json,/api/v1/admin/login,/api/v1/assessments,/api/v1/questionnaire,/api/v1/assessment-drafts",
        alias="AUTH_WHITELIST_PATHS",
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    assessment_documents_dir: str = Field(
        default=f"{gettempdir()}/methodalign-assessment-documents",
        alias="ASSESSMENT_DOCUMENTS_DIR",
    )
    participant_cookie_name: str = Field(default="methodalign_assessment", alias="PARTICIPANT_COOKIE_NAME")
    participant_cookie_secure: bool = Field(default=False, alias="PARTICIPANT_COOKIE_SECURE")
    document_encryption_key_base64: str = Field(
        default="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        alias="DOCUMENT_ENCRYPTION_KEY_BASE64",
    )
    document_encryption_key_version: str = Field(default="v1", alias="DOCUMENT_ENCRYPTION_KEY_VERSION")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_generation_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_GENERATION_MODEL")
    gemini_embedding_model: str = Field(default="gemini-embedding-2", alias="GEMINI_EMBEDDING_MODEL")
    gemini_embedding_dimensions: int = Field(default=768, alias="GEMINI_EMBEDDING_DIMENSIONS")
    gemini_request_timeout_ms: int = Field(default=90_000, alias="GEMINI_REQUEST_TIMEOUT_MS")
    gemini_min_request_interval_seconds: float = Field(
        default=8.0,
        alias="GEMINI_MIN_REQUEST_INTERVAL_SECONDS",
    )
    document_worker_poll_seconds: float = Field(default=2.0, alias="DOCUMENT_WORKER_POLL_SECONDS")
    document_worker_retry_limit: int = Field(default=3, alias="DOCUMENT_WORKER_RETRY_LIMIT")
    traditional_advisor_worker_poll_seconds: float = Field(default=2.0, alias="TRADITIONAL_ADVISOR_WORKER_POLL_SECONDS")
    traditional_advisor_retry_limit: int = Field(default=3, alias="TRADITIONAL_ADVISOR_RETRY_LIMIT")
    pdf_min_extracted_characters: int = Field(default=200, alias="PDF_MIN_EXTRACTED_CHARACTERS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("postgres_driver")
    @classmethod
    def validate_driver(cls, value: str) -> str:
        if value != "psycopg":
            raise ValueError("POSTGRES_DRIVER must be psycopg")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("JWT_SECRET must be at least 8 characters")
        return value

    @field_validator("document_encryption_key_base64")
    @classmethod
    def validate_document_encryption_key(cls, value: str) -> str:
        try:
            decoded = b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError("DOCUMENT_ENCRYPTION_KEY_BASE64 must be base64 encoded.") from exc
        if len(decoded) != 32:
            raise ValueError("DOCUMENT_ENCRYPTION_KEY_BASE64 must decode to exactly 32 bytes.")
        return value

    @field_validator("gemini_embedding_dimensions")
    @classmethod
    def validate_embedding_dimensions(cls, value: int) -> int:
        # The pgvector column and index are deliberately fixed at 768 dimensions.
        if value != 768:
            raise ValueError("GEMINI_EMBEDDING_DIMENSIONS must be 768 for the current pgvector schema.")
        return value

    @field_validator("gemini_min_request_interval_seconds")
    @classmethod
    def validate_gemini_request_interval(cls, value: float) -> float:
        if value < 0:
            raise ValueError("GEMINI_MIN_REQUEST_INTERVAL_SECONDS must be zero or greater.")
        return value

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+{self.postgres_driver}://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def auth_whitelist(self) -> set[str]:
        whitelist = {item.strip() for item in self.auth_whitelist_paths.split(",") if item.strip()}
        whitelist.add("/api/v1/assessment-drafts")
        return whitelist

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]


settings = Settings()
