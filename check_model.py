"""Quick check: can my API key reach a Gemini model right now?

Usage:
    python check_model.py                      # tests the model in .env
    python check_model.py some-model-name      # tests a specific model
    python check_model.py --list               # lists models your key can use
"""
import os
import sys

from dotenv import load_dotenv
from google import genai

load_dotenv("travel_planner/.env")

key = os.getenv("GOOGLE_API_KEY")
if not key:
    sys.exit("GOOGLE_API_KEY not found. Check travel_planner/.env (the real .env, not .env.example).")

client = genai.Client(api_key=key)  # kept in a variable so it stays open

if "--list" in sys.argv:
    for m in client.models.list():
        print(m.name)
    sys.exit()

model = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TRAVEL_MODEL", "gemini-3.8-flash")
print(f"Testing model: {model}")
try:
    reply = client.models.generate_content(model=model, contents="Say hi in five words.")
    print("SUCCESS:", reply.text)
except Exception as exc:
    print("FAILED:", type(exc).__name__, "-", str(exc)[:300])