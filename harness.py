"""
HARNESS: the shared plumbing for steps 4 to 9. Read once, then forget it.

Nothing in this file is a lesson. Every idea in Part 2 appears in the step
file that needs it. What lives here is the boring, repeated machinery: the
scratch directory and its guard, the five new tools, a token counter, and
the three loop steps (PLAN, ACT, REFLECT) that steps 4 to 8 all reuse
unchanged so that each file is a readable delta and nothing else.

Two notes before you skim it:

  1. Steps 4 to 8 run PLAN, ACT, REFLECT. SENSE and OBSERVE have not been
     deleted from the idea of an agent, and step 3 derived both. They are
     dropped here only to keep a live log short enough to read on a screen,
     because every file in Part 2 is about what SURROUNDS the loop rather
     than what happens inside it.

  2. llm() and llm_json() below are step 1's two functions with one line
     added: the token count the API already hands back. step1_one_shot.py
     is not modified. Nothing in Part 1 changes.
"""

import json
import os
import pathlib
import random
import re
import subprocess
import sys
import zlib

from groq import APIStatusError, BadRequestError, RateLimitError

from step1_one_shot import MODEL, client, get_employee, get_ticket, rule  # noqa: F401

ROOT = pathlib.Path(__file__).parent
SCRATCH = ROOT / "scratch"
SCRATCH.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
#  THE TOKEN METER
# ══════════════════════════════════════════════════════════════════════════
#
#  Every model call prints what it cost. In step 2 the budget was iterations
#  because iterations were all we could count. Now we can count the thing the
#  invoice actually counts, so we do.
#
#  List prices for the default model, in US dollars per million tokens. If
#  you swap MODEL, swap these too, or the rupee figure is fiction.

PRICE_IN, PRICE_OUT = 0.075, 0.30
USD_TO_INR = 88.0

USAGE = {"calls": 0, "prompt": 0, "completion": 0}

# How many words search_docs returns per call. 2,000 makes context growth
# impossible to miss. On a free Groq key, whose cap is 8,000 tokens per
# minute, `export SEARCH_WORDS=600` keeps every demo inside the allowance.
SEARCH_WORDS = int(os.getenv("SEARCH_WORDS", "2000"))


class ContextTooLarge(RuntimeError):
    """The prompt did not fit, and no retry will make it fit.

    This is the wall step 6 exists to show. On a paid key it is the model's
    context window; on a free one it is the tokens-per-minute cap, which
    arrives sooner and behaves identically. Either way the cure is the same:
    send less. It is a named exception rather than a returned dict because a
    loop cannot plan its way around a request it is not allowed to make.
    """


def _friendly_crash(kind, error, traceback):
    """Turn the two failures that are somebody else's quota, not your bug,
    into a sentence instead of forty lines of stack.

    Both of them are the same lesson arriving from outside: a run that grows
    without limit eventually meets a limit it did not set.
    """
    if isinstance(error, RateLimitError):
        rule("OUT OF TOKENS")
        print(f"  {str(error).split('Need more tokens')[0].strip()}\n")
        print("  That is your API key's allowance, not a fault in this lab.\n"
              "  Wait for the window Groq names above, use another key, or make\n"
              "  the context-heavy steps smaller:\n\n"
              "      export SEARCH_WORDS=600\n\n"
              "  which cuts what search_docs returns per call, and with it most\n"
              "  of what steps 6 and 8 spend.")
        return
    if isinstance(error, ContextTooLarge):
        rule("THE CONTEXT DID NOT FIT")
        print(f"  {error}\n\n  This is step 6's whole subject, arriving early.")
        return
    sys.__excepthook__(kind, error, traceback)


sys.excepthook = _friendly_crash


def reset_usage():
    USAGE.update(calls=0, prompt=0, completion=0)


def tokens_used():
    return USAGE["prompt"] + USAGE["completion"]


def rupees_used():
    return (USAGE["prompt"] * PRICE_IN + USAGE["completion"] * PRICE_OUT) / 1e6 * USD_TO_INR


def _record(label, reply):
    """Read the usage field the API already returns, and say it out loud."""
    usage = getattr(reply, "usage", None)
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    USAGE["calls"] += 1
    USAGE["prompt"] += prompt
    USAGE["completion"] += completion
    print(
        f"    [tokens] {label:<8} in={prompt:>6,}  out={completion:>5,}"
        f"   run total={tokens_used():>7,}  (about Rs {rupees_used():.2f})"
    )


def _guard(error):
    """A 413 is not a rate limit and not a bad request. It is a refusal, and
    the client will not retry its way out of one."""
    if getattr(error, "status_code", None) == 413 or "too large" in str(error):
        raise ContextTooLarge(str(error).split("please reduce")[0].strip()) from None
    raise error


