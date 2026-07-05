import sqlite3
from pathlib import Path


DB_PATH = Path("data/a05_lpr.sqlite")


def connect_db():
    """
    Connect to the SQLite database.

    If the database file does not exist yet, SQLite will create it.
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
    conn = connect_db()

    print("Connected to database successfully.")
    print(f"Database path: {DB_PATH}")

    show_existing_tables(conn)

    conn.close()


if __name__ == "__main__":
    main()