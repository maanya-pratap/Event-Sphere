import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _database_url():
    """Force the psycopg2 driver we install, whatever URL style Render gives."""
    url = os.environ.get("DATABASE_URL")
    if url:
        url = url.strip().strip('"').strip("'")
        for prefix in ("postgres://", "postgresql://",
                       "postgresql+psycopg://", "postgresql+psycopg2://"):
            if url.startswith(prefix):
                url = "postgresql+psycopg2://" + url[len(prefix):]
                break
    return url or "sqlite:///" + os.path.join(basedir, "instance", "eventsphere.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "images")
    CERT_FOLDER = os.path.join(basedir, "app", "static", "certifications")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB per request (phone photos are big)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
