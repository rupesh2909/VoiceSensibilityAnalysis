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
    / "ABC_Bank_male_agent_female_customer.wav"
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
    / "en_US-lessac-medium.onnx"
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
        "My name is Rahul. How may I help you today?"
    ),

    (
        "CUSTOMER",
        "I am really frustrated. "
        "I have been charged a fee on my account "
        "that I was never told about."
    ),

    (
        "AGENT",
        "I understand. Let me check the account "
        "and see what happened."
    ),

    (
        "CUSTOMER",
        "This is not the first time. "
        "I have already called twice this month "
        "about this issue and nobody has solved it."
    ),

    (
        "AGENT",
        "I am sorry you have had to call multiple times. "
        "I can remove the charge and check whether "
        "it is eligible for reversal."
    ),

    (
        "CUSTOMER",
        "Honestly, I am tired of dealing with this. "
        "If this is not fixed today, I am going to "
        "close my account and move my money to another bank."
    ),

    (
        "AGENT",
        "I understand your concern. "
        "I will escalate this to our service recovery team "
        "and check the fee reversal eligibility."
    ),

    (
        "CUSTOMER",
        "Please do not. "
        "I just want someone to take responsibility "
        "and remove it."
    ),

    (
        "AGENT",
        "Absolutely. I will create a priority case "
        "and arrange a callback from a relationship manager "
        "within two hours."
    ),

    (
        "CUSTOMER",
        "Fine. I hope this time someone actually follows up with me."
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