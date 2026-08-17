from transformers import pipeline

from config.settings import (
    ROOT_CAUSE_MODEL,
    ROOT_CAUSE_CATEGORIES
)


class RootCauseService:

    def __init__(self):

        self.classifier = None

    def _load_model(self):

        if self.classifier is not None:
            return

        print("Loading local root cause model...")

        self.classifier = pipeline(
            "zero-shot-classification",
            model=str(ROOT_CAUSE_MODEL),
            tokenizer=str(ROOT_CAUSE_MODEL)
        )

        print("Local root cause model loaded.")

    def identify_root_cause(self, text):

        self._load_model()

        result = self.classifier(
            text,
            candidate_labels=ROOT_CAUSE_CATEGORIES
        )

        return {
            "category": result["labels"][0],
            "root_cause": result["labels"][0],
            "confidence": float(result["scores"][0])
        }