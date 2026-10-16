from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CirrusLabs TalentHub API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "cirruslabs_talenthub"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://localhost:8443,http://127.0.0.1:8443"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    allow_self_registration: bool = True
    registration_email_domain: str = "cirruslabs.io"
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""
    resume_storage_dir: str = "storage/resumes"
    resume_max_size_bytes: int = 5 * 1024 * 1024
    avatar_storage_dir: str = "storage/avatars"
    avatar_max_size_bytes: int = 2 * 1024 * 1024
    avatar_allowed_content_types: str = "image/jpeg,image/png,image/webp"
    dashboard_recent_limit: int = 6
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def avatar_content_types(self) -> set[str]:
        return {value.strip().lower() for value in self.avatar_allowed_content_types.split(",") if value.strip()}

    @property
    def dashboard_recent_size(self) -> int:
        # Guard against a zero/negative configuration producing an empty slice.
        return max(1, self.dashboard_recent_limit)

@lru_cache
def get_settings() -> Settings:
    return Settings()
