"""
config.py
---------
Centralized application configuration and environment settings.
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

# --- Canonical Domain Dictionary (Single Source of Truth) ---
# Shared synchronously between Data Cleaning and the NL2SQL Prompt
CANONICAL_CITIES = ["Moscow", "Istanbul", "New York", "London", "Berlin", "Dubai"]
CANONICAL_ROLES = [
    "Civil Engineer", "HR Analyst", "Project Manager",
    "Software Engineer", "Accountant", "Data Analyst",
]
CANONICAL_STATUSES = ["active", "terminated"]
CANONICAL_DEPARTMENTS = [
    "Human Resources", "Engineering", "Finance", "Project Management", "IT"
]
CANONICAL_PROJECTS = [
    "GPP", "Skyline Tower", "Metro Expansion", "Cloud Migration"
]

# --- LLM settings (Multi-provider: Groq / Gemini) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq" if GROQ_API_KEY else "gemini")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
LLM_MODEL = os.environ.get("LLM_MODEL", GROQ_MODEL if LLM_PROVIDER == "groq" else "gemini-3.8-flash")

# --- Retrieval settings ---
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN
    os.environ["HUGGINGFACE_HUB_TOKEN"] = HF_TOKEN
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
FAISS_TOP_K = int(os.environ.get("FAISS_TOP_K", "5"))

# --- Safety settings: Financial Data & PII Exclusion ---
BLOCKED_COLUMNS = [
    "salary", "bonus", "compensation", "wage", "premium",
    "adines_number", "national_id", "ssn"
]  # queries referencing these are always rejected


def require_database_url():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env, fill it in, "
            "and make sure your shell loads it (or `export DATABASE_URL=...`)."
        )
    return DATABASE_URL
