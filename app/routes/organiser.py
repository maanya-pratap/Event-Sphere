import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

from app.routes import role_required
from app.extensions import db
from app.models import Event, Registration, Attendance
from app.services.analytics_service import organiser_stats, event_stats
from app.services.qr_service import resolve_token
from app.services.certificate_services import generate_certificate
from app.services.profile_service import update_profile
from app.services.ml_service import event_sentiment_summary

organiser_bp = Blueprint("organiser", __name__, template_folder="../templates/organiser")


@organiser_bp.before_request
@login_required
def guard():
    pass


@organiser_bp.route("/dashboard")
@role_required("organiser")
def dashboard():
    stats = organiser_stats(current_user)
    return render_template("organiser/dashboard.html", stats=stats)


@organiser_bp.route("/events/new", methods=["GET", "POST"])
@role_required("organiser")
def create_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General")
        venue = request.form.get("venue", "").strip()
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        capacity = request.form.get("capacity", 100)

        if not title or not start_time:
            flash("Title and start time are required.", "error")
        else:
            event = Event(
                title=title,
                description=description,
                category=category,
                venue=venue,
                start_time=datetime.fromisoformat(start_time),
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                capacity=int(capacity) if capacity else 100,
                organiser_id=current_user.id,
            )
            db.session.add(event)
            db.session.commit()
            flash(f'"{event.title}" is live!', "success")
            return redirect(url_for("organiser.dashboard"))

    return render_template("organiser/create_event.html")


@organiser_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@role_required("organiser")
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organiser_id != current_user.id:
        flash("You can only edit your own events.", "error")
        return redirect(url_for("organiser.dashboard"))

    if request.method == "POST":
        event.title = request.form.get("title", event.title)
        event.description = request.form.get("description", event.description)
        event.venue = request.form.get("venue", event.venue)
        event.category = request.form.get("category", event.category)
        start_time = request.form.get("start_time")
        if start_time:
            event.start_time = datetime.fromisoformat(start_time)
        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("organiser.dashboard"))

    return render_template("organiser/edit_event.html", event=event)


@organiser_bp.route("/events/<int:event_id>/participants")
@role_required("organiser")
def participants(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("organiser/participants.html", event=event)


@organiser_bp.route("/events/<int:event_id>/scanner")
@role_required("organiser")
def scanner(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("organiser/scanner.html", event=event)


@organiser_bp.route("/events/<int:event_id>/check-in", methods=["POST"])
@role_required("organiser")
def check_in(event_id):
    """Called by scanner.js with the decoded QR token."""
    event = Event.query.get_or_404(event_id)
    if event.organiser_id != current_user.id:
        return jsonify({"ok": False, "message": "This isn't your event."}), 403

    token = request.json.get("token", "") if request.is_json else request.form.get("token", "")
    registration = resolve_token(token)

    if not registration or registration.event_id != event_id:
        return jsonify({"ok": False, "message": "QR code not recognised for this event."}), 404

    if not registration.attendance:
        registration.attendance = Attendance(present=True, checked_in_at=datetime.utcnow(), checked_in_by=current_user.id)
    elif registration.attendance.present:
        return jsonify({
            "ok": False,
            "name": registration.participant.name,
            "message": f"{registration.participant.name} is already checked in.",
        }), 409
    else:
        registration.attendance.present = True
        registration.attendance.checked_in_at = datetime.utcnow()
        registration.attendance.checked_in_by = current_user.id

    db.session.commit()

    if not registration.certificate:
        path = generate_certificate(registration)
        from app.models import Certificate
        db.session.add(Certificate(registration_id=registration.id, file_path=path))
        db.session.commit()

    # The registrant's name is returned on its own so the scanner can show it
    # large: the organiser should compare it with the person standing in front
    # of them (this is what stops a forwarded QR screenshot being used by a friend).
    return jsonify({
        "ok": True,
        "name": registration.participant.name,
        "message": f"Welcome, {registration.participant.name}!",
    })


@organiser_bp.route("/events/<int:event_id>/attendance")
@role_required("organiser")
def attendance(event_id):
    event = Event.query.get_or_404(event_id)
    stats = event_stats(event)
    return render_template("organiser/attendance.html", event=event, stats=stats)


ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed_photo(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


def _gallery_folder(event_id):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], "events", str(event_id))


@organiser_bp.route("/gallery", methods=["GET", "POST"])
@role_required("organiser")
def gallery():
    """Upload and view event photos. Pick the event with ?event_id=... (defaults to the first)."""
    events = Event.query.filter_by(organiser_id=current_user.id).order_by(Event.start_time.desc()).all()
    event_id = request.values.get("event_id", type=int)
    selected = next((e for e in events if e.id == event_id), events[0] if events else None)

    if request.method == "POST":
        if not selected:
            flash("Create an event first, then you can add photos to it.", "error")
            return redirect(url_for("organiser.gallery"))
        folder = _gallery_folder(selected.id)
        os.makedirs(folder, exist_ok=True)
        saved = skipped = 0
        for f in request.files.getlist("photos"):
            if not f or not f.filename:
                continue
            if not _allowed_photo(f.filename):
                skipped += 1
                continue
            # uuid prefix: two phones can both upload "IMG_001.jpg" without overwriting each other
            name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename)}"
            f.save(os.path.join(folder, name))
            saved += 1
        if saved:
            flash(f"{saved} photo(s) uploaded.", "success")
        if skipped:
            flash(f"{skipped} file(s) skipped — only PNG, JPG and WEBP images are allowed.", "error")
        if not saved and not skipped:
            flash("No photos selected.", "info")
        return redirect(url_for("organiser.gallery", event_id=selected.id))

    photos = []
    if selected and os.path.isdir(_gallery_folder(selected.id)):
        photos = sorted(os.listdir(_gallery_folder(selected.id)))
    return render_template("organiser/gallery.html", events=events, event=selected, photos=photos)


@organiser_bp.route("/events/<int:event_id>/gallery/<filename>/delete", methods=["POST"])
@role_required("organiser")
def delete_photo(event_id, filename):
    event = Event.query.get_or_404(event_id)
    if event.organiser_id != current_user.id:
        abort(403)
    path = os.path.join(_gallery_folder(event_id), secure_filename(filename))
    if os.path.isfile(path):
        os.remove(path)
        flash("Photo deleted.", "info")
    return redirect(url_for("organiser.gallery", event_id=event_id))


@organiser_bp.route("/profile", methods=["GET", "POST"])
@role_required("organiser")
def profile():
    if request.method == "POST":
        # Organisers can't self-change email: admin approved the account under that address.
        ok, message = update_profile(current_user, request.form, allow_email=False)
        flash(message, "success" if ok else "error")
        return redirect(url_for("organiser.profile"))
    return render_template("organiser/profile.html")


@organiser_bp.route("/analytics")
@role_required("organiser")
def analytics():
    stats = organiser_stats(current_user)
    sentiment = event_sentiment_summary(current_user.events)
    return render_template("organiser/analytics.html", stats=stats, sentiment=sentiment)
