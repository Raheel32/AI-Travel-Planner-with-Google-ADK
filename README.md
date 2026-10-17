# AI Travel Planner with Google ADK

A multi-agent trip planner: you chat with a **Travel Coordinator**; a team of specialist agents
then researches flights, hotels and the destination, checks the budget, and writes a day-by-day plan.

> **Status:** tested offline (13 tests, including a full end-to-end run with a scripted fake model) on
> Python 3.12 and google-adk 2.12.0. **Not yet tested against live Gemini or live SerpApi**: that's your first run.
> The agents research and recommend only. They **cannot book** anything.

---

## 1. The big picture

```
You ──► travel_coordinator (root agent: asks questions, validates, saves the trip request)
              │  transfer
              ▼
        trip_pipeline  (SequentialAgent: runs its steps IN ORDER)
          1. research_team (ParallelAgent: runs these AT THE SAME TIME)
               ├─ flight_agent       → tool: search_flights
               ├─ hotel_agent        → tool: search_hotels
               └─ destination_agent  → tools: Google Search + get_weather_forecast
          2. budget_agent            → tool: calculate_trip_budget (plain Python maths)
          3. itinerary_agent         → writes the final plan for you
```

### Concepts you'll meet (read once, they'll click when you run it)

| Concept | Meaning | Where in this project |
|---|---|---|
| **Agent (`LlmAgent`)** | An LLM + instructions + tools. It decides *what to do*. | `travel_planner/agents/*.py` |
| **Tool** | A normal Python function the LLM can call. ADK turns its **docstring and type hints** into the schema the LLM sees. | `travel_planner/tools/*.py` |
| **Sub-agent / transfer** | An agent can hand the conversation to another agent. | root → `trip_pipeline` |
| **Workflow agents** | `SequentialAgent` (in order) and `ParallelAgent` (at once). They contain no AI themselves: they just control order, so the flow is predictable. | `agents/root_agent.py` |
| **Session state** | A shared dictionary for one conversation. | `trip_request`, `flight_results`, ... |
| **`output_key`** | Saves an agent's final answer into state under that name. | every specialist agent |
| **`{placeholders}`** | In an instruction, `{flight_results}` is replaced by that state value. This is how agents pass data to each other. | `budget_agent`, `itinerary_agent` |
| **Pydantic model** | Validates data (dates, airport codes, ranges) so bad values are caught early. | `models/trip_models.py` |
| **Provider pattern** | Only `services/providers.py` knows where data comes from. Swap `mock` → `serpapi` → something else without touching any agent. | `services/providers.py` |

**Two design rules worth remembering:** (1) the LLM never does money maths, since `calculate_trip_budget` does;
(2) the LLM never invents availability, since agents are told to report errors instead of guessing.

---

## 2. Setup (step by step)

You need **Python 3.10+** (check with `python --version`; on macOS/Linux it may be `python3`).

**Step 1: open a terminal in this folder** (the one containing `README.md` and the `travel_planner/` folder).

