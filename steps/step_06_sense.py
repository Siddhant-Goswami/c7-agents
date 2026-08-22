"""
STEP 06 — Discovery 4 of 7:  SENSE
══════════════════════════════════

    python steps/step_06_sense.py

Your list probably filled up fast: the goal, the user's request, history,
previous tool results, what tools exist, what we are allowed to do, the
environment.

And the word you reached for was probably "context", or "state", or
"perception".

The word from robotics is SENSE. A Roomba with the best cleaning algorithm
ever written and no sensor for where it is will clean nothing. Perception
comes before planning.

    Q. Is sense() magic? What could it actually be?
    A. It is an LLM call. That is all it has ever been.
"""

from lab import get_august_rainfall, llm, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data."
)
MAX_STEPS = 3

# What the model is ALLOWED to know it can do. Note: descriptions, not functions.
TOOL_MENU = {
    "august_rainfall": "args {city, year} — August weekend-by-weekend rainfall, ONE city, ONE year",
    "current_weather": "args {city} — today's weather, right now",
}


def sense(goal, history, tool_menu):
    """Construct the relevant state. This is context engineering as a loop step."""
    return llm(
        "You are the SENSE step of an agent loop.\n"
        "Describe the CURRENT SITUATION in 3-4 lines. Do not plan. Do not act.\n"
        "Say what is known, what is still missing, and what just happened.\n\n"
        f"GOAL: {goal}\n"
        f"TOOLS AVAILABLE: {tool_menu}\n"
        f"HISTORY SO FAR ({len(history)} steps): {history or 'nothing has happened yet'}\n"
    )


history = []

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    state = sense(GOAL, history, TOOL_MENU)
    show("STATE", state)

    # Still hardcoded by us. We have not delegated any decision yet.
    result = get_august_rainfall("Bangalore", 2024)

    history.append(
        {
            "step": step + 1,
            "state": state,
            "action": "august_rainfall(city=Bangalore, year=2024)",
            "result": f"driest weekend {result['driest_weekend']}, median {result['median_weekend_mm']}mm",
        }
    )


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# Read the three STATE blocks in order. They are different. That is new — and
# it is the first time iteration 2 has been conditioned on iteration 1.
#
#   Q1. Did the model NOTICE that we fetched the same year three times?
#       Did it say so?
#
# It probably did. Which is embarrassing for us, because we ignored it.
#
# Now the model knows where it is. So:
#
#   Q2. Should it call a tool immediately?
#
# Before you answer, look at the size of the actual job: ten years, ten API
# calls, extract rainfall per weekend, compare across years, handle a year
# with missing data, then conclude.
#
#   Q3. What goes wrong if it starts executing before deciding the sequence?
#       Name at least three failure modes.
#   Q4. What is the cheapest artifact in this whole loop to check for
#       correctness — the state, the sequence, or the tool result?
#
# Then open step_07.
