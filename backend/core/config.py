from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ENVIRONMENT: str = "development"

    # API Settings
    TITLE: str = "Framily Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/framily"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "framily"
    MINIO_SECURE: bool = False

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "*"

    # Frontend static serving
    SERVE_FRONTEND: bool = False
    FRONTEND_DIST_DIR: str = "/app/frontend-build"

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT.lower() != "production":
            return self

        if self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set for production.")

        if self.CORS_ORIGINS == "*":
            raise ValueError("CORS_ORIGINS cannot be '*' in production.")

        return self


settings = Settings()
