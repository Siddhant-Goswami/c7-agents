"""
STEP 1 — The program you already know how to write
═══════════════════════════════════════════════════

    python3 step1_one_shot.py

You already know how to call an LLM and how to call a tool. This file adds
nothing to that. It is here so we can agree on what we have — and then find
the exact place it breaks.

THE SETUP, if you have never seen a ticketing system:
When something breaks at an office, a college or a hospital, somebody writes
it down. That written-down complaint is a TICKET — a note with an ID like
"T-1002", a description, and a record of who reported it. data.json holds
tickets and people, and neither list names anybody directly: they use ID
codes, like roll numbers. A ticket says it was filed by "E-17". Looking up
E-17 gets you her name, and her manager's code — not her manager's name.
So the question below takes three lookups, and each one hands you the code
you need for the next.

The question this file asks:

    Who decides what happens next?

Everything above the line marked GIVENS is plumbing you already understand.
Read it once, then forget it. The lecture is below that line.
"""

import json
import os
import pathlib
import re
import time

import requests

# ══════════════════════════════════════════════════════════════════════════
#  GIVENS — the two halves. Nothing here is the idea.
# ══════════════════════════════════════════════════════════════════════════
#
#  The probabilistic half: llm() and llm_json(), which send text to a model.
#  The deterministic half: get_ticket() and get_employee(), which read a file.
#
#  Both providers speak the same OpenAI-shaped API, so this is ONE code path.
#  No SDK, no framework — just requests.

