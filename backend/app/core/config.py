from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default matches docker-compose.yml (dev). Override via .env for production.
    DATABASE_URL: str = "postgresql://clearview:clearview@localhost:5433/clearview"
    NEWSAPI_KEY: str = ""
    GOOGLE_FACTCHECK_API_KEY: str = ""
    API_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
