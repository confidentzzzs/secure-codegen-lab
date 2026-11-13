"""REFERENCE SOLUTION, strategy 4 (instructor only): plan -> code. Stage 1 lists the attack scenarios (no code); stage 2 writes code that defends against them."""
from prompts import _u


def s4_two_stage(c):
    return [
        {"role": "system", "content": "You are a security-conscious Python programmer."},
        {"role": "user", "content": "Here is a Python function to implement:\n\n```python\n" + c["prompt"] + "\n```\n\n"
                                    "Do NOT write code yet. List at most 3 concrete ways an attacker could abuse this function (what input, what damage), one line each."},
    ]


def s4_two_stage_stage2(c, first_output):
    return s4_two_stage(c) + [
        {"role": "assistant", "content": first_output},
        {"role": "user", "content": "Now complete the function. " + "Return the COMPLETE file (including the given code) in one ```python block, "
                                    "with code that defends against exactly the attacks you listed, and keep it concise (under about 60 lines)."},
    ]
