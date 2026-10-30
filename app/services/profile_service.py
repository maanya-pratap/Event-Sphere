"""Shared profile-update logic for participants and organisers."""
from app.extensions import db
from app.models import User


def update_profile(user, form, allow_email=True):
    """Apply a profile form to `user`. Returns (ok, message).

    - name/mobile (and email for participants) save directly.
    - A password change is only accepted if `current_password` matches.
    - Nothing is committed unless every check passes.
    """
    name = form.get("name", "").strip()
    if not name:
        return False, "Name can't be empty."

    new_email = form.get("email", user.email).strip().lower()
    if allow_email and new_email != user.email:
        if User.query.filter(User.email == new_email, User.id != user.id).first():
            return False, "That email is already used by another account."

    new_password = form.get("new_password", "")
    if new_password:
        if not user.check_password(form.get("current_password", "")):
            return False, "Current password is incorrect — nothing was changed."
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."

    user.name = name
    user.mobile = form.get("mobile", "").strip()
    if user.is_organiser:
        user.society_name = form.get("society_name", user.society_name or "").strip()
    if allow_email:
        user.email = new_email
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    return True, "Profile updated."
