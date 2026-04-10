from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mac/Homebrew/Postgres.app: use Unix socket (no TCP password prompt).
    # If this fails, run: psql -c "SHOW unix_socket_directories;" and set ?host= to that path.
    DATABASE_URL: str = "postgresql://priyanshvaghela@/clearview?host=/tmp"
    NEWSAPI_KEY: str = ""
    GOOGLE_FACTCHECK_API_KEY: str = ""
    API_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
