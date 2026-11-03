import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager


def gen_uuid():
    return uuid.uuid4().hex


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    # roles: admin | organiser | participant
    role = db.Column(db.String(20), nullable=False, default="participant")
    # organiser-specific
    society_name = db.Column(db.String(150))
    is_approved = db.Column(db.Boolean, default=False)  # organisers need admin approval
    # New sign-ups are set to False by the register route and flip to True when they click
    # the emailed link. The default is True so accounts created by seed.py/tests are trusted.
    email_verified = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(255), default="default.png")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
        # Login protection: wrong passwords in a row, and when the lock (if any) ends (UTC)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    locked_until = db.Column(db.DateTime, nullable=True)


    # cascade="all, delete-orphan": deleting a User also deletes everything that
    # belongs to them (their events, registrations, feedback) so no orphan rows remain.
    events = db.relationship(
        "Event", backref="organiser", lazy=True, foreign_keys="Event.organiser_id",
        cascade="all, delete-orphan",
    )
    registrations = db.relationship(
        "Registration", backref="participant", lazy=True, cascade="all, delete-orphan",
    )
    feedback_given = db.relationship(
        "Feedback", backref="author", lazy=True, cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # ---- brute-force protection -------------------------------------------------
    MAX_FAILED_ATTEMPTS = 5   # the 5th wrong password locks the account
    LOCK_HOURS = 5

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > datetime.utcnow())

    def lock_time_left(self):
        """Human-readable time until the lock ends, e.g. '4 h 59 min'."""
        if not self.is_locked:
            return ""
        minutes = int((self.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        hours, mins = divmod(minutes, 60)
        return f"{hours} h {mins} min" if hours else f"{mins} min"

    def register_failed_attempt(self):
        """Count a wrong password. Returns True if this attempt locked the account."""
        if self.locked_until and self.locked_until <= datetime.utcnow():
            self.failed_attempts = 0      # an old lock has run out, start counting afresh
            self.locked_until = None
        self.failed_attempts = (self.failed_attempts or 0) + 1
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.locked_until = datetime.utcnow() + timedelta(hours=self.LOCK_HOURS)
            return True
        return False

    def clear_failed_attempts(self):
        self.failed_attempts = 0
        self.locked_until = None

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_organiser(self):
        return self.role == "organiser"

    @property
    def is_participant(self):
        return self.role == "participant"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(60), default="General")
    venue = db.Column(db.String(150))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    banner_image = db.Column(db.String(255), default="default_event.png")
    capacity = db.Column(db.Integer, default=100)
    organiser_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # status: draft | published | completed | cancelled
    status = db.Column(db.String(20), default="published")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", backref="event", lazy=True, cascade="all, delete-orphan")
    feedback = db.relationship("Feedback", backref="event", lazy=True, cascade="all, delete-orphan")

    @property
    def seats_left(self):
        return max(self.capacity - len(self.registrations), 0)

    @property
    def attendance_count(self):
        return sum(1 for r in self.registrations if r.attendance and r.attendance.present)


class Registration(db.Model):
    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    qr_token = db.Column(db.String(64), unique=True, default=gen_uuid)
    qr_code_path = db.Column(db.String(255))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance = db.relationship("Attendance", backref="registration", uselist=False, cascade="all, delete-orphan")
    certificate = db.relationship("Certificate", backref="registration", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("user_id", "event_id", name="uq_user_event"),)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"), nullable=False)
    present = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime)
    checked_in_by = db.Column(db.Integer, db.ForeignKey("users.id"))


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comments = db.Column(db.Text)
    # Sentiment analysis output (filled in when feedback is submitted):
    # label is "positive" | "neutral" | "negative"; score is the model's confidence/compound score.
    sentiment_label = db.Column(db.String(10))
    sentiment_score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"), nullable=False)
    certificate_code = db.Column(db.String(64), unique=True, default=gen_uuid)
    file_path = db.Column(db.String(255))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
