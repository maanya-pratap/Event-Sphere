from app.models import Registration, Event
from tests.conftest import login


def test_participant_can_register_for_event(client, db, participant_user, sample_event):
    login(client, participant_user.email)
    resp = client.post(
        f"/participant/events/{sample_event.id}/register",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    reg = Registration.query.filter_by(user_id=participant_user.id, event_id=sample_event.id).first()
    assert reg is not None
    assert reg.qr_token is not None
    assert reg.qr_code_path is not None


def test_cannot_register_twice(client, db, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)

    count = Registration.query.filter_by(user_id=participant_user.id, event_id=sample_event.id).count()
    assert count == 1


def test_registration_blocked_when_event_full(client, db, participant_user, sample_event):
    sample_event.capacity = 0
    db.session.commit()

    login(client, participant_user.email)
    resp = client.post(
        f"/participant/events/{sample_event.id}/register",
        follow_redirects=True,
    )
    assert b"full" in resp.data.lower()
    assert Registration.query.filter_by(event_id=sample_event.id).count() == 0


def test_qr_ticket_only_visible_to_owner(client, db, participant_user, sample_event):
    from app.models import User

    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    reg = Registration.query.filter_by(user_id=participant_user.id).first()
    client.get("/auth/logout")

    other = User(name="Nosy", email="nosy@eventsphere.test", role="participant")
    other.set_password("password123")
    db.session.add(other)
    db.session.commit()

    login(client, other.email)
    resp = client.get(f"/participant/tickets/{reg.id}", follow_redirects=True)
    assert b"isn&#39;t yours" in resp.data or b"isn't yours" in resp.data
