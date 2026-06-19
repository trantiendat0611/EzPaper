from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EzPaper API"
    database_url: str = "postgresql+psycopg://ezpaper:ezpaper@localhost:5432/ezpaper"
    secret_key: str = "change-this-secret-key-before-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    upload_dir: str = "storage/uploads"
    max_upload_size_mb: int = 25
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    ai_provider: str = "auto"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
