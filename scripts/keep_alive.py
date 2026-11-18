
"""
keep_alive.py
-------------
Sends a lightweight database metadata query to Supabase.
"""

import os
import sys
import psycopg2


def normalize_url(url: str) -> str:
    cleaned = (url or "").strip()

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://"):]

    elif cleaned.startswith("postgresql+psycopg2://"):
        cleaned = "postgresql://" + cleaned[len("postgresql+psycopg2://"):]

    return cleaned


def ping_database(db_url: str) -> bool:
    target_url = normalize_url(db_url)

    if not target_url:
        raise ValueError("DATABASE_URL is not set.")

    with psycopg2.connect(target_url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE';
            """)

            result = cur.fetchone()

            print(f"Supabase database reachable.")
            print(f"Public tables found: {result[0]}")

            return True


if __name__ == "__main__":
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL is not configured.")
        sys.exit(1)

    try:
        if ping_database(database_url):
            print("Keep-alive ping successful!")

    except Exception as e:
        print(f"Keep-alive ping failed: {e}")
        sys.exit(1)
