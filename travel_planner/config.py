"""Central settings, read from environment variables (.env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # finds travel_planner/.env automatically

MODEL = os.getenv("TRAVEL_MODEL", "gemini-2.5-flash")

# "mock" = fake but realistic data, no keys needed.  "serpapi" = real prices.
DATA_PROVIDER = os.getenv("TRAVEL_DATA_PROVIDER", "mock").strip().lower()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "").strip()

# SerpApi's free plan is ~250 searches/month, so we cache every response on disk.
CACHE_DIR = Path(os.getenv("TRAVEL_CACHE_DIR", ".travel_cache"))
CACHE_TTL_HOURS = float(os.getenv("TRAVEL_CACHE_TTL_HOURS", "24"))
