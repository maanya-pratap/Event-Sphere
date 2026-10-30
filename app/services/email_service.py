"""
Email sending and signed links for verification and password reset.

Three ways to send, chosen automatically from environment variables:
  1. BREVO_API_KEY set      -> Brevo HTTP API (works on Render's free plan,
                               which blocks normal SMTP ports).
  2. MAIL_SERVER set        -> plain SMTP (works on your own laptop, or a paid host).
  3. neither                -> "console" mode: the email is printed in the terminal
                               so you can click the link while developing.

MAIL_FROM must be an address your provider has verified (for Brevo, a verified
"sender"; for Gmail SMTP, the Gmail address itself).
"""
import hashlib
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

log = logging.getLogger(__name__)

# Every message sent in console mode is kept here (the tests read it).
outbox = []

VERIFY_SALT = "verify-email"
RESET_SALT = "reset-password"
VERIFY_MAX_AGE = 60 * 60 * 24   # 24 hours
RESET_MAX_AGE = 60 * 60         # 1 hour


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def make_token(payload, salt):
    return _serializer().dumps(payload, salt=salt)


def read_token(token, salt, max_age):
    """Return the payload, or None if the token is forged, expired or damaged."""
    try:
        return _serializer().loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def password_fingerprint(user):
    """Changes whenever the password changes, so a reset link works only once."""
    return hashlib.sha256((user.password_hash or "").encode()).hexdigest()[:16]


def _send_brevo(to, subject, body):
    payload = {
        "sender": {"name": "EventSphere", "email": os.environ["MAIL_FROM"]},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": body,
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode(),
        headers={
            "api-key": os.environ["BREVO_API_KEY"],
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return 200 <= resp.status < 300


def _send_smtp(to, subject, body):
    msg = EmailMessage()
    msg["From"] = os.environ.get("MAIL_FROM") or os.environ["MAIL_USERNAME"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    port = int(os.environ.get("MAIL_PORT", "587"))
    host = os.environ["MAIL_SERVER"]
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        server.starttls()
    with server:
        if os.environ.get("MAIL_USERNAME"):
            server.login(os.environ["MAIL_USERNAME"], os.environ.get("MAIL_PASSWORD", ""))
        server.send_message(msg)
    return True


def send_email(to, subject, body):
    """Send one plain-text email. Returns True on success, False on failure.
    Never raises, so a mail problem cannot crash registration."""
    try:
        if os.environ.get("BREVO_API_KEY") and os.environ.get("MAIL_FROM"):
            return _send_brevo(to, subject, body)
        if os.environ.get("MAIL_SERVER"):
            return _send_smtp(to, subject, body)
    except (urllib.error.URLError, smtplib.SMTPException, OSError, KeyError) as exc:
        log.error("Could not send email to %s: %s", to, exc)
        return False
    # console mode
    outbox.append({"to": to, "subject": subject, "body": body})
    print("\n" + "=" * 60 + f"\nEMAIL (console mode) to {to}\nSubject: {subject}\n\n{body}\n" + "=" * 60 + "\n")
    return True


def email_is_real():
    """True when a real provider is configured (so the UI can say 'check your inbox')."""
    return bool(os.environ.get("MAIL_SERVER") or (os.environ.get("BREVO_API_KEY") and os.environ.get("MAIL_FROM")))
