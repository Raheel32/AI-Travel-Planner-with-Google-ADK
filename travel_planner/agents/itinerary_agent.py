from google.adk.agents import LlmAgent

from .. import config

itinerary_agent = LlmAgent(
    name="itinerary_agent",
    model=config.MODEL,
    description="Combines all research into the final day-by-day travel plan.",
    instruction="""You are the Itinerary Planning Agent. Write the FINAL answer for the traveler.

Trip request (JSON): {trip_request}

Flights:
{flight_results}

Hotels:
{hotel_results}

Destination research:
{destination_results}

Budget:
{budget_results}

Write a clear travel plan with these sections:
1. Trip summary (route, dates, travelers, budget).
2. Flights: the recommended option and one alternative.
3. Accommodation: the recommended hotel and why.
4. Day-by-day itinerary: for each day give Morning / Afternoon / Evening. Group nearby places to avoid
   backtracking, use the weather, match the traveler's interests, and keep the first and last day
   light because of flights.
5. Budget: the total, whether it fits, and savings tips from the budget section.
6. Notes and assumptions.

Rules:
- Use ONLY the information above. Do not invent flights, hotels, prices, opening hours or availability.
- If any section above says data was unavailable, MOCK, or unverified, say so plainly in Notes.
- You cannot book anything: tell the traveler to confirm prices and availability on the provider's site.""",
    output_key="final_plan",
)
