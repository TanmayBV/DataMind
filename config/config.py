"""
config.py
---------
Centralized configuration. Every script in scripts/ should import
settings from here instead of reading environment variables directly —
keeps connection/config logic in one place as the project grows
(Day 3+ will add LLM_API_KEY, EMBEDDING_MODEL, etc. here too).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # read .env file if present

# --- Database ---
DATABASE_URL = os.environ.get("DATABASE_URL")  # set via .env or export

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")

# --- Cleaning pipeline settings ---
FUZZY_THRESHOLD = 85  # rapidfuzz score below this -> flag for manual review

# --- LLM settings (used starting Day 3) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-3.8-flash")

# --- Retrieval settings (used starting Day 4) ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
FAISS_TOP_K = 5

# --- Safety settings (used starting Day 5) ---
BLOCKED_COLUMNS = ["salary"]  # queries referencing these are always rejected


def require_database_url():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env, fill it in, "
            "and make sure your shell loads it (or `export DATABASE_URL=...`)."
        )
    return DATABASE_URL
