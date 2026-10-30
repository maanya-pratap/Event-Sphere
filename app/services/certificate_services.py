import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from flask import current_app


def generate_certificate(registration):
    """Render a simple landscape PDF certificate for a present attendee.

    Phase 2 note: swap this for a designed template (logo, signature,
    QR verification stamp linking to a public /verify/<code> page).
    """
    user = registration.participant
    event = registration.event

    folder = current_app.config["CERT_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename = f"certificate_{registration.qr_token}.pdf"
    filepath = os.path.join(folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    width, height = page_size

    c.setFillColor(colors.HexColor("#0E0B1F"))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    c.setStrokeColor(colors.HexColor("#7C5CFF"))
    c.setLineWidth(3)
    c.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm, stroke=True, fill=False)

    c.setFillColor(colors.HexColor("#7C5CFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 3.2 * cm, "EVENTSPHERE")

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - 5.2 * cm, "Certificate of Participation")

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 7 * cm, "This certifies that")

    c.setFillColor(colors.HexColor("#00E5A0"))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 8.3 * cm, user.name)

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 9.6 * cm, f"attended \"{event.title}\"")
    c.drawCentredString(width / 2, height - 10.6 * cm, event.start_time.strftime("%d %B %Y"))

    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#9C93C9"))
    c.drawCentredString(width / 2, 1.6 * cm, f"Verification code: {registration.qr_token}")

    c.save()
    return f"certifications/{filename}"
