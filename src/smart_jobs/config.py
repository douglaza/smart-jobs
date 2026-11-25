from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    tz: str = "UTC"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smart_jobs"
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"


settings = Settings()
