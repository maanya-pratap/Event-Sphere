from app.models import User
from app.services import email_service as mail
from tests.conftest import login


def _register(client, email="new@eventsphere.test", account_type="participant"):
    return client.post(
        "/auth/register",
        data={
            "name": "New Person",
            "email": email,
            "mobile": "9876543210",
            "password": "password123",
            "confirm_password": "password123",
            "account_type": account_type,
            "society_name": "Chess Club" if account_type == "organiser" else "",
        },
        follow_redirects=True,
    )


def _link_in(message):
    return "/auth/" + message["body"].split("/auth/")[1].split()[0]


def test_register_sends_link_and_blocks_login_until_verified(client, db):
    mail.outbox.clear()
    _register(client)
    user = User.query.filter_by(email="new@eventsphere.test").first()
    assert user.email_verified is False
    assert len(mail.outbox) == 1 and mail.outbox[0]["to"] == "new@eventsphere.test"

    resp = login(client, "new@eventsphere.test")
    assert b"verify your email" in resp.data

    client.get(_link_in(mail.outbox[0]), follow_redirects=True)
    assert User.query.filter_by(email="new@eventsphere.test").first().email_verified is True
    resp = login(client, "new@eventsphere.test")
    assert b"Good to see you" in resp.data or b"Dashboard" in resp.data


def test_bad_verification_link_is_rejected(client, db):
    resp = client.get("/auth/verify/not-a-real-token", follow_redirects=True)
    assert b"invalid or has expired" in resp.data


def test_organiser_needs_verification_and_approval(client, db):
    mail.outbox.clear()
    _register(client, "org@eventsphere.test", "organiser")
    client.get(_link_in(mail.outbox[0]), follow_redirects=True)
    resp = login(client, "org@eventsphere.test")
    assert b"awaiting admin approval" in resp.data


def test_resend_verification(client, db):
    mail.outbox.clear()
    _register(client)
    client.post("/auth/resend-verification", data={"email": "new@eventsphere.test"})
    assert len(mail.outbox) == 2
    client.post("/auth/resend-verification", data={"email": "nobody@eventsphere.test"})
    assert len(mail.outbox) == 2  # unknown address: nothing sent


def test_forgot_password_full_flow(client, participant_user):
    mail.outbox.clear()
    resp = client.post("/auth/forgot-password", data={"email": participant_user.email},
                       follow_redirects=True)
    assert b"we sent a password reset link" in resp.data
    assert len(mail.outbox) == 1
    link = _link_in(mail.outbox[0])

    assert client.get(link).status_code == 200
    resp = client.post(link, data={"password": "brandnew1", "confirm_password": "brandnew1"},
                       follow_redirects=True)
    assert b"Password changed" in resp.data

    assert b"doesn" in login(client, participant_user.email, password="password123").data
    resp = login(client, participant_user.email, password="brandnew1")
    assert b"Good to see you" in resp.data or b"Dashboard" in resp.data


def test_reset_link_works_only_once(client, participant_user):
    mail.outbox.clear()
    client.post("/auth/forgot-password", data={"email": participant_user.email})
    link = _link_in(mail.outbox[0])
    client.post(link, data={"password": "brandnew1", "confirm_password": "brandnew1"})
    resp = client.get(link, follow_redirects=True)
    assert b"invalid, expired or already used" in resp.data


def test_forgot_password_unknown_email_gives_same_message(client, db):
    mail.outbox.clear()
    resp = client.post("/auth/forgot-password", data={"email": "ghost@eventsphere.test"},
                       follow_redirects=True)
    assert b"we sent a password reset link" in resp.data
    assert mail.outbox == []


def test_reset_rejects_mismatched_passwords(client, participant_user):
    mail.outbox.clear()
    client.post("/auth/forgot-password", data={"email": participant_user.email})
    link = _link_in(mail.outbox[0])
    resp = client.post(link, data={"password": "brandnew1", "confirm_password": "different"})
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data
