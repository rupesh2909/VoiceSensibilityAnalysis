from config.settings import (
    AGENT_SPEAKER_INDEX,
    CUSTOMER_SPEAKER_INDEX
)


# =========================================================
# OVERLAP
# =========================================================

def calculate_overlap(
    start1,
    end1,
    start2,
    end2
):

    overlap_start = max(
        start1,
        start2
    )

    overlap_end = min(
        end1,
        end2
    )

    return max(
        0.0,
        overlap_end - overlap_start
    )


# =========================================================
# ALIGN
# =========================================================

def align_segments(
    whisper_segments,
    diarization_segments
):
    """
    Align Whisper timestamped segments with
    diarization speaker segments.

    Parameters
    ----------
    whisper_segments:
        [
            {
                "start": float,
                "end": float,
                "text": str
            }
        ]

    diarization_segments:
        [
            {
                "start": float,
                "end": float,
                "speaker": str
            }
        ]
    """

    results = []

    for segment in whisper_segments:

        whisper_start = float(
            segment["start"]
        )

        whisper_end = float(
            segment["end"]
        )

        best_speaker = "UNKNOWN"

        best_overlap = 0.0

        # -------------------------------------------------
        # Find speaker with maximum temporal overlap
        # -------------------------------------------------

        for speaker_segment in (
            diarization_segments
        ):

            overlap = calculate_overlap(

                whisper_start,

                whisper_end,

                float(
                    speaker_segment["start"]
                ),

                float(
                    speaker_segment["end"]
                )
            )

            if overlap > best_overlap:

                best_overlap = (
                    overlap
                )

                best_speaker = (
                    speaker_segment[
                        "speaker"
                    ]
                )

        results.append({

            "start":
                whisper_start,

            "end":
                whisper_end,

            "text":
                str(
                    segment.get(
                        "text",
                        ""
                    )
                ).strip(),

            "speaker":
                best_speaker
        })

    return map_speakers(
        results
    )


# =========================================================
# MAP SPEAKERS
# =========================================================

def map_speakers(
    segments
):
    """
    Convert pyannote speaker labels to:

        AGENT
        CUSTOMER

    Current MVP assumption:
        first detected speaker = AGENT
        second detected speaker = CUSTOMER
    """

    speakers = []

    for segment in segments:

        speaker = (
            segment.get(
                "speaker"
            )
        )

        if (
            speaker
            and speaker != "UNKNOWN"
            and speaker not in speakers
        ):

            speakers.append(
                speaker
            )

    agent_speaker = None

    customer_speaker = None

    if (
        len(speakers)
        > AGENT_SPEAKER_INDEX
    ):

        agent_speaker = (
            speakers[
                AGENT_SPEAKER_INDEX
            ]
        )

    if (
        len(speakers)
        > CUSTOMER_SPEAKER_INDEX
    ):

        customer_speaker = (
            speakers[
                CUSTOMER_SPEAKER_INDEX
            ]
        )

    # -----------------------------------------------------
    # Apply mapping
    # -----------------------------------------------------

    for segment in segments:

        speaker = (
            segment.get(
                "speaker"
            )
        )

        if speaker == agent_speaker:

            segment["speaker"] = (
                "AGENT"
            )

        elif speaker == customer_speaker:

            segment["speaker"] = (
                "CUSTOMER"
            )

    return segments