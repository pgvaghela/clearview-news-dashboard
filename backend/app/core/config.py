from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default matches docker-compose.yml (dev). Override via .env for production.
    DATABASE_URL: str = "postgresql://clearview:clearview@localhost:5433/clearview"
    NEWSAPI_KEY: str = ""
    GOOGLE_FACTCHECK_API_KEY: str = ""
    # WebCite: https://webcite.co — sources/search uses 2 credits per call
    WEBCITE_API_KEY: str = ""
    WEBCITE_SOURCES_LIMIT: int = 10
    API_PREFIX: str = "/api/v1"
    # Comma-separated origins. In production set to your Render frontend URL.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
