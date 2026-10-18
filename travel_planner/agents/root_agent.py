"""Root agent + the workflow it hands off to.

Flow:  user -> travel_coordinator (collects + validates the request)
              -> trip_pipeline = Sequential[ research_team (Parallel[flight, hotel, destination]),
                                             budget_agent, itinerary_agent ]
"""
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from .. import config
from ..tools.trip_tools import save_trip_request
from .budget_agent import budget_agent
from .destination_agent import destination_agent
from .flight_agent import flight_agent
from .hotel_agent import hotel_agent
from .itinerary_agent import itinerary_agent

# Step 1 of the pipeline: three independent researchers.
# Parallel = all at once (fast, but bursts of model calls can hit free-tier per-minute limits).
# Sequential = one after another (slower, gentler). Chosen by TRAVEL_PARALLEL_RESEARCH in .env.
_research_class = ParallelAgent if config.PARALLEL_RESEARCH else SequentialAgent
research_team = _research_class(
    name="research_team",
    description="Runs flight, hotel and destination research.",
    sub_agents=[flight_agent, hotel_agent, destination_agent],
)

# Step 2 and 3 need the research results, so they run afterwards, in order.
trip_pipeline = SequentialAgent(
    name="trip_pipeline",
    description="Researches flights, hotels and the destination, then budgets and plans the trip.",
    sub_agents=[research_team, budget_agent, itinerary_agent],
)

root_agent = LlmAgent(
    name="travel_coordinator",
    model=config.MODEL,
    description="Collects trip requirements and coordinates the travel-planning team.",
    instruction="""You are the Travel Coordinator, the friendly entry point of an AI travel-planning team.

Your job is to collect these details from the user:
- departure city, destination city
- departure date and return date (ask for exact dates)
- number of travelers
- total budget and its currency
- interests (optional, e.g. history, food, nature)

Rules:
1. Ask ONLY for what is missing, in one short message. Do not ask for things already given.
2. Work out the 3-letter IATA airport codes for the origin and destination yourself.
   If a city has several airports and the choice is unclear, ask the user.
3. When you have everything, call save_trip_request. If it returns an error, fix the problem
   (ask the user if needed) and call it again.
4. After it returns status "saved", say in ONE short sentence that your team is researching,
   then transfer to trip_pipeline. Do NOT write the itinerary yourself.
5. You can only plan and recommend; you cannot book or pay for anything.
6. If the user only chats or asks general travel questions, answer briefly and offer to plan a trip.""",
    tools=[save_trip_request],
    sub_agents=[trip_pipeline],
)