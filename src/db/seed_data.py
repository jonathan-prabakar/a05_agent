import random
import sqlite3
from pathlib import Path

from seed_helpers import clear_existing_data
from demo_patients import seed_demo_patients
from random_patients import seed_random_patients


DB_PATH = Path("data/a05_lpr.sqlite")


def connect_db():
    """
    Connect to the SQLite database.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def show_existing_tables(conn):
    """
    Print all tables currently inside the SQLite database.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
        """
    )

    tables = cursor.fetchall()

    print("Existing tables:")

    if not tables:
        print("No tables found.")
        return

    for table in tables:
        print(f"- {table[0]}")


def main():
    random.seed(42)

    conn = connect_db()

    print("Connected to database successfully.")
    print(f"Database path: {DB_PATH}")

    show_existing_tables(conn)

    clear_existing_data(conn)
    seed_demo_patients(conn)
    seed_random_patients(conn, count=95)

    conn.commit()
    conn.close()

    print("Seed data completed successfully.")
    print("Total expected patients: 100")


if __name__ == "__main__":
    main()