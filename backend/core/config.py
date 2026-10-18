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

    # S3-compatible storage (Garage)
    S3_ENDPOINT: str = "garage:3900"
    S3_ACCESS_KEY: str = "garageadmin"
    S3_SECRET_KEY: str = "garageadmin"
    S3_BUCKET: str = "framily"
    S3_REGION: str = "garage"
    S3_SECURE: bool = False

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Password reset
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    # Public base URL of the web app, used to build the link in password reset
    # emails (e.g. https://framily.example.com). Falls back to the first
    # CORS origin, see public_url.
    PUBLIC_URL: str = ""

    # SMTP (outgoing mail). Password reset is disabled unless SMTP_HOST is set.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    # "starttls" (usually port 587), "ssl" (implicit TLS, usually port 465) or "none"
    SMTP_SECURITY: str = "starttls"
    SMTP_TIMEOUT: int = 10

    # CORS
    CORS_ORIGINS: str = "*"

    # Frontend static serving
    SERVE_FRONTEND: bool = False
    FRONTEND_DIST_DIR: str = "/app/frontend-build"

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST)

    @property
    def public_url(self) -> str:
        if self.PUBLIC_URL:
            return self.PUBLIC_URL.rstrip("/")
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]
        if origins:
            return origins[0].rstrip("/")
        return "http://localhost:5173"

    @model_validator(mode="after")
    def validate_smtp_settings(self):
        if self.SMTP_SECURITY.lower() not in ("starttls", "ssl", "none"):
            raise ValueError("SMTP_SECURITY must be one of: starttls, ssl, none.")
        if self.SMTP_HOST and not (self.SMTP_FROM or self.SMTP_USERNAME):
            raise ValueError("SMTP_FROM must be set when SMTP_HOST is set.")
        return self

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
