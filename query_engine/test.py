from pathlib import Path
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

print("Key loaded:", api_key is not None)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=api_key,
    temperature=0,
)

print("Calling Gemini...")

response = llm.invoke("Say hello in one sentence.")

print("SUCCESS")
print(response.content)