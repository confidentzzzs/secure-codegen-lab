"""Generate code for every (case, method).
Backend: Hugging Face transformers (works on a free Colab T4 or any local GPU/CPU).
Usage: python generate.py --model Qwen/Qwen3-1.7B --out ../results/run.jsonl"""
import argparse, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompts import METHODS, REFINE, STUDENT_METHODS, TWO_STAGE

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = "Qwen/Qwen3-1.7B"
DEFAULT_METHODS = [m for m in METHODS if m not in STUDENT_METHODS] + ["self_refine"]  # your strategies are run on their own: --methods s1_role


class HFBackend:
    def __init__(self, model, args):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch, self.a, self.trunc = torch, args, []
        if not torch.cuda.is_available():
            print("WARNING: no GPU found. Generation will be VERY slow (hours). On Colab: Runtime > Change runtime type > T4 GPU.", flush=True)
        self.tok = AutoTokenizer.from_pretrained(model, padding_side="left")
        if self.tok.pad_token_id is None: self.tok.pad_token = self.tok.eos_token
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32  # T4 has no bf16
        try:    # newer transformers call this `dtype`, older ones `torch_dtype`
            self.model = AutoModelForCausalLM.from_pretrained(model, dtype=dtype)
        except TypeError:
            self.model = AutoModelForCausalLM.from_pretrained(model, torch_dtype=dtype)
        self.model.to("cuda" if torch.cuda.is_available() else "cpu").eval()
        self.stop_ids = {i for i in (self.tok.pad_token_id, self.tok.eos_token_id, getattr(self.model.generation_config, "eos_token_id", None)) if isinstance(i, int)}
        eos = getattr(self.model.generation_config, "eos_token_id", None)
        if isinstance(eos, (list, tuple)): self.stop_ids |= set(eos)

    def __call__(self, batch):  # list of message lists -> list of strings
        torch, out = self.torch, []
        for i in range(0, len(batch), self.a.batch_size):
            texts = [self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True, enable_thinking=False)
                     for m in batch[i:i + self.a.batch_size]]
            enc = self.tok(texts, return_tensors="pt", padding=True).to(self.model.device)
            kw = dict(do_sample=True, temperature=self.a.temp, top_p=0.95) if self.a.temp > 0 else dict(do_sample=False)
            kw['repetition_penalty'] = self.a.rep_penalty
            with torch.no_grad():
                g = self.model.generate(**enc, max_new_tokens=self.a.max_tokens, pad_token_id=self.tok.pad_token_id, **kw)
            new = g[:, enc["input_ids"].shape[1]:]
            # truncated = the batch used the whole budget AND this row did not end with a stop token
            self.trunc += [bool(new.shape[1] >= self.a.max_tokens and int(row[-1]) not in self.stop_ids) for row in new]
            out += self.tok.batch_decode(new, skip_special_tokens=True)
        return out


def extract(text):
    blocks = re.findall(r"```(?:python|py)?\n(.*?)```", text, re.S)
    if blocks: return max(blocks, key=len) if len(blocks) > 1 and "def " not in blocks[-1] else blocks[-1]
    m = re.search(r"```(?:python|py)?\n(.*)", text, re.S)  # unclosed fence (output hit the token limit)
    return m.group(1) if m else text


def check_messages(name, msgs):
    ok = isinstance(msgs, list) and msgs and all(isinstance(x, dict) and x.get("role") in ("system", "user", "assistant")
                                                  and isinstance(x.get("content"), str) for x in msgs)
    if not ok:
        sys.exit(f"Method '{name}' must return a list of chat messages like [{{'role': 'user', 'content': '...'}}], "
                 f"but returned: {str(msgs)[:150]}")


