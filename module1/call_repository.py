from datetime import datetime
import uuid

from database.database import (
    get_connection
)

from config.settings import (
    STATUS_UPLOADED,
    STATUS_FAILED
)


def create_call(
    file_name,
    file_path,
    file_size,
    source
):

    call_id = (
        "CALL-"
        + datetime.now().strftime("%Y%m%d")
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )

    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO calls
            (
                call_id,
                file_name,
                file_path,
                file_size,
                source,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                file_name,
                str(file_path),
                file_size,
                source,
                STATUS_UPLOADED,
                datetime.now().isoformat()
            )
        )

        conn.commit()

    return call_id


def update_status(
    call_id,
    status
):

    with get_connection() as conn:

        conn.execute(
            """
            UPDATE calls
            SET status = ?
            WHERE call_id = ?
            """,
            (
                status,
                call_id
            )
        )

        conn.commit()


def get_all_calls():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                call_id,
                file_name,
                file_path,
                file_size,
                source,
                status,
                created_at
            FROM calls
            ORDER BY created_at
            """
        ).fetchall()

    return rows


def get_call(
    call_id
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                call_id,
                file_name,
                file_path,
                file_size,
                source,
                status,
                created_at
            FROM calls
            WHERE call_id = ?
            """,
            (call_id,)
        ).fetchone()

    return row


def get_call_by_file_name(
    file_name
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                call_id,
                file_name,
                file_path,
                file_size,
                source,
                status,
                created_at
            FROM calls
            WHERE file_name = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (file_name,)
        ).fetchone()

    return row