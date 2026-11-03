"""Captcha, 5th-wrong-password lock (5 hours) and unlock behaviour."""
from datetime import datetime, timedelta

from app.models import User
from app.services.captcha_service import make_hash
from tests.conftest import login


def test_four_wrong_passwords_do_not_lock(client, participant_user, db):
    for _ in range(4):
        resp = login(client, participant_user.email, password="wrong")
        assert b"attempt" in resp.data
    db.session.refresh(participant_user)
    assert participant_user.failed_attempts == 4
    assert not participant_user.is_locked


def test_fifth_wrong_password_locks_for_five_hours(client, participant_user, db):
    for _ in range(5):
        resp = login(client, participant_user.email, password="wrong")
    assert b"locked for 5 hours" in resp.data
    db.session.refresh(participant_user)
    assert participant_user.is_locked
    left = participant_user.locked_until - datetime.utcnow()
    assert timedelta(hours=4, minutes=59) < left <= timedelta(hours=5)


def test_correct_password_refused_while_locked(client, participant_user, db):
    for _ in range(5):
        login(client, participant_user.email, password="wrong")
    resp = login(client, participant_user.email)  # the right password
    assert b"locked" in resp.data
    assert b"Log out" not in resp.data


def test_lock_expires_after_five_hours(client, participant_user, db):
    for _ in range(5):
        login(client, participant_user.email, password="wrong")
    participant_user.locked_until = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    resp = login(client, participant_user.email)
    assert b"Good to see you" in resp.data


def test_successful_login_resets_counter(client, participant_user, db):
    for _ in range(3):
        login(client, participant_user.email, password="wrong")
    login(client, participant_user.email)
    db.session.refresh(participant_user)
    assert participant_user.failed_attempts == 0


def test_unknown_email_gives_generic_error(client, db):
    resp = login(client, "nobody@eventsphere.test", password="x")
    assert b"email/password combination" in resp.data


def test_captcha_required_when_enabled(client, app, participant_user):
    app.config["CAPTCHA_ENABLED"] = True
    # no captcha typed -> refused even with the right password
    resp = client.post("/auth/login", data={"email": participant_user.email, "password": "password123"},
                       follow_redirects=True)
    assert b"captcha text was wrong" in resp.data

    # wrong captcha does not count as a password attempt
    with client.session_transaction() as sess:
        sess["captcha_hash"] = make_hash("ABCDE")
    client.post("/auth/login", data={"email": participant_user.email, "password": "wrong", "captcha": "ZZZZZ"})
    assert User.query.get(participant_user.id).failed_attempts == 0

    # right captcha + right password gets in
    with client.session_transaction() as sess:
        sess["captcha_hash"] = make_hash("ABCDE")
    resp = client.post("/auth/login", data={"email": participant_user.email, "password": "password123",
                                            "captcha": "abcde"}, follow_redirects=True)
    assert b"Good to see you" in resp.data


def test_captcha_is_single_use(client, app, participant_user):
    app.config["CAPTCHA_ENABLED"] = True
    with client.session_transaction() as sess:
        sess["captcha_hash"] = make_hash("QWERT")
    client.post("/auth/login", data={"email": participant_user.email, "password": "wrong", "captcha": "QWERT"})
    resp = client.post("/auth/login", data={"email": participant_user.email, "password": "password123",
                                            "captcha": "QWERT"}, follow_redirects=True)
    assert b"captcha text was wrong" in resp.data


def test_captcha_image_is_png(client):
    resp = client.get("/auth/captcha.png")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    assert resp.data[:4] == b"\x89PNG"
