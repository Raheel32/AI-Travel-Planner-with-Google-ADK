"""Central settings, read from environment variables (.env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.models import Gemini
from google.genai import types

load_dotenv()  # finds travel_planner/.env automatically

# The model every agent uses. Wrapped in ADK's Gemini class so temporary Google
# errors (503 "high demand", 429 rate limits) are retried automatically with
# growing waits (2s, 4s, 8s, ...) instead of failing the whole chat.
_raw_model = os.getenv("TRAVEL_MODEL", "gemini-3.8-flash")
_model_name = _raw_model.strip().strip("\"'").strip().removeprefix("models/")

MODEL = Gemini(
    model=_model_name,
    retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2, max_delay=30, exp_base=2),
)

# "mock" = fake but realistic data, no keys needed.  "serpapi" = real prices.
DATA_PROVIDER = os.getenv("TRAVEL_DATA_PROVIDER", "mock").strip().lower()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "").strip()

# SerpApi's free plan is ~250 searches/month, so we cache every response on disk.
CACHE_DIR = Path(os.getenv("TRAVEL_CACHE_DIR", ".travel_cache"))
CACHE_TTL_HOURS = float(os.getenv("TRAVEL_CACHE_TTL_HOURS", "24"))