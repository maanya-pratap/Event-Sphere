from datetime import datetime, timedelta

from app.models import Event
from tests.conftest import login


def test_organiser_can_create_event(client, db, organiser_user):
    login(client, organiser_user.email)
    start = (datetime.utcnow() + timedelta(days=5)).isoformat()

    resp = client.post(
        "/organiser/events/new",
        data={
            "title": "Design Sprint",
            "description": "A one-day UI/UX sprint",
            "category": "Design",
            "venue": "Lab 2",
            "start_time": start,
            "capacity": "30",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    event = Event.query.filter_by(title="Design Sprint").first()
    assert event is not None
    assert event.organiser_id == organiser_user.id
    assert event.capacity == 30


def test_participant_cannot_create_event(client, participant_user):
    login(client, participant_user.email)
    resp = client.get("/organiser/events/new")
    assert resp.status_code == 403


def test_anonymous_redirected_from_event_creation(client):
    resp = client.get("/organiser/events/new", follow_redirects=True)
    assert resp.status_code == 200
    assert b"log in" in resp.data.lower()


def test_organiser_cannot_edit_others_event(client, db, organiser_user, sample_event):
    from app.models import User

    other = User(name="Other Org", email="other@eventsphere.test", role="organiser",
                 society_name="Drama Club", is_approved=True)
    other.set_password("password123")
    db.session.add(other)
    db.session.commit()

    login(client, other.email)
    resp = client.post(
        f"/organiser/events/{sample_event.id}/edit",
        data={"title": "Hijacked title"},
        follow_redirects=True,
    )
    db.session.refresh(sample_event)
    assert sample_event.title == "Hackathon 2026"


def test_published_event_visible_to_participants(client, participant_user, sample_event):
    login(client, participant_user.email)
    resp = client.get("/participant/events")
    assert resp.status_code == 200
    assert b"Hackathon 2026" in resp.data
