from pathlib import Path

import streamlit as st
import torch

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)


# =========================================================
# MODEL PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

QWEN_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "Qwen3"
)


# =========================================================
# LOAD MODEL ONCE
# =========================================================

@st.cache_resource(show_spinner=False)
def load_qwen_model(
    model_path: str
):

    model_path = str(
        Path(model_path).resolve()
    )

    if not Path(model_path).exists():

        raise FileNotFoundError(
            f"Qwen model not found at: "
            f"{model_path}"
        )

    # -----------------------------------------------------
    # TOKENIZER
    # -----------------------------------------------------

    tokenizer = (
        AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True
        )
    )

    # -----------------------------------------------------
    # MODEL
    # -----------------------------------------------------

    model = (
        AutoModelForCausalLM
        .from_pretrained(
            model_path,

            torch_dtype="auto",

            device_map="auto",

            local_files_only=True
        )
    )

    model.eval()

    return tokenizer, model


# =========================================================
# LOCAL SLM
# =========================================================

class LocalSLM:

    def __init__(
        self,
        model_path=None
    ):

        if model_path is None:

            model_path = (
                QWEN_MODEL_PATH
            )

        self.model_path = str(
            Path(model_path).resolve()
        )

        (
            self.tokenizer,
            self.model
        ) = load_qwen_model(
            self.model_path
        )

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(
        self,
        messages,
        max_new_tokens=512
    ):

        # -------------------------------------------------
        # Qwen chat template
        # -------------------------------------------------

        text = (
            self.tokenizer
            .apply_chat_template(
                messages,

                tokenize=False,

                add_generation_prompt=True
            )
        )

        # -------------------------------------------------
        # Tokenize
        # -------------------------------------------------

        model_inputs = (
            self.tokenizer(
                [text],
                return_tensors="pt"
            )
        )

        model_inputs = {
            key: value.to(
                self.model.device
            )

            for key, value
            in model_inputs.items()
        }

        # -------------------------------------------------
        # Generate
        # -------------------------------------------------

        with torch.no_grad():

            generated_ids = (
                self.model.generate(

                    **model_inputs,

                    max_new_tokens=
                        max_new_tokens,

                    do_sample=False,

                    pad_token_id=(
                        self.tokenizer
                        .eos_token_id
                    )
                )
            )

        # -------------------------------------------------
        # Remove prompt
        # -------------------------------------------------

        output_ids = (
            generated_ids[0]
            [
                model_inputs[
                    "input_ids"
                ].shape[-1]:
            ]
        )

        # -------------------------------------------------
        # Decode
        # -------------------------------------------------

        response = (
            self.tokenizer.decode(
                output_ids,
                skip_special_tokens=True
            )
        )

        return response.strip()