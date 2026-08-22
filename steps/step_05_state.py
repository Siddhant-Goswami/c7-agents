"""
STEP 05 — Discovery 3 of 7:  STATE
══════════════════════════════════

    python steps/step_05_state.py

The board said: what tool was called, what came back, what failed, what we
already concluded, and the original goal.

The smallest Python object that holds that is a list.
"""

from lab import get_august_rainfall, llm, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data."
)
MAX_STEPS = 3

history = []  # ← the entire memory system, for now

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    result = get_august_rainfall("Bangalore", 2024)
    answer = llm(f"Goal: {GOAL}\n\nData: {result}\n\nAnswer the goal in one line.")

    history.append(
        {
            "step": step + 1,
            "action": "get_august_rainfall('Bangalore', 2024)",
            "result_summary": f"{result['year']}: driest weekend {result['driest_weekend']}",
            "answer": answer,
        }
    )

    show("history length", len(history))

rule("WHAT THE SYSTEM NOW REMEMBERS")
for entry in history:
    show(f"step {entry['step']}", entry["result_summary"])


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# This tiny variable changed the nature of the system: it has a past.
#
# And we have just rediscovered the memory lecture. Here, memory is an
# embarrassing Python list. That is fine. Architecture first, sophistication
# later — episodic, semantic and procedural memory are all upgrades to THIS
# line, not replacements for it.
#
# But be honest about what we have and have not done. Run the program again
# and look at the answers, not the history:
#
#   Q1. Did the answer in iteration 3 differ from iteration 1?
#   Q2. Why not? The past is right there in `history`.
#   Q3. So what is still missing?
#
# The system has a memory that nothing reads. Before the model decides what
# to do, something has to hand it a picture of where it currently is.
#
#   Q4. List everything that belongs in that picture. Everything the model
#       needs to know BEFORE it decides anything.
#   Q5. What would you call the act of constructing that picture? One word.
#
# Then open step_06.
