from google.adk.agents import LlmAgent
from google.adk.tools.google_search_tool import GoogleSearchTool

from .. import config
from ..tools.weather_tools import get_weather_forecast

_SEARCH_INSTRUCTION = """You are the Destination Research Agent.

Trip request (JSON): {trip_request}

1. Call get_weather_forecast for the destination city and the trip dates.
   If no forecast is available, describe typical seasonal weather and clearly say it is NOT a forecast.
2. Use Google Search to find: top attractions and landmarks, restaurants / local food, and
   experiences that match the traveler's interests. Also find practical tips
   (local customs, getting around, safety, typical opening-day quirks).
3. Report only what you found. If you could not verify something (opening hours, prices), say so.
4. Output sections: Weather, Top attractions, Food, Experiences for your interests, Practical tips.
   Mention the source website for key facts.
Keep it focused and concise."""

_NO_SEARCH_INSTRUCTION = """You are the Destination Research Agent. Online search is switched OFF to save quota.

Trip request (JSON): {trip_request}

1. Call get_weather_forecast for the destination city and the trip dates.
   If no forecast is available, describe typical seasonal weather and clearly say it is NOT a forecast.
2. From your general knowledge, list well-known attractions, local food and experiences that match
   the traveler's interests, plus basic practical tips.
3. Start the answer with this line: "NOTE: from general knowledge, not verified online. Check opening hours and prices before going."
4. Never state exact opening hours, ticket prices or events as facts.
5. Output sections: Weather, Top attractions, Food, Experiences for your interests, Practical tips.
Keep it focused and concise."""

if config.USE_SEARCH:
    # bypass_multi_tools_limit lets the built-in Google Search live beside our own tool
    # (needs a recent google-adk; see the README troubleshooting section).
    _tools = [GoogleSearchTool(bypass_multi_tools_limit=True), get_weather_forecast]
    _instruction = _SEARCH_INSTRUCTION
else:
    _tools = [get_weather_forecast]
    _instruction = _NO_SEARCH_INSTRUCTION

destination_agent = LlmAgent(
    name="destination_agent",
    model=config.MODEL,
    description="Researches attractions, food, weather and practical tips for the destination.",
    instruction=_instruction,
    tools=_tools,
    output_key="destination_results",
)