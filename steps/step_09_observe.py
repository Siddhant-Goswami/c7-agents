"""
STEP 09 — Discovery 6 of 7:  OBSERVE
════════════════════════════════════

    python steps/step_09_observe.py

    A RESULT is what the environment returned.
    An OBSERVATION is what that result MEANS for the task.

This is the augmentation step from the RAG lecture, turned inward. Same move,
different audience: there we turned tool output into an answer for the user;
here we turn tool output into an account for the model itself.

The question is not "what did the API say?"
The question is "given my goal, what did I just learn?"
"""

from lab import get_august_rainfall, get_weather, llm, llm_json, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data (2016-2025)."
)
MAX_STEPS = 3

TOOL_MENU = {
    "august_rainfall": "args {city, year} — August weekend-by-weekend rainfall, ONE city, ONE year (1960-2025)",
    "current_weather": "args {city} — today's weather, right now",
}
TOOLS = {"august_rainfall": get_august_rainfall, "current_weather": get_weather}


def sense(goal, history, tool_menu):
    return llm(
        "You are the SENSE step of an agent loop.\n"
        "Describe the CURRENT SITUATION in 3-4 lines. Do not plan. Do not act.\n"
        "Say what is known, what is still missing, and what just happened.\n\n"
        f"GOAL: {goal}\n"
        f"TOOLS AVAILABLE: {tool_menu}\n"
        f"HISTORY SO FAR ({len(history)} steps): {history or 'nothing has happened yet'}\n"
    )


def plan(goal, state, tool_menu):
    return llm_json(
        "You are the PLAN step of an agent loop.\n"
        "Return JSON exactly like:\n"
        '{"steps": ["...", "..."], "next": {"tool": "<tool name>", "args": {...}}}\n\n'
        "Rules:\n"
        "- `steps` is the full ordered sequence still needed to reach the goal.\n"
        "- `next` is the SINGLE next action, and its tool must be one of the tools listed.\n"
        "- Do not repeat an action that already appears in history.\n\n"
        f"GOAL: {goal}\n"
        f"TOOLS AVAILABLE: {tool_menu}\n"
        f"CURRENT STATE: {state}\n"
    )


def act(the_plan, tools):
    action = the_plan.get("next") or {}
    name, args = action.get("tool"), action.get("args") or {}
    if name not in tools:
        return {"ok": False, "error": f"No such tool {name!r}. Allowed: {list(tools)}"}
    try:
        return {"ok": True, "data": tools[name](**args)}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}


def observe(goal, action, result):
    """Turn a raw result into an account written for the agent, not the user."""
    return llm(
        "You are the OBSERVE step of an agent loop.\n"
        "In 2-3 lines, state ONLY what was learned and whether it moves the goal forward.\n"
        "Be explicit if the result was empty, an error, off-target, or insufficient.\n"
        "Do not decide what to do next. That is somebody else's job.\n\n"
        f"GOAL: {goal}\n"
        f"ACTION TAKEN: {action}\n"
        f"RAW RESULT: {str(result)[:2000]}\n"
    )


history = []

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    state = sense(GOAL, history, TOOL_MENU)
    the_plan = plan(GOAL, state, TOOL_MENU)
    result = act(the_plan, TOOLS)
    observation = observe(GOAL, the_plan.get("next"), result)

    show("NEXT ACTION", the_plan.get("next"))
    show("OBSERVATION", observation)

    history.append(
        {
            "step": step + 1,
            "action": the_plan.get("next"),
            "observation": observation,
        }
    )


# ══════════════════════════════════════════════════════════════════════════
# THE CRITICAL MOMENT — do not skip this
# ══════════════════════════════════════════════════════════════════════════
#
# Put the whole loop on screen:
#
#       for step in range(MAX_STEPS):
#           state       = sense(...)
#           the_plan    = plan(...)
#           result      = act(...)
#           observation = observe(...)
#
#   Q1. Are we done? Is this an agent?
#
# Sit with it. Then:
#
#   Q2. Who decides whether that observation is ENOUGH?
#   Q3. What if we have only collected 2017?
#   Q4. What if the tool failed?
#   Q5. What if we already have all ten years and know the answer — what in
#       this code stops it running two more times and spending your budget?
#   Q6. What decides whether another iteration is necessary at all?
#
# And now the question this entire module has been asking since last session:
#
#     ┌────────────────────────────────────────────────────────────────┐
#     │              WHO DECIDES WHAT HAPPENS NEXT?                    │
#     └────────────────────────────────────────────────────────────────┘
#
# If your answer is "the model" — then write the line. Actually write it, in
# your editor, before you open step_10 and see it.