**Step 2: create and activate a virtual environment** (an isolated box for this project's packages):

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```
Your prompt should now start with `(.venv)`. If PowerShell blocks the script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then retry.

**Step 3: install the packages**

```bash
pip install -r requirements.txt
```

**Step 4: get a free Gemini API key** at https://aistudio.google.com/apikey

**Step 5: create your `.env` file.** Copy `travel_planner/.env.example` to `travel_planner/.env`
(same folder, new name) and paste your key:

```bash
# Windows:  copy travel_planner\.env.example travel_planner\.env
# macOS/Linux:  cp travel_planner/.env.example travel_planner/.env
```
Leave `TRAVEL_DATA_PROVIDER=mock` for now. `.env` is git-ignored, so your key will not be committed.

**Step 6: run the tests** (no key or internet needed):

```bash
python -m pytest
```
You should see `13 passed`.

**Step 7: start the ADK dev UI.** Run this from the folder that *contains* `travel_planner/` (not inside it):

```bash
adk web
```
Open the URL it prints (usually http://localhost:8000), choose **travel_planner** in the top-left dropdown, and chat.

### Try these prompts

1. `Hi, what can you do?` (the root answers directly)
2. `Plan a 5-day trip from Karachi to Istanbul for 2 people, budget 2500 USD, leaving 2027-04-10 and returning 2027-04-15. We like food and history.`
   (use dates in the future)

In the UI, open the **Events / Trace** tab: you'll see `save_trip_request`, the transfer, the three researchers
running side by side, then the budget and itinerary agents. Reading this trace is the fastest way to *understand* ADK.

With `mock` data, flights and hotels are labelled **MOCK**. That's correct behaviour: the agents must say so.

---

## 3. Going live with real prices (SerpApi)

1. Create a free account at https://serpapi.com (the free plan was **250 searches/month** when I checked,
   so confirm on their pricing page).
2. In `travel_planner/.env` set:
   ```
   TRAVEL_DATA_PROVIDER=serpapi
   SERPAPI_API_KEY=your_key_here
   ```
3. Restart `adk web` and plan a trip again.

**Protect your quota:** every response is cached in `.travel_cache/` for 24 hours, so repeating the same trip costs nothing.
One trip = 2 searches (flights + hotels). Keep `mock` on while developing and switch to `serpapi` for real checks.

**Know the limits** (SerpApi gets data from Google Flights/Hotels, it isn't an airline or booking API):
- I wrote the response parsing from SerpApi's documented format but could not test it against a live key. If a field is missing,
  the tool returns fewer options or an `error` and the agents say so. Please tell me what you see and we'll adjust.
- Flight price is treated as **per traveler** and times shown are for the **outbound** leg only. Verify on the booking page.
- It's a scraping-based service: fine for learning, but read its terms before building anything commercial.

**Swapping providers later** (e.g. Duffel or LiteAPI): add a function in `services/providers.py` returning the same
`FlightSearchResult` / `HotelSearchResult`, add one `if config.DATA_PROVIDER == "..."` branch. No agent changes.

---

## 4. Project map

```
travel_planner/
├── __init__.py            # tells ADK to import agent.py
├── agent.py               # exposes root_agent (ADK requires this exact name)
├── config.py              # reads .env settings
├── .env.example           # copy to .env
├── agents/                # WHO decides: root, flight, hotel, destination, budget, itinerary
├── tools/                 # WHAT they can do: trip request, flights, hotels, weather, budget
├── services/providers.py  # WHERE data comes from: mock / SerpApi + disk cache
└── models/trip_models.py  # Pydantic data contracts
tests/                     # offline tests, including a full fake-LLM pipeline run
```

---

## 5. Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `adk web` shows no agent | Run it from the folder that **contains** `travel_planner/`. |
| `404 model not found` | Your key doesn't offer that model. Change `TRAVEL_MODEL` in `.env` (see the model list in AI Studio). |
| `429 RESOURCE_EXHAUSTED` | Free-tier rate limit: three agents call Gemini at once. Wait a minute, or try a lighter model. |
| `Key 'trip_request' not found` | An agent ran before the request was saved. Start a new session in the UI and give all details. |
| Google Search tool error in `destination_agent` | `bypass_multi_tools_limit` needs ADK ≥ 1.16. Upgrade: `pip install -U google-adk`. If it persists, replace the tools list with `[get_weather_forecast]` and re-add search later through an `AgentTool`. |
| `DeprecationWarning: SequentialAgent / ParallelAgent` | Newer ADK versions are steering toward a `Workflow` API, but say it cannot yet be used as an `LlmAgent` sub-agent, which our root relies on. Everything works; we'll migrate once it can. |
| `SerpApi error` / `HTTP 401` | Check `SERPAPI_API_KEY`. Errors never print your key. |
| No weather forecast | Open-Meteo only forecasts ~16 days ahead; the agent falls back to typical seasonal weather and says so. |

---

## 6. Where to go next

1. Read the trace for a few trips; change an agent's `instruction` and watch the behaviour change.
2. Add a **route/travel-time tool** (Google Routes API) to the itinerary agent for realistic day plans.
3. Add **structured output** (`output_schema` with Pydantic) so the final plan is JSON for a UI.
4. Wrap it in a **FastAPI** endpoint or **Streamlit** page.
5. Add `adk eval` test cases for important conversations.
