import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV != "production"

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

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "eventhub-super-secret-key-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))
    )

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Allow admin registration via API (set to "true" in .env to enable)
    ALLOW_ADMIN_REGISTRATION = os.getenv("ALLOW_ADMIN_REGISTRATION", "true").lower() == "true"

    # Appwrite Configuration
    APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
    APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "")
    APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "")
    APPWRITE_BUCKET_ID = os.getenv("APPWRITE_BUCKET_ID", "")
