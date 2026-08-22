"""
STEP 01 — LLM + tool
════════════════════

    python steps/step_01_llm_plus_tool.py

You said the missing thing was live data. Here it is. This is the tool-calling
lecture, in six lines.

Now the question the whole session hangs on:

    Is this an agent?
"""

from lab import get_weather, llm

user_query = "What is the weather in Bangalore right now?"

result = get_weather("Bangalore")

answer = llm(f"Question: {user_query}\n\nLive data: {result}\n\nAnswer in one sentence.")

print(answer)


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# Walk the three questions again, slowly, and notice that the answer to every
# one of them is the same:
#
#   Q1. Who decided that get_weather() should be called?          → we did
#   Q2. Who decided that "Bangalore" was the argument?            → we did
#   Q3. Who decided to send the result back to the LLM?           → we did
#   Q4. Who decides what happens after print(answer)?             → the user
#
# So the shape is still:
#
#       Human → LLM → Tool → LLM → Human
#
# The LLM *participates* in this workflow. It does not *control* it.
#
#   Q5. So — is this an agent? Answer yes or no, and say why.
#   Q6. If not, name the one thing you would have to add. One thing.
#
# Then open step_02.
