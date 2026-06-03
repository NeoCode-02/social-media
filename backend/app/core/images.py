import io

from PIL import Image, ImageOps

THUMB_MAX = (480, 480)


def image_dimensions(data: bytes) -> tuple[int, int] | None:
    try:
        with Image.open(io.BytesIO(data)) as im_file:
            # EXIF orientation must be applied for accurate width/height —
            # untransposed portraits report landscape dimensions in the header.
            im: Image.Image = ImageOps.exif_transpose(im_file) or im_file
            return im.width, im.height
    except Exception:
        return None


def make_thumbnail(data: bytes) -> bytes | None:
    """Return a JPEG thumbnail (<=480px) for an image, or None if not an image."""
    try:
        with Image.open(io.BytesIO(data)) as im_file:
            im: Image.Image = ImageOps.exif_transpose(im_file) or im_file
            rgb = im.convert("RGB")
            rgb.thumbnail(THUMB_MAX)
            out = io.BytesIO()
            rgb.save(out, format="JPEG", quality=82)
            return out.getvalue()
    except Exception:
        return None

MAX_IMAGE_DIMENSIONS = (1920, 1080)

def compress_image(data: bytes, original_mime: str) -> tuple[bytes, str]:
    """Compress image, resize if too large, and convert to WEBP for storage savings."""
    try:
        with Image.open(io.BytesIO(data)) as im_file:
            if im_file.format == "GIF":
                # Do not compress animated gifs
                return data, original_mime

            im: Image.Image = ImageOps.exif_transpose(im_file) or im_file
            rgb = im.convert("RGB")
            rgb.thumbnail(MAX_IMAGE_DIMENSIONS)
            out = io.BytesIO()
            rgb.save(out, format="WEBP", quality=85)
            return out.getvalue(), "image/webp"
    except Exception:
        return data, original_mime
