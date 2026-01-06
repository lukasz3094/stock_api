from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
      env_file=".env", env_file_encoding='utf-8', extra='ignore')

  APP_NAME: str = "Domyślna Nazwa Aplikacji"
  DATABASE_URL: str | None = None
  SECRET_KEY: str
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
  GEMINI_API_KEY: str | None = None

  # Email Settings
  MAIL_USERNAME: str = "your_email@example.com"
  MAIL_PASSWORD: str = "your_password"
  MAIL_FROM: str = "your_email@example.com"
  MAIL_PORT: int = 587
  MAIL_SERVER: str = "smtp.gmail.com"
  MAIL_STARTTLS: bool = True
  MAIL_SSL_TLS: bool = False
  USE_CREDENTIALS: bool = True
  VALIDATE_CERTS: bool = True


settings = Settings()
