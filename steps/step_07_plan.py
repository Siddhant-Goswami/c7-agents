"""
STEP 07 — Discovery 5 of 7:  PLAN
═════════════════════════════════

    python steps/step_07_plan.py

You named the failure modes: wrong ordering (predict before you fetch and the
prediction is guaranteed wrong), unnecessary calls, premature conclusions, and
an answer nobody can verify because there was no sequence to check it against.

Sequence is now part of correctness. The plan is where sequence lives.

And you found the second reason on your own: a plan is the cheapest artifact
in the loop to verify. A plan costs one LLM call. An action touches the world.

    Q. What is plan() really?
    A. Still an LLM call. But this one has to return something the PROGRAM
       can branch on, so we ask for JSON instead of prose.
"""

from lab import get_august_rainfall, llm, llm_json, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data."
)
MAX_STEPS = 3

TOOL_MENU = {
    "august_rainfall": "args {city, year} — August weekend-by-weekend rainfall, ONE city, ONE year",
    "current_weather": "args {city} — today's weather, right now",
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
    """Ordered steps for the whole job, plus exactly ONE next action."""
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


history = []

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    state = sense(GOAL, history, TOOL_MENU)
    show("STATE", state)

    the_plan = plan(GOAL, state, TOOL_MENU)
    show("PLAN", the_plan)

    # The model just told us which tool to call and with which arguments.
    # We are still ignoring it. Look at the next line and feel bad about it.
    result = get_august_rainfall("Bangalore", 2024)

    history.append(
        {
            "step": step + 1,
            "plan": the_plan,
            "action_actually_taken": "august_rainfall(city=Bangalore, year=2024)",
            "result": f"driest weekend {result['driest_weekend']}",
        }
    )


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# Read `PLAN.next` in each iteration. The model asked for a specific tool with
# specific arguments. We ran a hardcoded line instead.
#
#   Q1. Why didn't we just ask the model to execute the whole plan itself?
#       (Two reasons. One is about cost, one is about verification.)
#
#   Q2. We are about to honour `next`. Why not simply let the LLM write and
#       run arbitrary Python? It would be fewer lines. Give me four reasons.
#
#   Q3. Write out the line that turns {"tool": "x", "args": {...}}
#       into an actual function call. What Python type do you need first?
#
# Then open step_08.
