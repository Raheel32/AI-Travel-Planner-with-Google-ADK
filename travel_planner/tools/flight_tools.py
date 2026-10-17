"""Flight tool: reads the saved trip request, asks the provider, returns plain data."""
from __future__ import annotations

from datetime import datetime, timezone

from google.adk.tools import ToolContext

from .. import config
from ..models.trip_models import FlightSearchResult
from ..services import providers
from .trip_tools import load_trip_request


async def search_flights(tool_context: ToolContext) -> dict:
    """Search round-trip flight options for the saved trip request.

    Takes no arguments: it reads the validated trip request from session state,
    so the LLM cannot accidentally change the dates or airports.

    Returns:
        A dict with `options` (cheapest first), `cheapest_price_per_traveler`,
        `provider`, `retrieved_at`, and possibly `note` or `error`.
    """
    req = load_trip_request(tool_context)
    if req is None:
        return {"error": "No trip request has been saved yet."}
    try:
        result = await providers.search_flights(req)
    except Exception as exc:  # never crash the agent: report the failure instead
        result = FlightSearchResult(
            provider=config.DATA_PROVIDER, currency=req.currency, error=str(exc),
            retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
    return result.model_dump(mode="json")
