"""Self-hosted image captcha (no Google account or API key needed).

The correct answer is never put in the page. It is stored in the user's session as a
salted hash, and it can be used only once.
"""
import hashlib
import io
import random

from flask import current_app, session
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# No 0/O, 1/I/l so people are not tricked by look-alike characters
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LENGTH = 5
SESSION_KEY = "captcha_hash"

_FONT_FILES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "Arial Bold.ttf",
    "arialbd.ttf",
]


def _font(size):
    for path in _FONT_FILES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)   # Pillow >= 10.1 can scale its built-in font
    except TypeError:
        return ImageFont.load_default()


def make_hash(code):
    salt = current_app.config["SECRET_KEY"]
    return hashlib.sha256(f"{salt}:{code.upper()}".encode()).hexdigest()


def new_captcha_png():
    """Create a fresh code, remember its hash in the session, return the PNG bytes."""
    code = "".join(random.choice(ALPHABET) for _ in range(LENGTH))
    session[SESSION_KEY] = make_hash(code)

    width, height = 190, 64
    img = Image.new("RGB", (width, height), (251, 244, 230))
    draw = ImageDraw.Draw(img)

    for _ in range(7):  # background noise lines
        colour = tuple(random.randint(150, 215) for _ in range(3))
        draw.line(
            [(random.randint(0, width), random.randint(0, height)),
             (random.randint(0, width), random.randint(0, height))],
            fill=colour, width=random.randint(1, 3),
        )

    font = _font(38)
    x = 12
    for ch in code:
        tile = Image.new("RGBA", (44, 56), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text(
            (6, 4), ch, font=font,
            fill=(random.randint(10, 70), random.randint(10, 60), random.randint(60, 150), 255),
        )
        tile = tile.rotate(random.randint(-22, 22), resample=Image.BICUBIC, expand=True)
        img.paste(tile, (x, random.randint(0, 8)), tile)
        x += 33

    for _ in range(90):  # speckles
        draw.point((random.randint(0, width - 1), random.randint(0, height - 1)),
                   fill=(random.randint(60, 160),) * 3)
    img = img.filter(ImageFilter.SMOOTH_MORE)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def check_captcha(answer):
    """True only if the typed text matches. The stored answer is used up either way."""
    expected = session.pop(SESSION_KEY, None)
    if not expected or not answer:
        return False
    return make_hash(answer.strip()) == expected
