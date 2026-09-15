from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai

# Project root: D:\nl2sql-rag-project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

print("API key loaded:", api_key is not None)

if api_key:
    print("API key starts with:", api_key[:8])
    print("API key length:", len(api_key))

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Say hello in one sentence."
)

print(response.text)
