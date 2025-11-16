from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

  APP_NAME: str = "Domyślna Nazwa Aplikacji"
  DATABASE_URL: str | None = None
  SECRET_KEY: str
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