def llm(prompt: str, label: str = "llm") -> str:
    try:
        reply = client.chat.completions.create(
            model=MODEL, temperature=0.2, messages=[{"role": "user", "content": prompt}]
        )
    except APIStatusError as error:
        _guard(error)
    _record(label, reply)
    return (reply.choices[0].message.content or "").strip()


def llm_json(prompt: str, label: str = "llm_json") -> dict:
    for _ in range(3):
        try:
            reply = client.chat.completions.create(
                model=MODEL, temperature=0.2,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
            )
            _record(label, reply)
            return json.loads(reply.choices[0].message.content)
        except BadRequestError:
            continue  # step 1's contract: a fumbled format is asked again
        except APIStatusError as error:
            _guard(error)
        except (json.JSONDecodeError, TypeError):
            continue
    return {"thought": "the model did not return usable JSON"}


# ══════════════════════════════════════════════════════════════════════════
#  THE BLAST RADIUS: one directory, and a guard that refuses everything else
# ══════════════════════════════════════════════════════════════════════════

def inside_scratch(path):
    """Resolve `path` under scratch/, or return None if it points outside.

    A bare name means scratch/name. A path already starting with scratch/ is
    taken from the repo root. Anything else, including ../ escapes, symlinks
    and absolute paths, resolves outside SCRATCH and gets refused.
    """
    p = pathlib.Path(os.path.expanduser(str(path)))
    if not p.is_absolute():
        p = ROOT / p if p.parts and p.parts[0] == SCRATCH.name else SCRATCH / p
    resolved = p.resolve()
    root = SCRATCH.resolve()
    return resolved if resolved == root or root in resolved.parents else None


def read_file(path: str) -> dict:
    target = inside_scratch(path)
    if target is None:
        return {"error": f"refused: {path} is outside scratch/"}
    if not target.exists():
        return {"error": f"no such file {path}"}
    return {"path": str(target.relative_to(ROOT)), "content": target.read_text()}


def write_file(path: str, content: str) -> dict:
    target = inside_scratch(path)
    if target is None:
        return {"error": f"refused: {path} is outside scratch/"}
    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return {"wrote": str(target.relative_to(ROOT)), "bytes": len(content),
            "overwrote_existing_file": existed}


