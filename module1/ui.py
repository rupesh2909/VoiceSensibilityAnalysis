from .customer_repository import (
    create_customer
)

import streamlit as st

from config.settings import (
    SAMPLE_FILES_DIR
)

from .validation_service import (
    validate_file
)

from .upload_service import (
    save_uploaded_file,
    copy_sample_file
)

from .call_repository import (
    create_call
)


def get_sample_files():

    if not SAMPLE_FILES_DIR.exists():

        return []

    return [
        file
        for file in SAMPLE_FILES_DIR.iterdir()
        if file.is_file()
    ]


def run_module1():

    st.subheader(
        "Module 1 — File Upload & Validation"
    )

    # =====================================================
    # CUSTOMER INFORMATION
    # =====================================================

    st.markdown(
        "### Customer Information"
    )

    customer_name = st.text_input(
        "Customer Name",
        value="Demo Customer"
    )

    customer_segment = st.selectbox(
        "Customer Segment",
        [
            "RETAIL",
            "HNI",
            "WEALTH",
            "CORPORATE"
        ]
    )

    customer_value = st.selectbox(
        "Customer Value",
        [
            "STANDARD",
            "GOLD",
            "PLATINUM",
            "HIGH_AUM"
        ]
    )    

    # =====================================================
    # SAMPLE FILES
    # =====================================================

    sample_files = get_sample_files()

    sample_names = [
        file.name
        for file in sample_files
    ]

    selected_samples = st.multiselect(
        "Select sample audio files",
        sample_names
    )

    # =====================================================
    # UPLOAD FILES
    # =====================================================

    uploaded_files = st.file_uploader(
        "Or upload audio file(s)",
        type=[
            "mp3",
            "wav",
            "m4a",
            "mp4",
            "aac",
            "flac"
        ],
        accept_multiple_files=True
    )

    # =====================================================
    # PROCESS
    # =====================================================

    if not st.button(
        "▶ Upload / Validate Files",
        type="primary"
    ):

        return []

    files = []

    # -----------------------------------------------------
    # Selected sample files
    # -----------------------------------------------------

    for file_name in selected_samples:

        path = (
            SAMPLE_FILES_DIR /
            file_name
        )

        files.append({
            "name": file_name,
            "source": "SAMPLE",
            "path": path,
            "size": path.stat().st_size
        })

    # -----------------------------------------------------
    # Uploaded files
    # -----------------------------------------------------

    for file in uploaded_files or []:

        files.append({
            "name": file.name,
            "source": "UPLOAD",
            "file": file,
            "size": file.size
        })

    if not files:

        st.warning(
            "Please select or upload "
            "at least one audio file."
        )

        return []

    # =====================================================
    # CUSTOMER
    # =====================================================

    try:

        customer_id = create_customer(
            customer_name=customer_name,
            customer_segment=customer_segment,
            customer_value=customer_value
        )

        st.info(
            f"Customer created: {customer_id}"
        )

    except Exception as e:

        st.error(
            f"Unable to create customer: {e}"
        )

        return []

    successful_files = []

    # =====================================================
    # PROCESS EACH FILE
    # =====================================================

    for item in files:

        file_name = item["name"]

        with st.status(
            f"Processing {file_name}",
            expanded=True
        ) as status:

            # ---------------------------------------------
            # Validation
            # ---------------------------------------------

            st.write(
                "🔍 Validating file..."
            )

            valid, message = validate_file(
                file_name,
                item["size"]
            )

            if not valid:

                st.error(
                    message
                )

                status.update(
                    label=f"Failed: {file_name}",
                    state="error"
                )

                continue

            st.write(
                "✓ Validation completed"
            )

            # ---------------------------------------------
            # Copy/upload
            # ---------------------------------------------

            st.write(
                "⬆️ Saving file to server..."
            )

            try:

                if item["source"] == "SAMPLE":

                    audio_path = (
                        copy_sample_file(
                            item["path"]
                        )
                    )

                else:

                    audio_path = (
                        save_uploaded_file(
                            item["file"]
                        )
                    )

                st.write(
                    "✓ File saved to data/audio"
                )

                # -----------------------------------------
                # Database
                # -----------------------------------------

                st.write(
                    "💾 Creating database entry..."
                )

                call_id = create_call(
                    file_name=file_name,
                    file_path=audio_path,
                    file_size=item["size"],
                    source=item["source"],
                    customer_id=customer_id
                )

                st.write(
                    f"✓ Database entry created "
                    f"({call_id})"
                )

                successful_files.append({
                    "call_id": call_id,
                    "file_name": file_name,
                    "file_path": audio_path
                })

                status.update(
                    label=f"Completed: {file_name}",
                    state="complete"
                )

            except Exception as e:

                st.error(
                    str(e)
                )

                status.update(
                    label=f"Failed: {file_name}",
                    state="error"
                )

    # =====================================================
    # SUMMARY
    # =====================================================

    if successful_files:

        st.success(
            f"{len(successful_files)} "
            f"file(s) uploaded successfully."
        )

    return successful_files