from datetime import datetime
import uuid

from database.database import (
    get_connection
)


def create_customer(
    customer_name=None,
    customer_segment="RETAIL",
    customer_value="STANDARD"
):

    customer_id = (
        "CUST-"
        + uuid.uuid4().hex[:8].upper()
    )

    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO customers
            (
                customer_id,
                customer_name,
                customer_segment,
                customer_value,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                customer_name,
                customer_segment,
                customer_value,
                datetime.now().isoformat()
            )
        )

        conn.commit()

    return customer_id


def get_customer(
    customer_id
):

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT
                customer_id,
                customer_name,
                customer_segment,
                customer_value,
                created_at
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()


def get_all_customers():

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT
                customer_id,
                customer_name,
                customer_segment,
                customer_value,
                created_at
            FROM customers
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_customer_call_history(
    customer_id
):

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT
                call_id,
                file_name,
                status,
                created_at
            FROM calls
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,)
        ).fetchall()