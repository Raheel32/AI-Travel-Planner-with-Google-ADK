from google.adk.agents import LlmAgent

from .. import config
from ..tools.flight_tools import search_flights

flight_agent = LlmAgent(
    name="flight_agent",
    model=config.MODEL,
    description="Searches and compares flight options for the saved trip request.",
    instruction="""You are the Flight Research Agent.

Trip request (JSON): {trip_request}

1. Call search_flights exactly once.
2. If the result has an "error", say flight data is unavailable and why. NEVER invent flights or prices.
3. Otherwise summarise the 3 best options, cheapest first: airline(s), stops, total duration,
   departure/arrival times, and price per traveler with its currency.
4. Mention the data provider and the retrieved_at time, plus any "note" from the result
   (for example that it is MOCK data). Say prices are not guaranteed until booked.
5. Finish with ONE last line in exactly this form:
   CHEAPEST_FLIGHT_PRICE_PER_TRAVELER: <number, or UNAVAILABLE>
Keep the answer short.""",
    tools=[search_flights],
    output_key="flight_results",
)