def bash(command: str) -> dict:
    """Run a shell command with scratch/ as the working directory.

    Be honest about what this is: a working directory plus a crude check for
    escapes is NOT a sandbox. A determined command gets out of it in one line.
    In production the blast radius is drawn by a container, a service account,
    or a filesystem you do not own. Here it only has to be tight enough that
    the demo cannot damage your laptop while you watch.
    """
    # Refuse ".." , "sudo", and any token that starts at the root or the home
    # directory. `rm -rf /` has to be refused BEFORE the shell sees it, not
    # after: a blocklist you test by running the command is not a blocklist.
    if ".." in command or "sudo" in command or re.search(r"""(^|[\s=<>|;&'"(])[~/]""", command):
        return {"error": "refused: command reaches outside scratch/"}
    try:
        done = subprocess.run(command, shell=True, cwd=SCRATCH, timeout=10,
                              capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return {"error": "timeout after 10s"}
    return {"exit_code": done.returncode,
            "stdout": done.stdout[-1500:], "stderr": done.stderr[-500:]}


# ══════════════════════════════════════════════════════════════════════════
#  THE PROPS: two tools that exist to make a failure visible on stage
# ══════════════════════════════════════════════════════════════════════════

_NOISE = (
    "the retry budget observed in production deployments consistently latency "
    "queue depth idempotency key rotation window cache invalidation downstream "
    "consumer backpressure vendor gateway settlement batch reconciliation ledger "
    "webhook replay signature drift timeout ceiling circuit breaker half open "
    "shard rebalance cold start percentile regression rollout cohort audit trail"
).split()


def search_docs(query: str) -> dict:
    """Return about 2,000 words of plausible-sounding noise about `query`.

    THIS IS A PROP. It searches nothing. It exists so that context growth is
    something you can watch climb in the token line rather than something you
    have to take on faith. The seed comes from the query, so two runs of the
    same query return byte-identical text and the before/after numbers in
    step 6 are comparable.
    """
    rng = random.Random(zlib.crc32(str(query).encode()))
    body = " ".join(rng.choice(_NOISE) for _ in range(SEARCH_WORDS - 20))
    return {"query": query, "words": SEARCH_WORDS,
            "text": f"Findings for {query}. " + body + f" End of findings for {query}."}


def flaky_tool(**_) -> dict:
    """A tool that always fails. Every real toolbox contains one of these:
    the vendor API that is down, the endpoint that was renamed last Tuesday."""
    return {"error": "upstream unavailable (503). this tool always fails."}


# ══════════════════════════════════════════════════════════════════════════
#  TOOL REGISTRIES AND THEIR DOCS
# ══════════════════════════════════════════════════════════════════════════

FILE_TOOLS = {"bash": bash, "read_file": read_file, "write_file": write_file}
TICKET_TOOLS = {"get_ticket": get_ticket, "get_employee": get_employee}

DOCS = {
    "get_ticket": '  get_ticket    args {"ticket_id":"T-…"}     -> {subject, filed_by}',
    "get_employee": '  get_employee  args {"employee_id":"E-…"} -> {name, manager}',
    "read_file": '  read_file     args {"path":"scratch/x.md"} -> {content}',
    "write_file": '  write_file    args {"path":"scratch/x.md","content":"…"} -> {wrote}',
    "bash": '  bash          args {"command":"ls"}         -> {exit_code, stdout}',
    "search_docs": '  search_docs   args {"query":"…"}          -> {text} (long)',
    "flaky_tool": '  flaky_tool    args {}                     -> deploy status',
}


def tool_docs(tools):
    return "\n".join(DOCS[name] for name in tools)


# ══════════════════════════════════════════════════════════════════════════
#  THE THREE LOOP STEPS, generalised over any tool registry
# ══════════════════════════════════════════════════════════════════════════

def plan(goal, history, tools, extra=""):
    return llm_json(
        "You are the PLAN step of an agent loop. Propose the SINGLE next tool call.\n\n"
        "TOOLS (only these exist):\n" + tool_docs(tools) + "\n\n"
        "RULE: never repeat a call whose args already appear in HISTORY.\n"
        'Return JSON exactly: {"thought":"…","tool":"…","args":{…}}\n\n'
        f"GOAL: {goal}\n"
        f"{extra}"
        f"HISTORY: {history}\n",
        label="plan",
    )


def act(action, tools):
    """Touch the world. The model NAMED a tool; the runtime DECIDES."""
    name, args = action.get("tool"), action.get("args") or {}
    if name not in tools:
        return {"error": f"no such tool {name!r}. allowed: {list(tools)}"}
    try:
        return tools[name](**args)
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


def reflect(goal, history, extra=""):
    return llm_json(
        "You are the REFLECT step of an agent loop. You alone decide whether it stops.\n\n"
        'Return JSON exactly: {"answer":"<one line stating the finished result>"}\n'
        "if HISTORY shows the GOAL is fully achieved, otherwise\n"
        '{"answer":null,"missing":"what is still needed"}\n\n'
        "RULES:\n"
        "- A tool that returned an error achieved nothing. Do not treat it as done.\n"
        "- If the goal was to write a file, it is done only once a write succeeded.\n"
        "- Copy names from a \"name\" field. Never answer with an ID like E-04.\n\n"
        f"GOAL: {goal}\n"
        f"{extra}"
        f"HISTORY: {history}\n",
        label="reflect",
    )


# ══════════════════════════════════════════════════════════════════════════
#  SMALL HELPERS
# ══════════════════════════════════════════════════════════════════════════

def preview(value, limit=110):
    """Shorten a value for the LOG only. History keeps the whole thing, which
    is exactly why step 6 has a problem to solve."""
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + f" …(+{len(text) - limit} chars)"


def show(action, result):
    print(f"  PLAN     {action.get('tool')}({preview(action.get('args'), 60)})"
          f"   ({preview(action.get('thought', ''), 70)})")
    print(f"  ACT      {preview(result)}")


def validate(obj, spec):
    """A schema check, by hand, in seven lines. `spec` maps key -> type.

    You do not need a validation library to refuse a malformed dict. You need
    to have decided which keys are required, which is the part a library
    cannot do for you.
    """
    if not isinstance(obj, dict):
        raise ValueError(f"expected a dict, got {type(obj).__name__}")
    for key, kind in spec.items():
        if key not in obj:
            raise ValueError(f"missing required key {key!r}")
        if not isinstance(obj[key], kind):
            raise ValueError(f"key {key!r} must be {kind.__name__}, got {type(obj[key]).__name__}")
    return obj


def ask_yes_no(question):
    """y/n from the terminal. If there is no terminal (CI, a piped run), the
    answer is no: a gate that opens when nobody is watching is not a gate."""
    if not sys.stdin.isatty():
        print(f"{question} [no terminal attached, so the gate answers: n]")
        return False
    try:
        return input(f"{question} [y/N] ").strip().lower().startswith("y")
    except EOFError:
        # Stdin closed under us. Fail closed. Every question a gate cannot
        # get an answer to is a no, including the ones it never got to ask.
        print("\n  [stdin closed, so the gate answers: n]")
        return False
