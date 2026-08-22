"""
STEP 03 — Discovery 1 of 7:  THE STOP
═════════════════════════════════════

    python steps/step_03_stop.py

Imagine the program we are about to write. It keeps making bad decisions:

    call the weather API → think → call the weather API → think →
    call the weather API → think → ... forever.

    Q1. What actually happens? Name the consequence, not the word "loop".
    Q2. So before we create autonomy, what boundary goes around it?

Wait for the room. Then type ONE line.
"""

from lab import rule

rule("the most boring line in this repository")

MAX_STEPS = 5

print(f"MAX_STEPS = {MAX_STEPS}")

rule("why it is not boring")

print(
    """
Defend that number out loud. Not "5 feels right" — a budget.

    "One iteration is roughly 4 LLM calls. On this model that is about
     $0.002. I am willing to spend a cent on one run of this program.
     So: 5 iterations, and it dies at the 6th."

That is engineering. A loop with no stop is not a feature you shipped, it is
an uncontrolled process you released.

Tonight our budget is iterations. In production it becomes dollars, tokens,
wall-clock time, permissions, or a milestone condition — 'stop when the tests
pass'. Pick one. But have one, and write it BEFORE the first run, not after
the bill.
"""
)


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# We now have a budget and nothing to spend it on. Our program still gets
# exactly one chance at the goal.
#
#   Q3. What is the minimum Python construct that gives a program a SECOND
#       chance at something? You already know it. Do not say "agent loop".
#
#   Q4. `while` or `for`? Argue for one. What does your choice imply about
#       who owns the stopping condition — you, or the model?
#
# Then open step_04.
