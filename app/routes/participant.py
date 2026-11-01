import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.routes import role_required
from app.extensions import db
from app.models import Event, Registration, Feedback
from app.services.qr_service import generate_qr_for_registration
from app.services.profile_service import update_profile
from app.services.ml_service import predict_sentiment

participant_bp = Blueprint("participant", __name__, template_folder="../templates/participant")


@participant_bp.before_request
@login_required
def guard():
    pass


@participant_bp.route("/dashboard")
@role_required("participant")
def dashboard():
    upcoming = (
        Event.query.filter(Event.status == "published", Event.start_time >= datetime.utcnow())
        .order_by(Event.start_time.asc())
        .limit(4)
        .all()
    )
    my_regs = Registration.query.filter_by(user_id=current_user.id).all()
    return render_template("participant/dashboard.html", upcoming=upcoming, my_regs=my_regs)


@participant_bp.route("/events")
@role_required("participant")
def events():
    q = request.args.get("q", "")
    query = Event.query.filter_by(status="published")
    if q:
        query = query.filter(Event.title.ilike(f"%{q}%"))
    all_events = query.order_by(Event.start_time.asc()).all()
    return render_template("participant/events.html", events=all_events, q=q)


@participant_bp.route("/gallery")
@role_required("participant")
def gallery():
    """Photos uploaded by organisers. Pick an event with ?event_id=..."""
    events = Event.query.filter_by(status="published").order_by(Event.start_time.desc()).all()

    def photos_for(eid):
        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "events", str(eid))
        return sorted(os.listdir(folder)) if os.path.isdir(folder) else []

    event_id = request.args.get("event_id", type=int)
    selected = next((e for e in events if e.id == event_id), None)
    if selected is None:
        # default to the newest event that actually has photos
        selected = next((e for e in events if photos_for(e.id)), events[0] if events else None)
    photos = photos_for(selected.id) if selected else []
    return render_template("participant/gallery.html", events=events, event=selected, photos=photos)


@participant_bp.route("/events/<int:event_id>")
@role_required("participant")
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    already_registered = Registration.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    return render_template("participant/event_details.html", event=event, already_registered=already_registered)


@participant_bp.route("/events/<int:event_id>/register", methods=["POST"])
@role_required("participant")
def register_for_event(event_id):
    event = Event.query.get_or_404(event_id)

    existing = Registration.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if existing:
        flash("You're already registered for this event.", "info")
        return redirect(url_for("participant.qr_ticket", reg_id=existing.id))

    if event.seats_left <= 0:
        flash("Sorry, this event is full.", "error")
        return redirect(url_for("participant.event_details", event_id=event_id))

    registration = Registration(user_id=current_user.id, event_id=event_id)
    db.session.add(registration)
    db.session.commit()

    registration.qr_code_path = generate_qr_for_registration(registration)
    db.session.commit()

    flash(f'You\'re in! Your pass for "{event.title}" is ready.', "success")
    return redirect(url_for("participant.qr_ticket", reg_id=registration.id))


@participant_bp.route("/tickets/<int:reg_id>")
@role_required("participant")
def qr_ticket(reg_id):
    registration = Registration.query.get_or_404(reg_id)
    if registration.user_id != current_user.id:
        flash("That ticket isn't yours.", "error")
        return redirect(url_for("participant.dashboard"))
    return render_template("participant/qr_ticket.html", registration=registration)


@participant_bp.route("/my-events")
@role_required("participant")
def my_events():
    regs = Registration.query.filter_by(user_id=current_user.id).all()
    return render_template("participant/my_events.html", regs=regs)


@participant_bp.route("/certificates")
@role_required("participant")
def certificates():
    regs = (
        Registration.query.filter_by(user_id=current_user.id)
        .join(Registration.certificate)
        .all()
    )
    return render_template("participant/certificates.html", regs=regs)


@participant_bp.route("/events/<int:event_id>/feedback", methods=["GET", "POST"])
@role_required("participant")
def feedback(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        rating = min(max(int(request.form.get("rating", 5)), 1), 5)
        comments = request.form.get("comments", "").strip()
        label, score = predict_sentiment(comments, rating)
        db.session.add(Feedback(
            event_id=event_id, user_id=current_user.id, rating=rating, comments=comments,
            sentiment_label=label, sentiment_score=score,
        ))
        db.session.commit()
        flash("Thanks for the feedback!", "success")
        return redirect(url_for("participant.my_events"))
    return render_template("participant/feedback.html", event=event)


@participant_bp.route("/profile", methods=["GET", "POST"])
@role_required("participant")
def profile():
    if request.method == "POST":
        ok, message = update_profile(current_user, request.form, allow_email=True)
        flash(message, "success" if ok else "error")
        return redirect(url_for("participant.profile"))
    return render_template("participant/profile.html")