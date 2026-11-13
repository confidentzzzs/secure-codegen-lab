"""STRATEGY 3: STRUCTURED REASONING OR CHECKLIST  (24 pts)

Give the model a scaffold to follow BEFORE it writes code: a security checklist, a step-by-step reasoning recipe,
or a "threat -> mitigation" table. The scaffold is added to the user message.
Rules (checked automatically): use c["prompt"] only; the same scaffold for every case.
Hints: long prompts can hurt a 1.7B model (more broken code). Try shorter/longer scaffolds and compare.

Run:  python generate.py --methods s3_structured --redo --out ../results/run.jsonl
"""
from prompts import _u

SCAFFOLD = ""   # TODO: your checklist / reasoning steps, e.g. "Before coding, think: (1) ... (2) ..."


def s3_structured(c):
    return [
        {"role": "system", "content": "You are a Python programmer."},
        {"role": "user", "content": _u(c["prompt"]) + ("\n\n" + SCAFFOLD if SCAFFOLD else "")},
    ]
