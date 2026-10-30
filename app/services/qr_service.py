import os
import qrcode
from flask import current_app


def generate_qr_for_registration(registration):
    """Create a QR image encoding the registration's verification token.

    The QR payload is just the qr_token string. The in-browser scanner
    (html5-qrcode) reads this text and POSTs it to the attendance
    check-in endpoint, where it's matched back to a Registration row.
    """
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "..", "qrcodes")
    os.makedirs(folder, exist_ok=True)

    filename = f"{registration.qr_token}.png"
    filepath = os.path.join(folder, filename)

    img = qrcode.make(registration.qr_token)
    img.save(filepath)

    return f"qrcodes/{filename}"


def resolve_token(token):
    """Look up a Registration by its scanned QR token."""
    from app.models import Registration
    return Registration.query.filter_by(qr_token=token).first()
