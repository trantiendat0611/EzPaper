from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EzPaper API"
    database_url: str = "postgresql+psycopg://ezpaper:ezpaper@localhost:5432/ezpaper"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
