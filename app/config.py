from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Строка подключения берётся из переменной окружения DATABASE_URL (или из .env)
    database_url: str


settings = Settings()
