"""
STEP 00 — Where we start
════════════════════════

    python steps/step_00_one_llm_call.py

Before you run it, answer this:

    What kind of system is this?

There are no new ideas on this page. This is the very first thing you built
in Module 2. We are starting here on purpose.
"""

from lab import llm

user_query = "What is the weather in Bangalore right now?"

answer = llm(user_query)

print(answer)


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# The answer above is confidently written and completely made up. The model
# has no idea what today's weather is.
#
#   Q1. What is the single thing this program is missing?
#   Q2. Who decided that `llm()` should be called at all?
#   Q3. Who decides what happens after `print(answer)`?
#
# Write your answer to Q1 down before you continue. Then open step_01.
