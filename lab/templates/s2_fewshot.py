"""STRATEGY 2: FEW-SHOT / IN-CONTEXT LEARNING WITH YOUR OWN EXAMPLES  (24 pts)

Write at least 2 demonstrations: (task stub, secure completion). The model sees them before the real task.
Rules (checked automatically): the demos must be YOUR OWN, about functions that are NOT in the benchmark
(pasting a benchmark task is refused). Do not copy `FEWSHOT` from prompts.py (you may read it for the format).
Hints: which vulnerability types do your demos cover? Does a demo about X help on a task about Y?

Run:  python generate.py --methods s2_fewshot --redo --out ../results/run.jsonl
"""
from prompts import _u, _a

DEMOS = [
    # (stub, secure_completion): both are full Python source strings, e.g.
    # ("import os\n\ndef read_note(name):\n    '''Return the text of the note called `name`.'''",
    #  "import os\n\ndef read_note(name):\n    '''Return the text of the note called `name`.'''\n    ..."),
]


def s2_fewshot(c):
    msgs = [{"role": "system", "content": "You are a Python programmer."}]
    for stub, solution in DEMOS:
        msgs += [{"role": "user", "content": _u(stub)}, {"role": "assistant", "content": _a(solution)}]
    msgs.append({"role": "user", "content": _u(c["prompt"])})
    return msgs
