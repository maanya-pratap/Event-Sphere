from datetime import datetime, timedelta

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User, Event


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    TESTING = True
    CAPTCHA_ENABLED = False  # the captcha has its own tests in test_login_security.py
    UPLOAD_FOLDER = "/tmp/eventsphere_test_uploads"
    CERT_FOLDER = "/tmp/eventsphere_test_certs"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def admin_user(db):
    user = User(name="Admin", email="admin@eventsphere.test", role="admin", is_approved=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def organiser_user(db):
    user = User(
        name="Nistha",
        email="organiser@eventsphere.test",
        role="organiser",
        society_name="Coding Club",
        is_approved=True,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def participant_user(db):
    user = User(name="Maanya Pratap", email="participant@eventsphere.test", role="participant")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def sample_event(db, organiser_user):
    event = Event(
        title="Hackathon 2026",
        description="24-hour build sprint",
        category="Tech",
        venue="Main Auditorium",
        start_time=datetime.utcnow() + timedelta(days=3),
        capacity=50,
        organiser_id=organiser_user.id,
        status="published",
    )
    db.session.add(event)
    db.session.commit()
    return event


def login(client, email, password="password123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
