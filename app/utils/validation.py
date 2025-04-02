from fastapi import HTTPException
from typing import List
import base64
import re

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]

def validate_image_file(file) -> None:
    """
    Validates that the uploaded file is an image.
    Raises HTTPException if the file is not an image.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types are: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )


def validate_base64_image(data_uri: str) -> None:
    """
    Validates that the provided string is a base64-encoded image URI of an allowed type.
    Raises HTTPException if invalid.
    """
    data_uri_pattern = r"^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$"
    match = re.match(data_uri_pattern, data_uri)
    
    if not match:
        raise HTTPException(status_code=400, detail="Invalid data URI format.")

    mime_type, base64_data = match.groups()
    
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed types are: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    try:
        base64.b64decode(base64_data, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding.")