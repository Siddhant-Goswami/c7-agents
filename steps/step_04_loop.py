"""
STEP 04 — Discovery 2 of 7:  THE LOOP
═════════════════════════════════════

    python steps/step_04_loop.py

Someone said it: a loop. `for`, not `while`, because `for` carries our budget
in its own signature — `range(MAX_STEPS)` IS the stopping condition.

This is the first genuinely new thing we have added tonight. Notice what did
NOT change: same LLM, same tool, same Python. The intelligence did not get
more intelligent. We gave the system another turn.
"""

from lab import get_august_rainfall, llm, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data."
)
MAX_STEPS = 3  # small, so you can watch every turn

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1}")

    result = get_august_rainfall("Bangalore", 2024)
    answer = llm(f"Goal: {GOAL}\n\nData: {result}\n\nAnswer the goal in one line.")

    show("action", "get_august_rainfall('Bangalore', 2024)")
    show("answer", answer)


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# Look at the three iterations you just watched.
#
#   Q1. What is different between iteration 1 and iteration 3?
#   Q2. So is that really iteration 3 — or is it iteration 1, happening again?
#
# A loop that cannot tell its turns apart is not iteration, it is repetition.
# We bought three chances and spent them all on the same chance.
#
#   Q3. Name everything iteration 2 would need to know about iteration 1 for
#       it to be a genuinely different turn. Shout them out; we will write
#       them on the board.
#
#   Q4. What is the smallest Python object that could hold that?
#
# Then open step_05.
