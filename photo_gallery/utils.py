import os
import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def compress_image(uploaded_file, quality=70, max_dimension=1920):
    """
    Compresses an uploaded image file:
    - Resizes if larger than max_dimension (keeps aspect ratio)
    - Re-encodes as JPEG at the given quality
    Returns a new InMemoryUploadedFile ready to assign to an ImageField.
    Falls back to the original file if compression fails for any reason.
    """
    try:
        img = Image.open(uploaded_file)

        # Convert to RGB (handles PNG/RGBA/CMYK etc. before saving as JPEG)
        if img.mode in ("RGBA", "P", "CMYK"):
            img = img.convert("RGB")

        # Resize if too large
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Build a new filename (force .jpg since we re-encoded as JPEG)
        original_name = os.path.splitext(uploaded_file.name)[0]
        new_name = f"{original_name}.jpg"

        return InMemoryUploadedFile(
            buffer,
            "ImageField",
            new_name,
            "image/jpeg",
            buffer.getbuffer().nbytes,
            None
        )
    except Exception:
        uploaded_file.seek(0)
        return uploaded_file