if pathlib.Path(".env").exists():  # optional convenience, not required
    for line in pathlib.Path(".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

PROVIDER = os.getenv("PROVIDER", "groq")

if PROVIDER == "groq":
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = os.getenv("MODEL", "openai/gpt-oss-20b")
    API_KEY = os.getenv("GROQ_API_KEY", "")
else:
    BASE_URL = "http://localhost:11434/v1/chat/completions"
    MODEL = os.getenv("MODEL", "qwen3.5:9b")
    API_KEY = "ollama"

SYSTEM = "You are a precise assistant. Answer directly, no preamble."


def _chat(prompt: str, system: str, as_json: bool) -> str:
    """One HTTP request. Retries on rate limits so a free key survives a lecture."""
    if PROVIDER == "groq" and not API_KEY:
        raise SystemExit(
            "\nNo GROQ_API_KEY set.\n"
            "  export GROQ_API_KEY=gsk_...      (free key: https://console.groq.com/keys)\n"
            "  ...or run fully offline:  PROVIDER=ollama python3 step1_one_shot.py\n"
        )

    body = {
        "model": MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if as_json:
        body["response_format"] = {"type": "json_object"}

    for attempt in range(6):
        response = requests.post(
            BASE_URL, json=body, timeout=600,
            headers={"Authorization": f"Bearer {API_KEY}"},
        )

        if response.status_code == 429:  # free tiers are rate limited; wait it out
            hint = re.search(r"try again in ([\d.]+)s", response.text)
            wait = float(hint.group(1)) + 1 if hint else 8.0
            print(f"    (rate limited, waiting {wait:.0f}s)")
            time.sleep(wait)
            continue

        # In strict JSON mode the API rejects the model's own malformed output.
        # It is a coin-flip, not a bug in your prompt — so just ask again.
        if response.status_code == 400 and "json_validate" in response.text:
            print("    (model emitted invalid JSON, retrying)")
            continue

        if not response.ok:  # never make a student debug a bare status code
            raise SystemExit(f"\n{PROVIDER} returned {response.status_code}:\n{response.text[:400]}\n")

        return (response.json()["choices"][0]["message"].get("content") or "").strip()

    raise SystemExit("Six failed attempts in a row. Wait a minute and re-run.")


def llm(prompt: str, system: str = SYSTEM) -> str:
    """Text in, text out. For things a human reads."""
    return _chat(prompt, system, as_json=False)


def llm_json(prompt: str, system: str = SYSTEM) -> dict:
    """Text in, dict out. For decisions the PROGRAM has to branch on.

    `if reflection["answer"]` needs a dict, not a paragraph. That is the only
    difference between this and llm().
    """
    text = _chat(prompt, system + " Reply with a single JSON object.", as_json=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)  # survive a stray code fence
        if not match:
            raise ValueError(f"Model did not return JSON:\n{text}")
        return json.loads(match.group(0))


DATA = json.loads(pathlib.Path(__file__).with_name("data.json").read_text())


def get_ticket(ticket_id: str) -> dict:
    """One ticket. Tells you WHO filed it — never who manages them."""
    return DATA["tickets"].get(ticket_id, {"error": f"no ticket {ticket_id}"})


def get_employee(employee_id: str) -> dict:
    """One employee. Tells you their manager's ID — never that manager's name."""
    return DATA["employees"].get(employee_id, {"error": f"no employee {employee_id}"})


# Every key here is a permission you granted on purpose. The model may name
# these and nothing else. Notice this is a plain dict.
TOOLS = {"get_ticket": get_ticket, "get_employee": get_employee}

TOOL_MENU = {
    "get_ticket": 'args {"ticket_id": "T-…"} -> {subject, filed_by, priority}',
    "get_employee": 'args {"employee_id": "E-…"} -> {name, team, manager}',
}

GOAL = "What is the NAME of the manager of the person who filed ticket T-1002?"


def rule(label=""):
    print(f"\n── {label} " + "─" * max(0, 74 - len(label)) if label else "─" * 76)


# ══════════════════════════════════════════════════════════════════════════
#  THE LECTURE STARTS HERE
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"provider={PROVIDER}  model={MODEL}")
    print(f"\nGOAL: {GOAL}")

    # ─── ATTEMPT A ─── one tool call, then ask the model ──────────────────
    rule("ATTEMPT A — one tool call, like last week")

    ticket = get_ticket("T-1002")
    print(f"get_ticket('T-1002') -> {ticket}")

    answer = llm(f"Question: {GOAL}\n\nData: {ticket}\n\nAnswer in one short sentence.")
    print(f"\nanswer: {answer}")

    print(
        "\nThe ticket knows WHO filed it (E-17). It does not know who manages E-17,\n"
        "and it does not know anybody's name. The model cannot invent either one.\n"
        "One tool call is not enough — and nothing in this program noticed that."
    )

    # ─── ATTEMPT B ─── fine, we'll write the whole chain ourselves ────────
    rule("ATTEMPT B — fine, we write out every hop by hand")

    hop1 = get_ticket("T-1002")
    hop2 = get_employee(hop1["filed_by"])
    hop3 = get_employee(hop2["manager"])

    print(f"hop 1  get_ticket('T-1002')      -> filed_by = {hop1['filed_by']}")
    print(f"hop 2  get_employee('{hop1['filed_by']}')       -> manager  = {hop2['manager']}")
    print(f"hop 3  get_employee('{hop2['manager']}')       -> name     = {hop3['name']}")
    print(f"\nanswer: {hop3['name']}   ← correct!")

    print(
        "\nCorrect. So we are done, right?\n"
        "Look at what made it correct: WE knew there were exactly three hops.\n"
        "We typed that knowledge into the source code."
    )

    # ─── THE SAME CODE, A DIFFERENT TICKET ────────────────────────────────
    rule("ATTEMPT B, unchanged, pointed at ticket T-1007")

    hop1 = get_ticket("T-1007")
    hop2 = get_employee(hop1["filed_by"])
    print(f"hop 1  get_ticket('T-1007')      -> filed_by = {hop1['filed_by']}")
    print(f"hop 2  get_employee('{hop1['filed_by']}')       -> manager  = {hop2['manager']}")

    try:
        hop3 = get_employee(hop2["manager"])
        print(f"hop 3  get_employee({hop2['manager']}) -> {hop3}")
        print(f"\nanswer: {hop3.get('name')}   ← garbage. E-01 is the CEO; there is no hop 3.")
    except Exception as error:
        print(f"\nCRASH: {type(error).__name__}: {error}")

    print(
        "\nSame program. Different ticket. The chain was two hops long, not three,\n"
        "and the program had no way to notice. It does exactly what we typed —\n"
        "every single time — including when what we typed is wrong."
    )


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 2
# ══════════════════════════════════════════════════════════════════════════
#
# Walk the questions. Notice the answer to every one of them is the same:
#
#   Q1. Who decided get_ticket() should be called first?        → we did
#   Q2. Who decided "E-17" was the argument to hop 2?           → we did
#   Q3. Who decided there were exactly three hops?              → we did
#   Q4. Who reads the crash above and picks the fix?            → we do
#
# The shape is still:   Human → Tool → Tool → Tool → LLM → Human
# The LLM PARTICIPATES in this workflow. It does not CONTROL it.
#
# And here is the thing that makes this problem different from last week's:
#
#     You cannot write hop 2 until hop 1 has returned.
#     The argument to the next call is INSIDE the previous result.
#
# So no amount of planning ahead saves you. The sequence is not knowable
# in advance — not by us, not by anyone.
#
#   Q5. What is the minimum we must add so that the SOFTWARE, not the human,
#       decides what happens next?
#
#   Q6. Before we hand a program the freedom to keep going — is there
#       something we should decide FIRST?
#
# Write down Q5 and Q6. Then open step2_loop.py.
