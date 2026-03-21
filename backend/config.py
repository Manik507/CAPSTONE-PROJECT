import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    """
    Centralized Flask configuration.

    Environment variables supported (recommended):
      - DATABASE_URL=postgresql://user:pass@host:5432/dbname
      - JWT_SECRET_KEY=super-secret
      - FLASK_ENV=development|production
    """

    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV != "production"

    # Prefer a full DATABASE_URL; fall back to discrete parts if provided.
    _database_url = os.getenv("DATABASE_URL")
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "eventhub")
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))
    )

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Auth behavior
    ALLOW_ADMIN_REGISTRATION = os.getenv("ALLOW_ADMIN_REGISTRATION", "false").lower() == "true"