def check_case_independent(name, cases):
    """A strategy may depend on c["prompt"] only. If anything else in the messages changes from case to case
    (e.g. c["cwe"]), it uses the answer key: refuse. Also refuse if another benchmark task is pasted into the prompt."""
    if name == "cwe_hint" or not cases: return
    def text(c): return "\n".join(x["content"] for x in METHODS[name](c))
    norm = {}
    for c in cases:
        t = text(c)
        for p in sorted({c["prompt"], c["prompt"].strip()}, key=len, reverse=True): t = t.replace(p, "<TASK>")
        norm[c["id"]] = t
        for o in cases:
            if o["id"] != c["id"] and o["prompt"].strip() in t:
                sys.exit(f"Method '{name}': the benchmark task {o['id']} appears inside your prompt for {c['id']}. "
                         "Do not paste benchmark tasks as examples; write your own.")
    if len(set(norm.values())) > 1:
        sys.exit(f"Method '{name}' builds a different prompt for different cases (apart from c['prompt']). "
                 "That means it uses the answer key (e.g. c['cwe']) or other per-case information, which is not allowed.")


def run(a):
    all_cases = [json.loads(l) for l in open(a.cases)]    # the guard always looks at ALL cases, even with --limit
    cases = all_cases[:a.limit]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    unknown = [m for m in a.methods if m not in METHODS and m != "self_refine"]
    if unknown: sys.exit(f"Unknown method(s) {unknown}. Available: {list(METHODS) + ['self_refine']}")
    if a.redo and os.path.exists(a.out):  # drop old rows of the methods being re-run (otherwise they are skipped as 'done')
        keep = [l for l in open(a.out) if json.loads(l)["method"] not in a.methods]
        open(a.out, "w").writelines(keep)
    done = set()
    if os.path.exists(a.out):  # resume
        done = {(j["id"], j["method"]) for j in map(json.loads, open(a.out))}
    for m in a.methods:  # fail fast (before loading the model): wrong format, or uses the answer key
        if m in METHODS and cases:
            check_messages(m, METHODS[m](cases[0])); check_case_independent(m, all_cases)
            if m in TWO_STAGE: check_messages(m + "_stage2", TWO_STAGE[m](cases[0], "example first answer"))
    only = {tuple(p) for p in json.load(open(a.only))} if a.only else None
    gen = HFBackend(a.model, a)
    with open(a.out, "a") as f:
        for m in a.methods:
            todo = [c for c in cases if (c["id"], m) not in done and (only is None or (m, c["id"]) in only)]
            if not todo: continue
            t = time.time(); print(f"[{m}] generating {len(todo)} cases ...", flush=True)
            if m in TWO_STAGE:          # student two-stage strategy: stage 2 sees the model's stage-1 answer
                first = gen([METHODS[m](c) for c in todo])
                raws = gen([TWO_STAGE[m](c, f) for c, f in zip(todo, first)])
            elif m == "self_refine":
                msgs = [METHODS["sec_instruct"](c) for c in todo]
                first = gen(msgs)
                msgs = [x + [{"role": "assistant", "content": r}, {"role": "user", "content": REFINE}] for x, r in zip(msgs, first)]
                raws = gen(msgs)
            else:
                raws = gen([METHODS[m](c) for c in todo])
            for c, raw, tr in zip(todo, raws, gen.trunc[-len(raws):]):
                f.write(json.dumps({"id": c["id"], "method": m, "raw": raw, "code": extract(raw), "truncated": tr}) + "\n")
            f.flush()
            print(f"{m:13s} {len(todo)} cases  {time.time()-t:6.1f}s", flush=True)


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    ap.add_argument("--cases", default=os.path.join(HERE, "..", "data", "cases.jsonl"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--temp", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--rep-penalty", type=float, default=1.05)
    ap.add_argument("--only", default=None, help="JSON file of [method, case_id] pairs to run (rerun failures)")
    ap.add_argument("--redo", action="store_true", help="discard existing results of --methods and regenerate them")
    ap.add_argument("--limit", type=int, default=None)
    return ap

if __name__ == "__main__":
    run(parser().parse_args())
