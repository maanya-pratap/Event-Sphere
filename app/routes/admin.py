from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.routes import role_required
from app.extensions import db
from app.models import User, Event, Attendance
from app.services.analytics_service import platform_stats
from app.services.cleanup_service import collect_user_files, collect_event_photo_folders, remove_files

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.before_request
@login_required
def guard():
    pass


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    stats = platform_stats()
    pending = User.query.filter_by(role="organiser", is_approved=False).all()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, pending=pending, recent_events=recent_events)


@admin_bp.route("/organisers")
@role_required("admin")
def organisers():
    all_organisers = User.query.filter_by(role="organiser").order_by(User.is_approved.asc()).all()
    return render_template("admin/organisers.html", organisers=all_organisers)


@admin_bp.route("/organisers/<int:user_id>/approve", methods=["POST"])
@role_required("admin")
def approve_organiser(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"{user.society_name or user.name} approved.", "success")
    return redirect(url_for("admin.organisers"))


@admin_bp.route("/organisers/<int:user_id>/reject", methods=["POST"])
@role_required("admin")
def reject_organiser(user_id):
    """Reject a pending application — same full removal as delete_user."""
    return delete_user(user_id)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_id):
    """Permanently delete a participant or organiser and everything tied to them.

    Order matters:
      1. collect the file paths (needs the rows to still exist)
      2. null Attendance.checked_in_by for check-ins this user performed
         (an organiser's scans of OTHER people's rows must not block the delete)
      3. delete the user row -> SQLAlchemy cascades to events, registrations,
         attendance, certificates and feedback
      4. remove the QR / certificate / gallery files from disk
    """
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin accounts can't be deleted from here.", "error")
        return redirect(request.referrer or url_for("admin.dashboard"))

    name = user.society_name or user.name
    is_organiser = user.role == "organiser"
    file_paths = collect_user_files(user)
    photo_folders = collect_event_photo_folders(user)

    Attendance.query.filter_by(checked_in_by=user.id).update({"checked_in_by": None})
    db.session.delete(user)
    db.session.commit()

    remove_files(file_paths, photo_folders)
    flash(f"{name} and all associated data were permanently deleted.", "success")
    return redirect(url_for("admin.organisers" if is_organiser else "admin.users"))


@admin_bp.route("/events")
@role_required("admin")
def events():
    all_events = Event.query.order_by(Event.start_time.desc()).all()
    return render_template("admin/events.html", events=all_events)


@admin_bp.route("/users")
@role_required("admin")
def users():
    all_users = User.query.filter_by(role="participant").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/analytics")
@role_required("admin")
def analytics():
    stats = platform_stats()
    top_events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
    return render_template("admin/analytics.html", stats=stats, top_events=top_events)
