from config.settings import (
    AGENT_SPEAKER_INDEX,
    CUSTOMER_SPEAKER_INDEX
)


def calculate_overlap(
    start1,
    end1,
    start2,
    end2
):

    start = max(
        start1,
        start2
    )

    end = min(
        end1,
        end2
    )

    if end <= start:

        return 0.0

    return end - start


def align_segments(
    whisper_segments,
    diarization
):

    diarization_segments = []

    for turn, speaker in diarization:

        diarization_segments.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })

    results = []

    for segment in whisper_segments:

        best_speaker = "UNKNOWN"

        best_overlap = 0.0

        for speaker_segment in (
            diarization_segments
        ):

            overlap = calculate_overlap(
                segment["start"],
                segment["end"],
                speaker_segment["start"],
                speaker_segment["end"]
            )

            if overlap > best_overlap:

                best_overlap = overlap

                best_speaker = (
                    speaker_segment["speaker"]
                )

        results.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
            "speaker": best_speaker
        })

    return map_speakers(
        results
    )


def map_speakers(
    segments
):

    speakers = []

    for segment in segments:

        speaker = segment["speaker"]

        if (
            speaker != "UNKNOWN"
            and speaker not in speakers
        ):

            speakers.append(
                speaker
            )

    # -----------------------------------------------------
    # Current MVP mapping
    # -----------------------------------------------------

    agent_speaker = None

    customer_speaker = None

    if len(speakers) > AGENT_SPEAKER_INDEX:

        agent_speaker = (
            speakers[AGENT_SPEAKER_INDEX]
        )

    if len(speakers) > CUSTOMER_SPEAKER_INDEX:

        customer_speaker = (
            speakers[CUSTOMER_SPEAKER_INDEX]
        )

    # -----------------------------------------------------
    # Convert to AGENT / CUSTOMER
    # -----------------------------------------------------

    for segment in segments:

        if (
            segment["speaker"]
            == agent_speaker
        ):

            segment["speaker"] = "AGENT"

        elif (
            segment["speaker"]
            == customer_speaker
        ):

            segment["speaker"] = "CUSTOMER"

    return segments