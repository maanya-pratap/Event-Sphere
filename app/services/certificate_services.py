import math
import os
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

# Light, printable palette
PAPER = colors.HexColor("#FFFFFF")
RAYS = colors.HexColor("#F6F5FC")       # very light violet sunburst
VIOLET = colors.HexColor("#5B3FD6")     # brand accent
NAVY = colors.HexColor("#1B1F4B")       # main text
GREY = colors.HexColor("#4A4F6A")       # body text
RULE = colors.HexColor("#C9C6DE")       # thin rules


def _fit_font_size(text, font, start_size, max_width, min_size=14):
    """Shrink a line of text until it fits inside max_width (long names / titles)."""
    size = start_size
    while size > min_size and stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def _draw_sunburst(c, width, height):
    """Soft rays behind the text, clipped to the inside of the frame."""
    c.saveState()
    clip = c.beginPath()
    clip.rect(1.25 * cm, 1.25 * cm, width - 2.5 * cm, height - 2.5 * cm)
    c.clipPath(clip, stroke=0, fill=0)
    cx, cy, radius, rays = width / 2, height / 2, width, 48
    step = 2 * math.pi / rays
    c.setFillColor(RAYS)
    for i in range(0, rays, 2):
        a0, a1 = i * step, (i + 1) * step
        p = c.beginPath()
        p.moveTo(cx, cy)
        p.lineTo(cx + radius * math.cos(a0), cy + radius * math.sin(a0))
        p.lineTo(cx + radius * math.cos(a1), cy + radius * math.sin(a1))
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def draw_certificate(c, width, height, name, event_title, event_date, code):
    """Draw the certificate onto an open reportlab canvas (no Flask needed)."""
    cx = width / 2

    # paper + sunburst
    c.setFillColor(PAPER)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    _draw_sunburst(c, width, height)

    # double frame: thin navy outside, thick violet inside
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    c.rect(0.8 * cm, 0.8 * cm, width - 1.6 * cm, height - 1.6 * cm, stroke=1, fill=0)
    c.setStrokeColor(VIOLET)
    c.setLineWidth(5)
    c.rect(1.2 * cm, 1.2 * cm, width - 2.4 * cm, height - 2.4 * cm, stroke=1, fill=0)

    # brand (letter-spaced)
    c.saveState()
    c.setFillColor(VIOLET)
    brand = c.beginText()
    brand.setFont("Helvetica-Bold", 12)
    brand.setCharSpace(4)
    text = "EVENTSPHERE"
    brand.setTextOrigin(cx - stringWidth(text, "Helvetica-Bold", 12) / 2 - 2 * len(text), height - 2.9 * cm)
    brand.textOut(text)
    c.drawText(brand)
    c.restoreState()  # letter-spacing must not leak into the other lines

    # title between two thin rules
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(3.2 * cm, height - 3.5 * cm, width - 3.2 * cm, height - 3.5 * cm)
    c.line(3.2 * cm, height - 5.5 * cm, width - 3.2 * cm, height - 5.5 * cm)
    title = "CERTIFICATE OF PARTICIPATION"
    t_size = _fit_font_size(title, "Helvetica-Bold", 32, width - 8 * cm)
    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", t_size)
    c.drawCentredString(cx, height - 4.75 * cm, title)

    # "presented to"
    c.setFillColor(GREY)
    c.setFont("Helvetica", 15)
    c.drawCentredString(cx, height - 7.0 * cm, "This certificate is proudly presented to")

    # participant name (auto-shrinks for very long names)
    name_size = _fit_font_size(name, "Times-BoldItalic", 42, width - 8 * cm, min_size=20)
    c.setFillColor(NAVY)
    c.setFont("Times-BoldItalic", name_size)
    c.drawCentredString(cx, height - 8.9 * cm, name)

    c.setStrokeColor(VIOLET)
    c.setLineWidth(1.2)
    c.line(cx - 7 * cm, height - 9.4 * cm, cx + 7 * cm, height - 9.4 * cm)

    # appreciation paragraph (wraps automatically; event name and date in bold)
    style = ParagraphStyle(
        "cert-body",
        fontName="Helvetica",
        fontSize=14,
        leading=22,
        alignment=TA_CENTER,
        textColor=GREY,
    )
    body = (
        "Awarded in appreciation of your participation and commitment shown during "
        "the program, demonstrating cooperation, enthusiasm, and a positive spirit "
        "in every activity. This certifies that the participant attended "
        f"<b><font color='#1B1F4B'>{escape(event_title)}</font></b> on "
        f"<b><font color='#1B1F4B'>{escape(event_date)}</font></b>."
    )
    para = Paragraph(body, style)
    box_w = width - 10 * cm
    _, para_h = para.wrapOn(c, box_w, height)
    para.drawOn(c, (width - box_w) / 2, height - 10.3 * cm - para_h)

    # small seal
    sy = 3.6 * cm
    c.setFillColor(VIOLET)
    c.circle(cx, sy, 0.95 * cm, stroke=0, fill=1)
    c.setStrokeColor(PAPER)
    c.setLineWidth(1)
    c.circle(cx, sy, 0.78 * cm, stroke=1, fill=0)
    c.setFillColor(PAPER)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx, sy - 0.2 * cm, "ES")

    # verification code
    c.setFillColor(GREY)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(cx, 1.9 * cm, f"Verification code: {code}")


def generate_certificate(registration):
    """Render a landscape PDF certificate for a present attendee."""
    user = registration.participant
    event = registration.event

    folder = current_app.config["CERT_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename = f"certificate_{registration.qr_token}.pdf"
    filepath = os.path.join(folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    width, height = page_size

    draw_certificate(
        c, width, height,
        name=user.name,
        event_title=event.title,
        event_date=event.start_time.strftime("%d %B %Y"),
        code=registration.qr_token,
    )

    c.save()
    return f"certifications/{filename}"
