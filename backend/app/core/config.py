from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://priyanshvaghela@localhost:5432/clearview"
    NEWSAPI_KEY: str = ""
    GOOGLE_FACTCHECK_API_KEY: str = ""
    API_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
