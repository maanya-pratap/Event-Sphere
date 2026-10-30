import io
import os
import shutil

from app.models import Registration
from tests.conftest import login


def test_organiser_uploads_photo_and_bad_type_is_skipped(app, client, db, organiser_user, sample_event):
    shutil.rmtree(os.path.join(app.config["UPLOAD_FOLDER"], "events", str(sample_event.id)), ignore_errors=True)
    login(client, organiser_user.email)
    data = {"photos": [(io.BytesIO(b"fakepng"), "pic.png"), (io.BytesIO(b"x"), "evil.exe")]}
    client.post(f"/organiser/gallery?event_id={sample_event.id}", data=data,
                content_type="multipart/form-data", follow_redirects=True)
    folder = os.path.join(app.config["UPLOAD_FOLDER"], "events", str(sample_event.id))
    files = os.listdir(folder)
    assert len(files) == 1 and files[0].endswith("pic.png")


def test_checkin_returns_registrant_name(client, db, organiser_user, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register")
    reg = Registration.query.first()
    client.get("/auth/logout")
    login(client, organiser_user.email)
    data = client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": reg.qr_token}).get_json()
    assert data["name"] == "Maanya Pratap"


def test_other_organiser_cannot_scan_for_this_event(client, db, organiser_user, participant_user, sample_event):
    from app.models import User
    other = User(name="Other", email="other@eventsphere.test", role="organiser", is_approved=True)
    other.set_password("password123")
    db.session.add(other)
    db.session.commit()
    login(client, other.email)
    resp = client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": "x"})
    assert resp.status_code == 403
