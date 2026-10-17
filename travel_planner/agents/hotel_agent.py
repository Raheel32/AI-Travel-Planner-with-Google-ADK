from google.adk.agents import LlmAgent

from .. import config
from ..tools.hotel_tools import search_hotels

hotel_agent = LlmAgent(
    name="hotel_agent",
    model=config.MODEL,
    description="Finds and compares hotel options for the saved trip request.",
    instruction="""You are the Hotel Research Agent.

Trip request (JSON): {trip_request}

1. Call search_hotels exactly once.
2. If the result has an "error", say hotel data is unavailable and why. NEVER invent hotels or prices.
3. Otherwise recommend up to 3 hotels (a budget, a mid-range and a comfort pick if available):
   name, rate per night (per room), rating, stars, key amenities and a link if one is given.
4. Mention the data provider, retrieved_at time and any "note" (for example that it is MOCK data).
   Say availability must be confirmed before booking.
5. Finish with ONE last line in exactly this form:
   CHEAPEST_HOTEL_RATE_PER_NIGHT: <number, or UNAVAILABLE>
Keep the answer short.""",
    tools=[search_hotels],
    output_key="hotel_results",
)
