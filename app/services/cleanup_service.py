"""Removing a user's files from disk.

SQLAlchemy's cascade deletes the *database rows*, but QR images and
certificate PDFs are real files on disk — the database knows nothing
about them. So we collect their paths first, delete the rows, and
only then remove the files.
"""
import os
from flask import current_app


def _qr_folder():
    # qr_service saves QR images to <UPLOAD_FOLDER>/../qrcodes
    return os.path.normpath(os.path.join(current_app.config["UPLOAD_FOLDER"], "..", "qrcodes"))


def collect_user_files(user):
    """Return absolute paths of every QR/certificate file tied to this user.

    For a participant: their own registrations.
    For an organiser: registrations on every event they own (those rows
    vanish too when the events are deleted).
    """
    registrations = list(user.registrations)
    for event in user.events:
        registrations.extend(event.registrations)

    paths = set()
    for reg in registrations:
        if reg.qr_code_path:
            paths.add(os.path.join(_qr_folder(), os.path.basename(reg.qr_code_path)))
        if reg.certificate and reg.certificate.file_path:
            paths.add(os.path.join(current_app.config["CERT_FOLDER"], os.path.basename(reg.certificate.file_path)))
    return paths


def collect_event_photo_folders(user):
    """Gallery folders for every event an organiser owns."""
    folders = set()
    for event in user.events:
        folders.add(os.path.join(current_app.config["UPLOAD_FOLDER"], "events", str(event.id)))
    return folders


def remove_files(paths, folders=()):
    removed = 0
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
        except OSError:
            pass  # a file we can't delete shouldn't block the account deletion
    for folder in folders:
        try:
            if os.path.isdir(folder):
                for name in os.listdir(folder):
                    os.remove(os.path.join(folder, name))
                os.rmdir(folder)
        except OSError:
            pass
    return removed
