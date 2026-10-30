import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _database_url():
    """Render hands out postgres://... but SQLAlchemy needs postgresql://..."""
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url or "sqlite:///" + os.path.join(basedir, "instance", "eventsphere.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "images")
    CERT_FOLDER = os.path.join(basedir, "app", "static", "certifications")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB per request (phone photos are big)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
