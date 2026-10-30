from app.extensions import db
from app.models import Event, Registration, Attendance, Feedback, User


def platform_stats():
    return {
        "total_events": Event.query.count(),
        "total_users": User.query.filter_by(role="participant").count(),
        "total_organisers": User.query.filter_by(role="organiser").count(),
        "total_registrations": Registration.query.count(),
        "total_attendance": Attendance.query.filter_by(present=True).count(),
    }


def event_stats(event):
    regs = event.registrations
    present = sum(1 for r in regs if r.attendance and r.attendance.present)
    ratings = [f.rating for f in event.feedback]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    return {
        "registrations": len(regs),
        "present": present,
        "absent": len(regs) - present,
        "avg_rating": avg_rating,
        "feedback_count": len(ratings),
    }


def organiser_stats(organiser):
    events = organiser.events
    return {
        "event_count": len(events),
        "total_registrations": sum(len(e.registrations) for e in events),
        "total_attendance": sum(e.attendance_count for e in events),
        "events": events,
    }
