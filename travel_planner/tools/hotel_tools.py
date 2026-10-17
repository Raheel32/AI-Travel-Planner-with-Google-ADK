"""Hotel tool: same pattern as the flight tool."""
from __future__ import annotations

from datetime import datetime, timezone

from google.adk.tools import ToolContext

from .. import config
from ..models.trip_models import HotelSearchResult
from ..services import providers
from .trip_tools import load_trip_request


async def search_hotels(tool_context: ToolContext) -> dict:
    """Search hotel options for the saved trip request (dates, city, travelers).

    Returns:
        A dict with `options` (cheapest first), `cheapest_rate_per_night`
        (per room), `provider`, `retrieved_at`, and possibly `note` or `error`.
    """
    req = load_trip_request(tool_context)
    if req is None:
        return {"error": "No trip request has been saved yet."}
    try:
        result = await providers.search_hotels(req)
    except Exception as exc:
        result = HotelSearchResult(
            provider=config.DATA_PROVIDER, currency=req.currency, error=str(exc),
            retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
    return result.model_dump(mode="json")
