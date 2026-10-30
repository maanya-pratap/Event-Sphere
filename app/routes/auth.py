from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User
from app.services import email_service as mail

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


def _redirect_for_role(user):
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if user.role == "organiser":
        return redirect(url_for("organiser.dashboard"))
    return redirect(url_for("participant.dashboard"))


def _send_verification(user):
    token = mail.make_token({"email": user.email}, mail.VERIFY_SALT)
    link = url_for("auth.verify_email", token=token, _external=True)
    body = (
        f"Hi {user.name.split(' ')[0]},\n\n"
        "Welcome to EventSphere! Please confirm your email address by opening this link "
        "(valid for 24 hours):\n\n"
        f"{link}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    return mail.send_email(user.email, "Verify your EventSphere email", body)


def _send_reset(user):
    token = mail.make_token(
        {"id": user.id, "fp": mail.password_fingerprint(user)}, mail.RESET_SALT
    )
    link = url_for("auth.reset_password", token=token, _external=True)
    body = (
        f"Hi {user.name.split(' ')[0]},\n\n"
        "We received a request to reset your EventSphere password. Open this link to choose "
        "a new one (valid for 1 hour, works once):\n\n"
        f"{link}\n\n"
        "If you did not ask for this, ignore this email; your password stays the same."
    )
    return mail.send_email(user.email, "Reset your EventSphere password", body)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        account_type = request.form.get("account_type", "participant")
        society_name = request.form.get("society_name", "").strip()

        if not name or not email or not password:
            flash("Please fill in every field.", "error")
        elif password != confirm:
            flash("Passwords don't match.", "error")
        elif len(password) < 6:
            flash("Password should be at least 6 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(
                name=name,
                email=email,
                mobile=mobile,
                role="organiser" if account_type == "organiser" else "participant",
                society_name=society_name if account_type == "organiser" else None,
                is_approved=(account_type != "organiser"),
                email_verified=False,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            sent = _send_verification(user)
            if sent:
                flash(f"Account created! We sent a verification link to {email}. "
                      "Open it, then log in.", "success")
            else:
                flash("Account created, but we could not send the verification email. "
                      "Use 'Resend verification email' on the login page.", "info")
            if account_type == "organiser":
                flash("Your society account will also need admin approval.", "info")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("That email/password combination doesn't match.", "error")
        elif not user.email_verified:
            flash("Please verify your email first. Check your inbox for the link.", "info")
            return render_template("auth/login.html", unverified_email=email)
        elif user.role == "organiser" and not user.is_approved:
            flash("Your society account is awaiting admin approval.", "info")
        else:
            login_user(user, remember=remember)
            flash(f"Good to see you, {user.name.split(' ')[0]}.", "success")
            return _redirect_for_role(user)

    return render_template("auth/login.html")


@auth_bp.route("/verify/<token>")
def verify_email(token):
    data = mail.read_token(token, mail.VERIFY_SALT, mail.VERIFY_MAX_AGE)
    user = User.query.filter_by(email=data["email"]).first() if data else None
    if user is None:
        flash("That verification link is invalid or has expired. Request a new one below.", "error")
        return redirect(url_for("auth.login"))
    if user.email_verified:
        flash("Your email is already verified. Please log in.", "info")
    else:
        user.email_verified = True
        db.session.commit()
        flash("Email verified! You can log in now.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        _send_verification(user)
    # Same message either way, so nobody can use this form to find out who has an account.
    flash("If that email has an unverified account, we sent a new verification link.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            _send_reset(user)
        flash("If that email has an account, we sent a password reset link.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    data = mail.read_token(token, mail.RESET_SALT, mail.RESET_MAX_AGE)
    user = db.session.get(User, data["id"]) if data else None
    if user is None or data.get("fp") != mail.password_fingerprint(user):
        flash("That reset link is invalid, expired or already used. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 6:
            flash("Password should be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords don't match.", "error")
        else:
            user.set_password(password)
            user.email_verified = True  # they proved they own the inbox
            db.session.commit()
            flash("Password changed. Please log in with the new password.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.landing"))
