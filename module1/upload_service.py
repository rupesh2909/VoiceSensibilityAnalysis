from pathlib import Path
import shutil

from config.settings import AUDIO_DIR


def save_uploaded_file(
    uploaded_file
):

    destination = (
        AUDIO_DIR /
        uploaded_file.name
    )

    with open(
        destination,
        "wb"
    ) as output_file:

        output_file.write(
            uploaded_file.getbuffer()
        )

    return destination


def copy_sample_file(
    source_path
):

    source_path = Path(
        source_path
    )

    destination = (
        AUDIO_DIR /
        source_path.name
    )

    shutil.copy2(
        source_path,
        destination
    )

    return destination