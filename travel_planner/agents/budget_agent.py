from google.adk.agents import LlmAgent

from .. import config
from ..tools.budget_tools import calculate_trip_budget

budget_agent = LlmAgent(
    name="budget_agent",
    model=config.MODEL,
    description="Estimates the total trip cost and checks it against the budget.",
    instruction="""You are the Budget Agent. You never do money maths yourself: you always use the tool.

Trip request (JSON): {trip_request}

Flight research:
{flight_results}

Hotel research:
{hotel_results}

1. Read CHEAPEST_FLIGHT_PRICE_PER_TRAVELER and CHEAPEST_HOTEL_RATE_PER_NIGHT from the research above.
2. Call calculate_trip_budget with those numbers plus nights, travelers and budget from the trip request.
   nights = days between departure_date and return_date.
   If a value is UNAVAILABLE, pass 0 for it and clearly warn that the total is INCOMPLETE.
3. Present the breakdown (flights, hotel, food, local transport, activities, contingency),
   the total, and whether it is within budget. If over budget, give the tool's suggestions.
4. State the assumptions the tool reports. Do not change any number the tool returned.""",
    tools=[calculate_trip_budget],
    output_key="budget_results",
)
