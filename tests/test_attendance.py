from app.models import Registration, Attendance, Certificate
from tests.conftest import login


def _register(client, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    reg = Registration.query.filter_by(user_id=participant_user.id, event_id=sample_event.id).first()
    client.get("/auth/logout")
    return reg


def test_organiser_can_check_in_valid_token(client, db, organiser_user, participant_user, sample_event):
    reg = _register(client, participant_user, sample_event)

    login(client, organiser_user.email)
    resp = client.post(
        f"/organiser/events/{sample_event.id}/check-in",
        json={"token": reg.qr_token},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True

    attendance = Attendance.query.filter_by(registration_id=reg.id).first()
    assert attendance is not None
    assert attendance.present is True
    # a certificate should be auto-issued on first check-in
    assert Certificate.query.filter_by(registration_id=reg.id).first() is not None


def test_checkin_rejects_unknown_token(client, organiser_user, sample_event):
    login(client, organiser_user.email)
    resp = client.post(
        f"/organiser/events/{sample_event.id}/check-in",
        json={"token": "not-a-real-token"},
    )
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False


def test_checkin_rejects_second_scan(client, db, organiser_user, participant_user, sample_event):
    reg = _register(client, participant_user, sample_event)
    login(client, organiser_user.email)

    client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": reg.qr_token})
    resp = client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": reg.qr_token})

    assert resp.status_code == 409
    assert "already checked in" in resp.get_json()["message"]


def test_checkin_rejects_token_from_other_event(client, db, organiser_user, participant_user, sample_event):
    from datetime import datetime, timedelta
    from app.models import Event

    other_event = Event(
        title="Other Event",
        start_time=datetime.utcnow() + timedelta(days=1),
        organiser_id=organiser_user.id,
        status="published",
    )
    db.session.add(other_event)
    db.session.commit()

    reg = _register(client, participant_user, sample_event)
    login(client, organiser_user.email)
    resp = client.post(f"/organiser/events/{other_event.id}/check-in", json={"token": reg.qr_token})
    assert resp.status_code == 404
