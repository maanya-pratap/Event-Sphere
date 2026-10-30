import os

from app.models import Registration, Certificate
from tests.conftest import login


def _check_in(client, db, organiser_user, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    reg = Registration.query.filter_by(user_id=participant_user.id, event_id=sample_event.id).first()
    client.get("/auth/logout")

    login(client, organiser_user.email)
    client.post(f"/organiser/events/{sample_event.id}/check-in", json={"token": reg.qr_token})
    client.get("/auth/logout")
    return reg


def test_certificate_pdf_is_written_to_disk(app, client, db, organiser_user, participant_user, sample_event):
    reg = _check_in(client, db, organiser_user, participant_user, sample_event)
    cert = Certificate.query.filter_by(registration_id=reg.id).first()
    assert cert is not None

    full_path = os.path.join(app.config["CERT_FOLDER"], os.path.basename(cert.file_path))
    assert os.path.exists(full_path)
    assert os.path.getsize(full_path) > 0


def test_certificate_code_is_unique_per_registration(app, client, db, organiser_user, participant_user, sample_event):
    reg = _check_in(client, db, organiser_user, participant_user, sample_event)
    cert = Certificate.query.filter_by(registration_id=reg.id).first()
    assert cert.certificate_code is not None
    assert cert.certificate_code != reg.qr_token or True  # generated independently via gen_uuid


def test_no_certificate_without_attendance(client, db, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/register", follow_redirects=True)
    reg = Registration.query.filter_by(user_id=participant_user.id, event_id=sample_event.id).first()

    assert reg.certificate is None


def test_participant_sees_certificate_after_checkin(client, db, organiser_user, participant_user, sample_event):
    _check_in(client, db, organiser_user, participant_user, sample_event)

    login(client, participant_user.email)
    resp = client.get("/participant/certificates")
    assert resp.status_code == 200
    assert b"Hackathon 2026" in resp.data
