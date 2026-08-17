import sqlite3

from config.settings import DATABASE_PATH


def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database():

    schema_path = (
        DATABASE_PATH.parent.parent
        / "database"
        / "schema.sql"
    )

    with get_connection() as conn:

        with open(
            schema_path,
            "r",
            encoding="utf-8"
        ) as file:

            conn.executescript(
                file.read()
            )

        conn.commit()