from flask import Blueprint, render_template
from app.models import Event
from datetime import datetime

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    upcoming = (
        Event.query.filter(Event.status == "published", Event.start_time >= datetime.utcnow())
        .order_by(Event.start_time.asc())
        .limit(6)
        .all()
    )
    return render_template("landing.html", events=upcoming)
