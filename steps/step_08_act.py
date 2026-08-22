"""
STEP 08 — ACT, and the boundary you are actually designing
══════════════════════════════════════════════════════════

    python steps/step_08_act.py

You answered Q2: security, permissions, hallucinated tools that do not exist,
arbitrary side effects on a machine you own.

So the Python type you need is a dictionary — a registry. The model may only
name things that are keys in it.

Read these two lines next to each other. They are the most important two
lines in the file:

    the_plan = plan(...)                       ← probabilistic judgement
    TOOLS[action["tool"]](**action["args"])    ← deterministic execution

The model PROPOSES an action. The runtime DECIDES which actions exist at all.

    Q. Who has more power here — the model or the developer?
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

# The possible world. The model gets to move inside it; it does not get to
# expand it. Every key here is a permission you granted on purpose.
TOOLS = {
    "august_rainfall": get_august_rainfall,
    "current_weather": get_weather,
}


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
    """Cross the boundary. Everything below this line is deterministic."""
    action = the_plan.get("next") or {}
    name = action.get("tool")
    args = action.get("args") or {}

    if name not in tools:
        # The model asked for a tool that does not exist. This is not a crash,
        # it is information — and in a moment it becomes something to reflect on.
        return {"ok": False, "error": f"No such tool {name!r}. Allowed: {list(tools)}"}

    try:
        return {"ok": True, "data": tools[name](**args)}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}


history = []

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    state = sense(GOAL, history, TOOL_MENU)
    show("STATE", state)

    the_plan = plan(GOAL, state, TOOL_MENU)
    show("NEXT ACTION", the_plan.get("next"))

    result = act(the_plan, TOOLS)
    show("RESULT", str(result)[:400] + ("..." if len(str(result)) > 400 else ""))

    history.append({"step": step + 1, "plan": the_plan, "result": result})


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# The model is now choosing which year to fetch. We did not write a single
# year number. That is one decision delegated.
#
# Now look hard at the RESULT lines.
#
#   Q1. The API returned something. Does that mean the action SUCCEEDED?
#
# Most rooms say yes. So consider these, one at a time:
#
#       {"ok": True, "data": {"weekends": []}}     ← 200, and empty
#       {"ok": False, "error": "500 ..."}          ← it failed
#       ... rainfall data, but for Delhi           ← right shape, wrong city
#       ... one perfect year of data               ← real, useful, and nowhere
#                                                     near enough for the goal
#
#   Q2. So what is the difference between a RESULT and an OBSERVATION?
#   Q3. In RAG, augmentation turned retrieved information into an answer for
#       the USER. What is the equivalent move here, and who is the audience?
#
# Then open step_09.
