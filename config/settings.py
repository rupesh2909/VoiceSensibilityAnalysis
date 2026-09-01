from pathlib import Path


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

SAMPLE_FILES_DIR = DATA_DIR / "sample_files"

AUDIO_DIR = DATA_DIR / "audio"

DATABASE_DIR = DATA_DIR / "database"

DATABASE_PATH = DATABASE_DIR / "voice_sensibility.db"


# =========================================================
# FILE VALIDATION
# =========================================================

ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".mp4",
    ".aac",
    ".flac"
}

MAX_FILE_SIZE_MB = 500


# =========================================================
# AUDIO
# =========================================================

AUDIO_SAMPLE_RATE = 16000

AUDIO_CHANNELS = 1

AUDIO_FORMAT = "wav"


# =========================================================
# WHISPER
# =========================================================

WHISPER_MODEL = "base"

WHISPER_FP16 = False


# =========================================================
# DIARIZATION
# =========================================================

DIARIZATION_MODEL = (
    "pyannote/speaker-diarization-community-1"
)

MIN_SPEAKERS = 2

MAX_SPEAKERS = 2


# =========================================================
# SPEAKER MAPPING
# =========================================================
#
# For the current MVP we assume the first detected
# speaker is AGENT and the second is CUSTOMER.
#
# This can later be replaced with a more sophisticated
# speaker-identification mechanism.
# =========================================================

AGENT_SPEAKER_INDEX = 0

CUSTOMER_SPEAKER_INDEX = 1


# =========================================================
# SENTIMENT
# =========================================================

SENTIMENT_MODEL = (
    "cardiffnlp/twitter-roberta-base-sentiment-latest"
)

MAX_SENTIMENT_TEXT_LENGTH = 4000

# =========================================================
# EMOTION
# =========================================================

EMOTION_MODEL = (
    "SamLowe/roberta-base-go_emotions"
)

MAX_EMOTION_TEXT_LENGTH = 4000

EMOTION_CONFIDENCE_THRESHOLD = 0.20


# =========================================================
# EMOTION MAPPING
# =========================================================
#
# GoEmotions contains "annoyance", which we map to the
# business category FRUSTRATION.
#
# It also contains "disappointment", "confusion",
# "anger", etc.
# =========================================================

EMOTION_LABEL_MAPPING = {

    "anger":
        "ANGER",

    "annoyance":
        "FRUSTRATION",

    "disappointment":
        "DISAPPOINTMENT",

    "confusion":
        "CONFUSION",

    "fear":
        "FEAR",

    "sadness":
        "SADNESS",

    "neutral":
        "NEUTRAL",

    "joy":
        "JOY",

    "surprise":
        "SURPRISE"
}


# =========================================================
# APPLICATION
# =========================================================

APP_TITLE = "Voice Sensibility Analysis"

APP_ICON = "🎧"

PAGE_LAYOUT = "wide"


# =========================================================
# DATABASE STATUS
# =========================================================

STATUS_UPLOADED = "UPLOADED"

STATUS_TRANSCRIBING = "TRANSCRIBING"

STATUS_DIARIZING = "DIARIZING"

STATUS_COMPLETED = "COMPLETED"

STATUS_ANALYZED = "ANALYZED"

STATUS_FAILED = "FAILED"


# =========================================================
# CREATE REQUIRED DIRECTORIES
# =========================================================

SAMPLE_FILES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

AUDIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ROOT_CAUSE_MODEL = (
    BASE_DIR
    / "models"
    / "root_cause"
)

ROOT_CAUSE_CATEGORIES = [

    "Fees / Charges",
    "Fraud / Unauthorized Transaction",
    "Mobile Banking",
    "Internet Banking",
    "Login / Authentication",
    "Loan Processing",
    "Account Opening",
    "Card Issue",
    "Service Delay",
    "Product Features",
    "Pricing / Interest Rate",
    "Poor Customer Service",
    "Other"
]

ROOT_CAUSE_CONFIDENCE_THRESHOLD = 0.40

# =========================================================
# RETENTION RULE THRESHOLDS
# =========================================================

RETENTION_SENTIMENT_THRESHOLD = 0.70

RETENTION_ANGER_THRESHOLD = 0.70

CUSTOMER_VALUE_OPTIONS = [
    "GOLD",
    "PLATINUM",
    "HIGH AUM"
]

HIGH_VALUE_CUSTOMER_VALUES = {
    "HIGH AUM",
    "PLATINUM",
}