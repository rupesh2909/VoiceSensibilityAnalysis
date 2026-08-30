import sys
from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.database import get_connection


def clear_database():

    with get_connection() as conn:

        conn.execute("PRAGMA foreign_keys = OFF")

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        for row in tables:

            table_name = row["name"]

            print(
                f"Clearing table: {table_name}"
            )

            conn.execute(
                f'DELETE FROM "{table_name}"'
            )

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        conn.commit()


if __name__ == "__main__":

    print("=" * 50)
    print("Voice Sensibility Analysis")
    print("Database Reset")
    print("=" * 50)

    answer = input(
        "Are you sure you want to clear the database? "
        "[yes/no]: "
    ).strip().lower()

    if answer != "yes":

        print("Database reset cancelled.")

    else:

        clear_database()

        print("=" * 50)
        print("✓ Database cleared successfully.")
        print("=" * 50)
