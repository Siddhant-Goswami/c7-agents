"""
STEP 2 — A budget, a loop, and a memory
════════════════════════════════════════

    python3 step2_loop.py

You said the software has to decide. Before we grant that freedom, we answer
your Q6 first — because a program that decides for itself when to continue is
a program that can decide to continue forever.

    Q. What actually happens then? Name the consequence, not the word "loop".
    A. Your API bill. Or your rate limit. Or a production system being
       poked 40,000 times at 3am.

So the boundary comes FIRST, and it is the most boring line in this repo:

    MAX_STEPS = 5

Defend that number from a budget, not a vibe: "one iteration is ~2 model
calls, this chain is 3 hops, 5 gives it room to recover from one mistake and
dies on the sixth." Here the budget is iterations. In production it becomes
dollars, tokens, wall-clock, or a milestone ('stop when the tests pass').
Pick one. But have one, and write it BEFORE the first run.

Now — everything else in this file is stuff you already own.
"""

from step1_one_shot import GOAL, TOOL_MENU, TOOLS, llm_json, rule

MAX_STEPS = 5  # ← the boundary. Written before the freedom, on purpose.


def decide_next(goal, history):
    """Ask the model for the SINGLE next tool call. This is one llm_json call.

    Nothing magic. The only new thing is that its answer is a decision the
    program will act on, instead of prose a human will read.
    """
    return llm_json(
        "Propose the SINGLE next tool call that makes progress on the GOAL.\n\n"
        f"TOOLS (only these exist):\n"
        f'  get_ticket    args {{"ticket_id":"T-…"}}    -> {{subject, filed_by}}\n'
        f'  get_employee  args {{"employee_id":"E-…"}}  -> {{name, manager}}\n\n'
        "RULE: never repeat a call whose args already appear in HISTORY —\n"
        "that result is already known.\n\n"
        'Return JSON exactly: {"thought":"…","tool":"…","args":{…}}\n\n'
        f"GOAL: {goal}\n"
        f"HISTORY: {history}\n"
    )


def run_tool(action):
    """The deterministic half. The model NAMED a tool; the runtime DECIDES
    whether that tool exists. Read those two facts next to each other:

        action = decide_next(...)      ← probabilistic judgement
        TOOLS[action["tool"]](...)     ← deterministic execution

    Q. Who has more power here — the model, or you?
    """
    name, args = action.get("tool"), action.get("args") or {}
    if name not in TOOLS:
        return {"error": f"no such tool {name!r}. allowed: {list(TOOLS)}"}
    try:
        return TOOLS[name](**args)
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


if __name__ == "__main__":
    print(f"GOAL: {GOAL}")

    # ─── PART 1 ─── a loop, and nothing else ──────────────────────────────
    rule("PART 1 — a loop with a budget, and no memory")

    for step in range(3):
        action = decide_next(GOAL, "nothing has happened yet")
        result = run_tool(action)
        print(f"  iteration {step + 1}:  {action.get('tool')}({action.get('args')})  ->  {result}")

    print(
        "\nThree iterations. Three identical iterations.\n"
        "We bought three chances and spent all three on the same chance.\n\n"
        "  Q. What is different between iteration 1 and iteration 3?\n"
        "  A. Nothing. So that is not iteration — it is repetition.\n\n"
        "A loop that cannot tell its turns apart is a `for` statement, not progress.\n"
        "  Q. What would iteration 2 need to know about iteration 1 to differ?\n"
        "  Q. What is the smallest Python object that holds that?"
    )

    # ─── PART 2 ─── the smallest thing that holds a turn ──────────────────
    rule("PART 2 — the same loop, plus a list")

    history = []  # ← the entire memory system. A list.

    for step in range(MAX_STEPS):
        action = decide_next(GOAL, history)
        result = run_tool(action)

        # Carry it forward. THIS is what makes the next turn a different turn.
        history.append({"step": step + 1, "tool": action.get("tool"),
                        "args": action.get("args"), "result": result})

        print(f"  iteration {step + 1}:  {action.get('tool')}({action.get('args')})  ->  {result}")

    rule("WHAT THE PROGRAM NOW KNOWS")
    for entry in history:
        print(f"  step {entry['step']}: {entry['tool']}({entry['args']}) -> {entry['result']}")

    print(
        "\nLook hard at that list. Somewhere in it is the answer to the goal.\n"
        "The program walked the chain on its own — we never typed the hops.\n"
        "\nAnd yet this program printed no answer, and would have kept going if\n"
        "MAX_STEPS were 50. Read the last iterations: once the chain was walked,\n"
        "it had nothing useful left to do, so it burned the rest of the budget.\n"
    )


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 3
# ══════════════════════════════════════════════════════════════════════════
#
# We now have four of the pieces:
#
#     the STOP      MAX_STEPS = 5, written before the freedom
#     the LOOP      another attempt is possible
#     the STATE     history — so turn 2 differs from turn 1
#     the ACTION    a registry the model may name, and nothing outside it
#
# And the program STILL cannot finish. Two things are missing, and this file
# shows you both if you read its output carefully:
#
#   Q1. A tool returned {"manager": "E-04"}. Is a returned value the same
#       thing as knowing what happened? What if it had returned
#       {"error": "no employee E-99"} — which line of this program would
#       have noticed, and changed its behaviour as a result?
#
#   Q2. The answer is sitting in `history` and the program never said it.
#       Something has to look at everything that has happened and decide:
#       are we done, or do we go again? Who does that right now?
#           → nobody. `range(MAX_STEPS)` does. That is a countdown, not a
#             judgement.
#
#   Q3. Name the two functions you would add. What does each one receive,
#       and what must each one return for the PROGRAM to branch on it?
#
# Write down Q3 before you continue. Then open step3_agent.py.
