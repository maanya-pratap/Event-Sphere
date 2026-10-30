from app.models import User
from tests.conftest import login


def test_register_participant(client, db):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Astha Kumari",
            "email": "astha@eventsphere.test",
            "mobile": "9876543210",
            "password": "password123",
            "confirm_password": "password123",
            "account_type": "participant",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    user = User.query.filter_by(email="astha@eventsphere.test").first()
    assert user is not None
    assert user.role == "participant"
    assert user.is_approved is True


def test_register_organiser_requires_approval(client, db):
    client.post(
        "/auth/register",
        data={
            "name": "Shreya Xaxa",
            "email": "society@eventsphere.test",
            "password": "password123",
            "confirm_password": "password123",
            "account_type": "organiser",
            "society_name": "Photography Club",
        },
        follow_redirects=True,
    )
    user = User.query.filter_by(email="society@eventsphere.test").first()
    assert user is not None
    assert user.role == "organiser"
    assert user.is_approved is False

    # A real sign-up must verify its email first; here we mark it verified so this
    # test checks the approval gate on its own (the email flow is in test_email_flow.py).
    user.email_verified = True
    db.session.commit()

    # Unapproved organiser should not be able to log in yet
    resp = login(client, "society@eventsphere.test")
    assert b"awaiting admin approval" in resp.data


def test_register_password_mismatch(client, db):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Someone",
            "email": "mismatch@eventsphere.test",
            "password": "password123",
            "confirm_password": "different",
            "account_type": "participant",
        },
        follow_redirects=True,
    )
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data
    assert User.query.filter_by(email="mismatch@eventsphere.test").first() is None


def test_login_success_and_logout(client, participant_user):
    resp = login(client, participant_user.email)
    assert resp.status_code == 200
    assert b"Good to see you" in resp.data or b"Dashboard" in resp.data

    resp = client.get("/auth/logout", follow_redirects=True)
    assert resp.status_code == 200


def test_login_wrong_password(client, participant_user):
    resp = login(client, participant_user.email, password="wrongpass")
    assert b"doesn&#39;t match" in resp.data or b"doesn't match" in resp.data


def test_duplicate_email_registration_rejected(client, participant_user):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Duplicate",
            "email": participant_user.email,
            "password": "password123",
            "confirm_password": "password123",
            "account_type": "participant",
        },
        follow_redirects=True,
    )
    assert b"already exists" in resp.data
