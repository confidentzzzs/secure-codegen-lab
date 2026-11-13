"""STRATEGY 1: ROLE / SYSTEM PROMPT  (24 pts)

Change ONLY the system prompt: who the model is told to be, what it values, what it must never do.
The user message must stay exactly `_u(c["prompt"])`, so any difference in score comes from the role alone.

Rules (checked automatically): use c["prompt"] only. Anything that changes from case to case, such as c["cwe"],
is refused by generate.py. Do not paste benchmark tasks into the prompt.

Run:  python generate.py --methods s1_role --redo --out ../results/run.jsonl
"""
from prompts import _u


def s1_role(c):
    return [
        {"role": "system", "content": "You are a Python programmer."},   # TODO: write your own system prompt
        {"role": "user", "content": _u(c["prompt"])},
    ]
