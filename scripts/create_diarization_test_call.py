from pathlib import Path
import subprocess
import wave

from piper import PiperVoice


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_DIR = PROJECT_ROOT / "models" / "tts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "sample_files"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "Positive_customer.wav"
)


# =========================================================
# VOICE MODELS
# =========================================================
#
# Download two different Piper English voices into:
#
# models/tts/
#
# Example:
#
# en_US-lessac-medium.onnx
# en_US-amy-medium.onnx
#
# Lessac = Agent
# Amy    = Customer
#
# =========================================================

AGENT_MODEL = (
    MODEL_DIR
    / "en_US-ryan-medium.onnx"
)

CUSTOMER_MODEL = (
    MODEL_DIR
    / "en_US-amy-medium.onnx"
)


# =========================================================
# DIALOGUE
# =========================================================

DIALOGUE = [

    (
        "AGENT",
        "Thank you for calling ABC Bank. "
        "My name is David. How may I help you today?"
    ),

    (
        "CUSTOMER",
        "Hi David. I would like to know if I can increase the limit on my credit card"
    ),

    (
        "AGENT",
        "Certainly, I can explain the process"
        "We can submit a credit limit after checking your eligibility"
    ),

    (
        "CUSTOMER",
        "What document do I need?"
    ),

    (
        "AGENT",
        "We need your recent income document."
    ),

    (
        "CUSTOMER",
        "That sounds easy "
        "Can I submit it today "
    ),

    (
        "AGENT",
        "Yes, I can explain the steps and if you face any difficulty, our support team can assist you"
    ),

    (
        "CUSTOMER",
        "Perfect. Thank you for explaining everything so clearly"
    ),

    (
        "AGENT",
        "You are very welcome. Is there anything else I can help you with?"
    ),

    (
        "CUSTOMER",
        "No, not at all. Thanks for your help. Have a great day."
    ),

    (
        "AGENT",
        "You too. Thank you for banking with ABC Bank."
    ),    
]


# =========================================================
# VALIDATE MODELS
# =========================================================

if not AGENT_MODEL.exists():

    raise FileNotFoundError(
        f"Agent voice model not found:\n{AGENT_MODEL}"
    )

if not CUSTOMER_MODEL.exists():

    raise FileNotFoundError(
        f"Customer voice model not found:\n{CUSTOMER_MODEL}"
    )


# =========================================================
# LOAD VOICES
# =========================================================

print("Loading Agent voice...")

agent_voice = PiperVoice.load(
    str(AGENT_MODEL)
)

print("Loading Customer voice...")

customer_voice = PiperVoice.load(
    str(CUSTOMER_MODEL)
)


# =========================================================
# TEMP DIRECTORY
# =========================================================

TEMP_DIR = (
    OUTPUT_DIR
    / "_tts_test"
)

TEMP_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# GENERATE EACH TURN
# =========================================================

segments = []

for index, (speaker, text) in enumerate(DIALOGUE):

    print(
        f"Generating {index + 1}/{len(DIALOGUE)} "
        f"{speaker}..."
    )

    voice = (
        agent_voice
        if speaker == "AGENT"
        else customer_voice
    )

    output_path = (
        TEMP_DIR
        / f"{index:02d}_{speaker}.wav"
    )

    with wave.open(
        str(output_path),
        "wb"
    ) as wav_file:

        voice.synthesize_wav(
            text,
            wav_file
        )

    segments.append(
        output_path
    )


# =========================================================
# COMBINE TURNS
# =========================================================

import wave

print("Combining dialogue...")

with wave.open(
    str(OUTPUT_FILE),
    "wb"
) as output_wav:

    first_segment = True

    for segment_path in segments:

        with wave.open(
            str(segment_path),
            "rb"
        ) as input_wav:

            if first_segment:

                output_wav.setnchannels(
                    input_wav.getnchannels()
                )

                output_wav.setsampwidth(
                    input_wav.getsampwidth()
                )

                output_wav.setframerate(
                    input_wav.getframerate()
                )

                first_segment = False

            else:

                # Make sure every Piper segment has
                # identical audio parameters.
                if (
                    input_wav.getnchannels()
                    != output_wav.getnchannels()
                    or
                    input_wav.getsampwidth()
                    != output_wav.getsampwidth()
                    or
                    input_wav.getframerate()
                    != output_wav.getframerate()
                ):

                    raise RuntimeError(
                        "Inconsistent audio format "
                        f"in {segment_path}"
                    )

            output_wav.writeframes(
                input_wav.readframes(
                    input_wav.getnframes()
                )
            )

            # -------------------------------------------------
            # 650 ms silence between speakers
            # -------------------------------------------------

            silence_samples = int(
                input_wav.getframerate() * 0.650
            )

            silence_bytes = (
                b"\x00"
                * silence_samples
                * input_wav.getnchannels()
                * input_wav.getsampwidth()
            )

            output_wav.writeframes(
                silence_bytes
            )


# =========================================================
# CLEANUP
# =========================================================

for segment in segments:

    segment.unlink(
        missing_ok=True
    )

try:

    TEMP_DIR.rmdir()

except OSError:

    pass


# =========================================================
# RESULT
# =========================================================

print()
print("=" * 70)
print("CALL CREATED")
print("=" * 70)

print(
    f"File: {OUTPUT_FILE}"
)

print(
    "Format: WAV / PCM 16-bit / mono / 16 kHz"
)

print(
    "Agent: Lessac voice"
)

print(
    "Customer: Amy voice"
)

print("=" * 70)