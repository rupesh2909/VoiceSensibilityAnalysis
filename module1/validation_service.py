from pathlib import Path

from config.settings import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_FILE_SIZE_MB
)


def validate_file(
    file_name,
    file_size
):

    extension = Path(
        file_name
    ).suffix.lower()

    # -----------------------------------------------------
    # Extension
    # -----------------------------------------------------

    if extension not in ALLOWED_AUDIO_EXTENSIONS:

        return (
            False,
            f"Unsupported file type: {extension}"
        )

    # -----------------------------------------------------
    # File size
    # -----------------------------------------------------

    max_size = (
        MAX_FILE_SIZE_MB
        * 1024
        * 1024
    )

    if file_size > max_size:

        return (
            False,
            f"File size exceeds "
            f"{MAX_FILE_SIZE_MB} MB"
        )

    return True, "Valid"