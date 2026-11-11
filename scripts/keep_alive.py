"""
keep_alive.py
-------------
Sends a lightweight query (SELECT 1) to Supabase to prevent the free tier
project from pausing after 7 days of inactivity.
"""

import os
import sys

# shortcut: standalone ping script without loading app/LLM modules, upgrade if pool management needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
try:
    from config import DATABASE_URL
except Exception:
    DATABASE_URL = None

import psycopg2


def normalize_url(url: str) -> str:
    cleaned = (url or "").strip()
    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://"):]
    elif cleaned.startswith("postgresql+psycopg2://"):
        cleaned = "postgresql://" + cleaned[len("postgresql+psycopg2://"):]
    return cleaned


def ping_database(db_url: str = None) -> bool:
    target_url = normalize_url(db_url or os.environ.get("DATABASE_URL") or DATABASE_URL)
    if not target_url:
        raise ValueError("DATABASE_URL is not set.")

    with psycopg2.connect(target_url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            return result[0] == 1


if __name__ == "__main__":
    assert normalize_url("postgres://u:p@h/d") == "postgresql://u:p@h/d"
    assert normalize_url("postgresql+psycopg2://u:p@h/d") == "postgresql://u:p@h/d"
    
    url = os.environ.get("DATABASE_URL") or DATABASE_URL
    if not url:
        print("DATABASE_URL not configured. Skipped live ping.")
        sys.exit(0)

    try:
        if ping_database(url):
            print("Keep-alive ping successful: Supabase is active.")
    except Exception as e:
        print(f"Keep-alive ping failed: {e}")
        sys.exit(1)

