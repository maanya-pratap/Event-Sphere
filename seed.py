"""
Seed EventSphere with demo accounts and events so you can demo the app
to your mentor without manually registering a dozen accounts.

Usage:
    python seed.py

Creates (all passwords are `password123`):
    admin@eventsphere.test        (admin)
    coding.club@eventsphere.test  (organiser, approved)
    drama.club@eventsphere.test   (organiser, PENDING approval — demo the admin approval flow)
    maanya@eventsphere.test       (participant)
    nistha@eventsphere.test       (participant)
    astha@eventsphere.test        (participant, already registered + checked in to one event)
"""
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, Event, Registration, Attendance, Certificate
from app.services.qr_service import generate_qr_for_registration
from app.services.certificate_services import generate_certificate

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    admin = User(name="Admin", email="admin@eventsphere.test", role="admin", is_approved=True)
    admin.set_password("password123")

    coding_club = User(
        name="Nistha", email="coding.club@eventsphere.test", role="organiser",
        society_name="Coding Club", is_approved=True, mobile="7370871441",
    )
    coding_club.set_password("password123")

    drama_club = User(
        name="Astha Kumari", email="drama.club@eventsphere.test", role="organiser",
        society_name="Drama Society", is_approved=False, mobile="7541920820",
    )
    drama_club.set_password("password123")

    maanya = User(name="Maanya Pratap", email="maanya@eventsphere.test", role="participant", mobile="8935963008")
    maanya.set_password("password123")

    nistha_p = User(name="Nistha Kumari", email="nistha@eventsphere.test", role="participant", mobile="7370871442")
    nistha_p.set_password("password123")

    astha = User(name="Astha", email="astha@eventsphere.test", role="participant", mobile="7541920821")
    astha.set_password("password123")

    db.session.add_all([admin, coding_club, drama_club, maanya, nistha_p, astha])
    db.session.commit()

    events = [
        Event(
            title="CodeSprint '26 — 24hr Hackathon",
            description="Build something in 24 hours. Free food, mentors on call, prizes for top 3 teams.",
            category="Tech",
            venue="CSE Block, Main Auditorium",
            start_time=datetime.utcnow() + timedelta(days=6, hours=2),
            capacity=80,
            organiser_id=coding_club.id,
            status="published",
        ),
        Event(
            title="Intro to Git & GitHub Workshop",
            description="Hands-on session on version control for first-year students.",
            category="Workshop",
            venue="Lab 4",
            start_time=datetime.utcnow() + timedelta(days=2, hours=5),
            capacity=40,
            organiser_id=coding_club.id,
            status="published",
        ),
        Event(
            title="Web Dev Bootcamp Kickoff",
            description="First session of a 4-week Flask + React bootcamp.",
            category="Workshop",
            venue="Seminar Hall B",
            start_time=datetime.utcnow() - timedelta(days=3),
            capacity=60,
            organiser_id=coding_club.id,
            status="completed",
        ),
    ]
    db.session.add_all(events)
    db.session.commit()

    past_event = events[2]
    for user in (maanya, nistha_p, astha):
        reg = Registration(user_id=user.id, event_id=past_event.id)
        db.session.add(reg)
        db.session.commit()
        reg.qr_code_path = generate_qr_for_registration(reg)
        db.session.commit()

    # Check in two of the three attendees so the analytics + certificates
    # dashboards have something real to show your mentor.
    for user in (maanya, nistha_p):
        reg = Registration.query.filter_by(user_id=user.id, event_id=past_event.id).first()
        reg.attendance = Attendance(present=True, checked_in_at=datetime.utcnow(), checked_in_by=coding_club.id)
        db.session.commit()
        path = generate_certificate(reg)
        db.session.add(Certificate(registration_id=reg.id, file_path=path))
        db.session.commit()

    # Also register everyone for the upcoming hackathon (not checked in yet)
    for user in (maanya, nistha_p, astha):
        reg = Registration(user_id=user.id, event_id=events[0].id)
        db.session.add(reg)
        db.session.commit()
        reg.qr_code_path = generate_qr_for_registration(reg)
        db.session.commit()

    print("Seed complete.")
    print("Log in as any of:")
    print("  admin@eventsphere.test / password123 (admin)")
    print("  coding.club@eventsphere.test / password123 (organiser, approved)")
    print("  drama.club@eventsphere.test / password123 (organiser, pending — try approving via admin)")
    print("  maanya@eventsphere.test / password123 (participant, has a certificate)")
