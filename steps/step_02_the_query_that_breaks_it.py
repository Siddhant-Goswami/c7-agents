"""
STEP 02 — The query that breaks it
══════════════════════════════════

    python steps/step_02_the_query_that_breaks_it.py

Same program. Different question.

    "My sister's wedding is in Bangalore this August.
     From the last 10 years of data, which weekend is least likely to rain?"

Do not read ahead. Answer these first:

    Q1. How many tool calls does this need?
    Q2. Do we know, before starting, exactly which calls will be necessary?
    Q3. What happens if one of them fails?
    Q4. What if the data that comes back changes what we need next?
"""

from lab import get_august_rainfall, llm, rule, show

GOAL = (
    "Find the August weekend in Bangalore that is least likely to rain, "
    "using the last 10 years of rainfall data."
)

rule("ATTEMPT A — the program we already have")

result = get_august_rainfall("Bangalore", 2024)
answer = llm(f"Goal: {GOAL}\n\nData: {result}\n\nAnswer the goal.")
show("answer", answer)

print(
    "\nThat answer is about ONE year. The goal said ten. The program had no way\n"
    "to know it was under-informed, and no way to go get the rest."
)

rule("ATTEMPT B — fine, fetch all ten years first")

years = range(2016, 2026)
everything = [get_august_rainfall("Bangalore", y) for y in years]
blob = str(everything)

show("years fetched", len(everything))
show("characters we are about to send the model", f"{len(blob):,}")

try:
    answer = llm(f"Goal: {GOAL}\n\nData for ten years: {blob}\n\nAnswer the goal.")
    show("answer", answer)
    print(
        "\nIt fit — this time. In the tool-calling practical this exact shape threw a\n"
        "context-window error from the API. Either way, look at what we just did."
    )
except Exception as error:  # noqa: BLE001
    show("ERROR", error)
    print(
        "\nThere it is. Same failure as the tool-calling practical. The system breaks\n"
        "at the boundary rather than degrading quietly."
    )


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you move on
# ══════════════════════════════════════════════════════════════════════════
#
# Look at ATTEMPT B and find the human fingerprints. Every one of these was a
# decision, and every one of them was made by us, in advance, in the source:
#
#     range(2016, 2026)      ← we chose ten. we chose which ten.
#     [ ... for y in years]  ← we chose to loop. we chose to fetch before asking.
#     one final llm(...)     ← we chose that one pass was enough.
#
# And when ATTEMPT B breaks, who reads the error and picks the fix? We do.
# Output correct → the user decides what happens next.
# Output wrong   → the builder decides what happens next.
# Either way: a human decides. That human does not scale.
#
# So here is the only question for the next 70 minutes:
#
#     ┌────────────────────────────────────────────────────────────────┐
#     │  What is the MINIMUM we must add to this program so that the   │
#     │  software, rather than the human, decides what happens next?   │
#     └────────────────────────────────────────────────────────────────┘
#
#   Q5. Before we add anything at all — is there something we should decide
#       FIRST, before we hand a program the freedom to keep going?
#
# Answer Q5 before you continue. Then open step_03.
