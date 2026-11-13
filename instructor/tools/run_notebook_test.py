"""Execute a lab notebook the way Colab would, in a fresh work directory, and report failures.
Handles `%%writefile` cells, `!shell` lines (mixed with python in one cell) and plain python cells.

Usage (needs torch, transformers, bandit and a GPU):
    python run_notebook_test.py <notebook.ipynb> <empty_work_dir>
Exit code 0 only if no cell failed.  "/content/lab_work" in the notebook is replaced by <work_dir>.
"""
import json, os, subprocess, sys, time, traceback

nb_path, work = sys.argv[1], os.path.abspath(sys.argv[2])
os.makedirs(work, exist_ok=True)
nb = json.load(open(nb_path)); ns = {"__name__": "__main__"}; bad = 0
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"]).replace("/content/lab_work", work)
    t = time.time(); print(f"\n##### cell {i}: {src.splitlines()[0][:70]}", flush=True)
    if src.startswith("%%writefile"):
        head, _, body = src.partition("\n"); path = head.split(None, 1)[1].strip()
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        open(path, "w").write(body + "\n"); print(f"wrote {path} ({len(body)} chars)"); continue
    buf = []

    def flush_py():
        global bad
        if not buf:
            return
        try:
            exec(compile("\n".join(buf), f"cell{i}", "exec"), ns)
        except BaseException:
            bad += 1; print(f"!!!! cell {i} raised:"); traceback.print_exc()
        buf.clear()

    for line in src.splitlines():          # IPython semantics: '!' = shell, the rest = python, kept in order
        if line.startswith("!"):
            flush_py()
            r = subprocess.run(line[1:], shell=True)
            if r.returncode:
                bad += 1; print(f"!!!! cell {i} command failed (rc={r.returncode}): {line}", flush=True)
        else:
            buf.append(line)
    flush_py()
    print(f"({time.time()-t:.0f}s)", flush=True)
print(f"\nNOTEBOOK DONE, failures: {bad}")
sys.exit(1 if bad else 0)
