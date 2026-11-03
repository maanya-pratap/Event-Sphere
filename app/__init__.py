import os
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from config import Config
from app.extensions import db, login_manager, migrate

load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Behind Render's proxy, trust the forwarded https/host so emailed links are https://...
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    os.makedirs(app.config["CERT_FOLDER"], exist_ok=True)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.organiser import organiser_bp
    from app.routes.participant import participant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(organiser_bp, url_prefix="/organiser")
    app.register_blueprint(participant_bp, url_prefix="/participant")

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()
        _ensure_user_columns()
        _ensure_admin()

    return app

def _ensure_user_columns():
    """db.create_all() never adds columns to a table that already exists (like the live
    Render database), so add the login-lock columns ourselves if they are missing."""
    from sqlalchemy import inspect, text

    existing = {c["name"] for c in inspect(db.engine).get_columns("users")}
    with db.engine.begin() as conn:
        if "failed_attempts" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0"))
        if "locked_until" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP"))
            

def _ensure_admin():
    """On a fresh online database there is no shell to run seed.py. If ADMIN_EMAIL and
    ADMIN_PASSWORD are set, make sure that admin account exists (created once, never reset)."""
    from app.models import User

    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not password:
        return
    if User.query.filter_by(email=email).first() is None:
        admin = User(name="Admin", email=email, role="admin", is_approved=True, email_verified=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
