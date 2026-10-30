import os

from app.models import User, Event, Registration, Attendance, Certificate, Feedback
from tests.conftest import login


def _full_flow(client, organiser_user, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    reg = Registration.query.filter_by(user_id=participant_user.id).first()
    client.get("/auth/logout")
    login(client, organiser_user.email)
    client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": reg.qr_token})
    client.get("/auth/logout")
    return reg


def test_admin_deletes_participant_and_all_their_data(app, client, db, admin_user, organiser_user, participant_user, sample_event):
    reg = _full_flow(client, organiser_user, participant_user, sample_event)
    cert_file = os.path.join(app.config["CERT_FOLDER"], os.path.basename(Certificate.query.first().file_path))
    assert os.path.exists(cert_file)
    db.session.add(Feedback(event_id=sample_event.id, user_id=participant_user.id, rating=4, comments="nice"))
    db.session.commit()

    login(client, admin_user.email)
    resp = client.post(f"/admin/users/{participant_user.id}/delete", follow_redirects=True)
    assert resp.status_code == 200

    assert User.query.get(participant_user.id) is None
    assert Registration.query.count() == 0
    assert Attendance.query.count() == 0
    assert Certificate.query.count() == 0
    assert Feedback.query.count() == 0
    assert not os.path.exists(cert_file)
    assert Event.query.count() == 1  # the event itself survives


def test_admin_deletes_organiser_with_events_and_checkins(client, db, admin_user, organiser_user, participant_user, sample_event):
    _full_flow(client, organiser_user, participant_user, sample_event)

    login(client, admin_user.email)
    client.post(f"/admin/users/{organiser_user.id}/delete", follow_redirects=True)

    assert User.query.get(organiser_user.id) is None
    assert Event.query.count() == 0
    assert Registration.query.count() == 0
    assert User.query.get(participant_user.id) is not None  # participants themselves remain


def test_admin_cannot_delete_admin(client, db, admin_user):
    login(client, admin_user.email)
    client.post(f"/admin/users/{admin_user.id}/delete", follow_redirects=True)
    assert User.query.get(admin_user.id) is not None


def test_participant_cannot_delete_users(client, db, participant_user, organiser_user):
    login(client, participant_user.email)
    resp = client.post(f"/admin/users/{organiser_user.id}/delete")
    assert resp.status_code == 403
    assert User.query.get(organiser_user.id) is not None
