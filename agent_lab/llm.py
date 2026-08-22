"""The probabilistic half. Given to you, not derived.

Two functions. Both are just: send text to an LLM, get text back.

Everything else in this lab is built out of these two functions,
a dictionary, and a Python list. Nothing is imported from a framework,
because there is no framework.
"""

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DEFAULT_SYSTEM = "You are a precise assistant. Answer directly, no preamble."

_client = None


def _groq() -> Groq:
    """Built on first use, so the steps that never call an LLM need no key."""
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key or key == "gsk_replace_me":
            raise SystemExit(
                "\nNo GROQ_API_KEY found.\n"
                "  1. cp .env.example .env\n"
                "  2. paste your key from https://console.groq.com/keys\n"
            )
        _client = Groq(api_key=key)
    return _client


def llm(prompt: str, system: str = DEFAULT_SYSTEM) -> str:
    """One LLM call in, one string out. This is the whole probabilistic half."""
    response = _groq().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def llm_json(prompt: str, system: str = DEFAULT_SYSTEM) -> dict:
    """Same call, but we insist the model hands back a JSON object.

    Why this exists: some steps of the loop produce prose for a human to read,
    and some produce a decision the *program* has to branch on. `if reflection["done"]`
    needs a dict, not a paragraph. That is the only difference.
    """
    response = _groq().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system + " Reply with a single JSON object."},
            {"role": "user", "content": prompt},
        ],
    )
    return _extract_json(response.choices[0].message.content)


def _extract_json(text: str) -> dict:
    """Models occasionally wrap JSON in prose or a code fence. Survive that."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    braced = re.search(r"\{.*\}", text, re.DOTALL)
    if braced:
        return json.loads(braced.group(0))

    raise ValueError(f"Model did not return JSON. It returned:\n{text}")
