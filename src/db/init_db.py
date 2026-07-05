import sqlite3
from pathlib import Path


DB_PATH = Path("data/a05_lpr.sqlite")
SCHEMA_PATH = Path("src/db/schema.sql")


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r") as schema_file:
        schema_sql = schema_file.read()

    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print("Database schema initialized successfully.")
    print(f"Database path: {DB_PATH}")
    print(f"Schema path: {SCHEMA_PATH}")


if __name__ == "__main__":
    initialize_database()