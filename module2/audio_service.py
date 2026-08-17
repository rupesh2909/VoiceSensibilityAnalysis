import subprocess
from pathlib import Path

import numpy as np
import torch

from config.settings import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_FORMAT
)


def convert_to_wav(input_file):

    input_file = Path(input_file)

    output_file = (
        input_file.parent
        / f"{input_file.stem}_processed.{AUDIO_FORMAT}"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-ac",
        str(AUDIO_CHANNELS),
        "-vn",
        str(output_file)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg failed:\n\n"
            + result.stderr
        )

    return output_file


def load_audio_for_pyannote(
    audio_file
):

    """
    Load audio using FFmpeg and return
    a PyTorch waveform tensor.

    Output shape:

        [channels, samples]

    Since the audio is converted to mono,
    shape will normally be:

        [1, samples]
    """

    command = [
        "ffmpeg",
        "-i",
        str(audio_file),

        "-f",
        "f32le",

        "-acodec",
        "pcm_f32le",

        "-ar",
        str(AUDIO_SAMPLE_RATE),

        "-ac",
        str(AUDIO_CHANNELS),

        "pipe:1"
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg audio decoding failed:\n\n"
            + result.stderr.decode(
                errors="ignore"
            )
        )

    audio = np.frombuffer(
        result.stdout,
        dtype=np.float32
    )

    waveform = torch.from_numpy(
        audio.copy()
    )

    # Mono audio
    waveform = waveform.unsqueeze(0)

    return waveform