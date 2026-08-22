"""Printing helpers so we can watch the loop think. Not part of the idea."""

import json
import shutil

WIDTH = min(shutil.get_terminal_size((88, 20)).columns, 88)


def rule(label: str = "") -> None:
    if not label:
        print("─" * WIDTH)
        return
    print(f"\n── {label} " + "─" * max(0, WIDTH - len(label) - 4))


def show(label: str, value) -> None:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, indent=2)
    print(f"{label}: {value}")
