import shutil

import streamlit as st

from database.database import get_connection
from config.settings import AUDIO_DIR


def clear_database():

    with get_connection() as conn:

        # Get all user tables
        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        # Disable foreign key checking temporarily
        conn.execute(
            "PRAGMA foreign_keys = OFF"
        )

        for table in tables:

            table_name = table["name"]

            conn.execute(
                f'DELETE FROM "{table_name}"'
            )

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        conn.commit()


def clear_audio_files():

    if not AUDIO_DIR.exists():

        return 0

    deleted_count = 0

    for file_path in AUDIO_DIR.iterdir():

        if file_path.is_file():

            file_path.unlink()

            deleted_count += 1

        elif file_path.is_dir():

            shutil.rmtree(
                file_path
            )

    return deleted_count


def reset_application():

    clear_database()

    deleted_files = (
        clear_audio_files()
    )

    return deleted_files


def render_reset_database():

    st.sidebar.divider()

    st.sidebar.subheader(
        "Development Tools"
    )

    st.sidebar.caption(
        "Temporary development option"
    )

    if st.sidebar.button(
        "🗑️ Clear Database & Uploaded Files",
        type="secondary"
    ):

        st.session_state[
            "confirm_database_reset"
        ] = True

    # -----------------------------------------------------
    # Confirmation
    # -----------------------------------------------------

    if st.session_state.get(
        "confirm_database_reset",
        False
    ):

        st.sidebar.warning(
            "This will delete all database "
            "records and all uploaded files "
            "from data/audio/."
        )

        st.sidebar.caption(
            "Files in data/sample_files/ "
            "will NOT be deleted."
        )

        col1, col2 = st.sidebar.columns(2)

        with col1:

            if st.button(
                "Yes, Clear",
                key="confirm_reset"
            ):

                try:

                    deleted_files = (
                        reset_application()
                    )

                    st.session_state[
                        "confirm_database_reset"
                    ] = False

                    st.sidebar.success(
                        f"Database cleared. "
                        f"{deleted_files} uploaded "
                        f"file(s) deleted."
                    )

                    st.rerun()

                except Exception as e:

                    st.sidebar.error(
                        f"Reset failed: {e}"
                    )

        with col2:

            if st.button(
                "Cancel",
                key="cancel_reset"
            ):

                st.session_state[
                    "confirm_database_reset"
                ] = False

                st.rerun()