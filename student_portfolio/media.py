"""Profile-photo processing: verify it is really an image, then resize to a square JPEG."""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

import config


class PhotoError(Exception):
    pass


def process_photo(file_storage):
    data = file_storage.read(config.MAX_PHOTO_BYTES + 1)
    if not data:
        raise PhotoError("No file received")
    if len(data) > config.MAX_PHOTO_BYTES:
        raise PhotoError("Photo must be smaller than %d MB" % (config.MAX_PHOTO_BYTES // (1024 * 1024)))
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in ("JPEG", "PNG", "WEBP"):
            raise PhotoError("Use a JPG, PNG or WebP image")
        img = ImageOps.exif_transpose(img).convert("RGB")
    except PhotoError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise PhotoError("That file is not a valid image")

    size = config.PHOTO_SIZE
    img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=85, optimize=True)
    return out.getvalue()
