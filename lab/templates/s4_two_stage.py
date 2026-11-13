"""STRATEGY 4: TWO-STAGE PROMPTING  (24 pts)

The model is called TWICE. Stage 1 = `s4_two_stage(c)`; its answer is passed to stage 2 = `s4_two_stage_stage2(c, first_output)`.
The code that is scored is the answer of stage 2. Typical designs: (a) plan: stage 1 lists the risks, stage 2 writes code that
handles them; (b) draft and fix: stage 1 writes code, stage 2 reviews and repairs it (note: `self_refine` already does a simple version of this;
yours must be different, e.g. a more specific review).
Both functions return a list of chat messages. Stage 2 usually includes the stage-1 conversation:
  messages_of_stage1 + [{"role": "assistant", "content": first_output}, {"role": "user", "content": "..."}]
Rules (checked automatically): use c["prompt"] only; no answer key.

Run:  python generate.py --methods s4_two_stage --redo --out ../results/run.jsonl      (takes about 2x as long)
"""
from prompts import _u


def s4_two_stage(c):             # stage 1
    return [
        {"role": "system", "content": "You are a Python programmer."},
        {"role": "user", "content": _u(c["prompt"])},        # TODO
    ]


def s4_two_stage_stage2(c, first_output):   # stage 2: sees what the model answered in stage 1
    return s4_two_stage(c) + [
        {"role": "assistant", "content": first_output},
        {"role": "user", "content": "Output the final COMPLETE code in one ```python block."},   # TODO
    ]
