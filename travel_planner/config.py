"""Central settings, read from environment variables (.env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.models import Gemini
from google.genai import types

load_dotenv()  # finds travel_planner/.env automatically


def _flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Clean the model name so quotes, spaces or a "models/" prefix can't break it.
_raw_model = os.getenv("TRAVEL_MODEL", "gemini-3.8-flash")
MODEL_NAME = _raw_model.strip().strip("\"'").strip().removeprefix("models/")

# Wrapped in ADK's Gemini class so temporary Google errors (503 "high demand",
# 429 per-minute limits) are retried with growing waits (2s, 4s, 8s ... up to 60s)
# instead of failing the whole chat. A DAILY quota cannot be fixed by retrying.
MODEL = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(attempts=8, initial_delay=2, max_delay=60, exp_base=2),
)

# --- Free-tier friendliness -------------------------------------------------
# Run flight, hotel and destination research ONE AFTER ANOTHER instead of at the
# same time. Same number of calls, but no burst, so per-minute limits are easier to stay under.
PARALLEL_RESEARCH = _flag("TRAVEL_PARALLEL_RESEARCH", False)

# Google Search grounding costs extra model calls and has its own quota.
# Set to false to save quota: the destination agent then uses weather data plus
# its general knowledge, and must say that nothing was verified online.
USE_SEARCH = _flag("TRAVEL_USE_SEARCH", True)

# "mock" = fake but realistic data, no keys needed.  "serpapi" = real prices.
DATA_PROVIDER = os.getenv("TRAVEL_DATA_PROVIDER", "mock").strip().lower()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "").strip()

# SerpApi's free plan is ~250 searches/month, so we cache every response on disk.
CACHE_DIR = Path(os.getenv("TRAVEL_CACHE_DIR", ".travel_cache"))
CACHE_TTL_HOURS = float(os.getenv("TRAVEL_CACHE_TTL_HOURS", "24"))