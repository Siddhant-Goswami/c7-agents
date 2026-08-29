"""
STEP 9. Not a new capability. The same system, in somebody else's words.

    pip install openai-agents
    python3 step9_sdk.py

Nothing below can do anything steps 4 to 8 could not. This file exists so that
when you read an SDK's documentation next week, every noun in it already has a
thing in your own code that it replaced.

| What we built | SDK abstraction |
| while loop | Runner |
| tool registry | Tools |
| message history | Session / context |
| run_subagent() | Agent-as-tool / handoff |
| limits | Runner configuration |
| save_state / load_state | Session / store |
| permission_gate() | Approval / middleware |
| compact_history() | SDK context mechanisms |

Read that table as a bill. The right-hand column is what you stop typing. It
is also what you stop being able to see, and every row of it is a decision
somebody made without asking you.
"""

import os

try:
    from agents import (Agent, OpenAIChatCompletionsModel, Runner, function_tool,
                        set_tracing_disabled)
    from openai import AsyncOpenAI
except ImportError as error:
    raise SystemExit(
        f"step 9 needs the one library this repo otherwise refuses: {error}\n\n"
        "    pip install -U openai-agents\n\n"
        "Steps 1 to 8 do not need it and still run without it."
    )

from step1_one_shot import GOAL, MODEL, get_employee, get_ticket

set_tracing_disabled(True)

# Groq speaks the OpenAI wire format, so the SDK points at it and the model
# does not change. Same model as every other file in this repo, on purpose.
llm = OpenAIChatCompletionsModel(
    model=MODEL,
    openai_client=AsyncOpenAI(api_key=os.environ["GROQ_API_KEY"],
                              base_url="https://api.groq.com/openai/v1"),
)


# ── Tools. Same two functions. The decorator is the whole difference. ──────
@function_tool
def ticket(ticket_id: str) -> str:
    """Look up one ticket. Returns its subject and who filed it."""
    return str(get_ticket(ticket_id))


@function_tool
def employee(employee_id: str) -> str:
    """Look up one employee. Returns their name and their manager's id."""
    return str(get_employee(employee_id))


# ── run_subagent() becomes an agent used as a tool. ───────────────────────
researcher = Agent(
    name="lookup_specialist",
    instructions="Resolve employee ids to names. Answer in one line. Never invent a name.",
    model=llm,
    tools=[employee],
)

agent = Agent(
    name="ticket_agent",
    instructions=("Answer the question using the tools. A manager's NAME is never "
                  "an id like E-04: look it up."),
    model=llm,
    tools=[ticket, researcher.as_tool(
        tool_name="ask_lookup_specialist",
        tool_description="Delegate an employee id to name lookup to a fresh agent.")],
)

if __name__ == "__main__":
    print(f"model={MODEL}\nGOAL: {GOAL}\n")

    # max_turns is the whole budget layer of step 8, as a keyword argument.
    result = Runner.run_sync(agent, GOAL, max_turns=6)

    print(f"\nanswer: {result.final_output}")
    print(f"turns:  {len(result.new_items)} items in the session the SDK kept for you")
    print("\nThe loop did not disappear. You stopped writing it.")


# ══════════════════════════════════════════════════════════════════════════
# PREDICT: the last one
# ══════════════════════════════════════════════════════════════════════════
#
# Rebuild this file yourself without looking, then name where your loop, your
# history, your gate and your budget went. An SDK is someone else's rung zero,
# tested at scale: what exactly did you buy, and what did you give up the
# ability to see?
#
# Then, one last time:
#
#   Q. There is no permission_gate() above. A tool in that list writes to a
#      filesystem. Find, in the SDK's own documentation, the hook where your
#      gate goes. If you cannot find it in five minutes, that is the answer to
#      the question above.
