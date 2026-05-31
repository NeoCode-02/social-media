import io

from PIL import Image

THUMB_MAX = (480, 480)


def image_dimensions(data: bytes) -> tuple[int, int] | None:
    try:
        with Image.open(io.BytesIO(data)) as im:
            return im.width, im.height
    except Exception:
        return None


def make_thumbnail(data: bytes) -> bytes | None:
    """Return a JPEG thumbnail (<=480px) for an image, or None if not an image."""
    try:
        with Image.open(io.BytesIO(data)) as im:
            rgb = im.convert("RGB")
            rgb.thumbnail(THUMB_MAX)
            out = io.BytesIO()
            rgb.save(out, format="JPEG", quality=82)
            return out.getvalue()
    except Exception:
        return None
