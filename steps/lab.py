"""Plumbing, not ideas.

Every step file starts with `from lab import ...`. This module does two things
and then gets out of the way:

  1. puts the repo root on sys.path, so `python steps/step_04_loop.py` works
     from the project root without any PYTHONPATH gymnastics;
  2. re-exports the four givens — llm, llm_json, and the two weather tools —
     plus two printing helpers.

Nothing in here is part of tonight's argument. Open agent_lab/llm.py and
agent_lab/tools.py if you want to see what the givens actually are.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent_lab.display import rule, show  # noqa: E402
from agent_lab.llm import MODEL, llm, llm_json  # noqa: E402
from agent_lab.tools import get_august_rainfall, get_weather  # noqa: E402

__all__ = [
    "MODEL",
    "llm",
    "llm_json",
    "get_weather",
    "get_august_rainfall",
    "rule",
    "show",
]
