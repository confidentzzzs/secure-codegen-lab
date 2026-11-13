"""Rebuild deliverables/*.zip from the current files, then scan the student zip for leaked answers.
Run after `python lab/build_notebook.py` and `python lab/build_notebook.py --solution`:   python instructor/tools/make_zips.py"""
import os, zipfile, nbformat
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); D = f"{R}/deliverables"
os.makedirs(D, exist_ok=True)
for f in os.listdir(D): os.remove(f"{D}/{f}")
def add(z, rel, arc=None): z.write(f"{R}/{rel}", arc or rel)
with zipfile.ZipFile(f"{D}/secure_codegen_lab_STUDENT.zip", "w", zipfile.ZIP_DEFLATED) as z:
    add(z, "student/secure_codegen_lab.ipynb", "secure_codegen_lab/secure_codegen_lab.ipynb")
    add(z, "student/README.md", "secure_codegen_lab/README.md")
inst = ["student/secure_codegen_lab.ipynb", "student/README.md", "instructor/README.md", "instructor/ANSWER_KEY.md",
        "instructor/secure_codegen_lab_SOLUTION.ipynb", "instructor/tools/run_notebook_test.py", "instructor/tools/make_zips.py",
        "instructor/reference/qwen3-1.7b.jsonl", "instructor/reference/qwen3-1.7b.scores.json", "instructor/reference/scores_table.txt",
        "instructor/reference/audit_report.txt", "instructor/reference/cases.jsonl", "data/cases.jsonl"]
inst += [f"instructor/solution/{f}" for f in sorted(os.listdir(f"{R}/instructor/solution"))]
inst += [f"lab/{f}" for f in sorted(os.listdir(f"{R}/lab")) if f.endswith(".py")]
inst += [f"lab/templates/{f}" for f in sorted(os.listdir(f"{R}/lab/templates")) if f.endswith(".py")]
with zipfile.ZipFile(f"{D}/secure_codegen_lab_INSTRUCTOR_with_solution.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for rel in inst: add(z, rel, "secure_codegen_lab_instructor/" + rel)
txt = """secure_codegen_lab: contents of this bundle
1. secure_codegen_lab_STUDENT.zip                  -> give to students (notebook + handout, no answers)
2. secure_codegen_lab_INSTRUCTOR_with_solution.zip -> instructor only. Start with instructor/README.md and instructor/ANSWER_KEY.md
To test: upload the notebook to Google Colab, Runtime > Change runtime type > T4 GPU, run all cells.
Students design four prompting strategies (Step 4 cells) and write answers in the cells titled "YOUR ANSWER". Grading: Task 1 = 4 pts, four strategies x 24 pts.
"""
with zipfile.ZipFile(f"{D}/secure_codegen_lab_ALL.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("README_FIRST.txt", txt)
    for f in ("secure_codegen_lab_STUDENT.zip", "secure_codegen_lab_INSTRUCTOR_with_solution.zip"): z.write(f"{D}/{f}", f)
# ---- verification
st = zipfile.ZipFile(f"{D}/secure_codegen_lab_STUDENT.zip"); ins = zipfile.ZipFile(f"{D}/secure_codegen_lab_INSTRUCTOR_with_solution.zip")
bad = ["senior application-security", "compare_digest", "html.escape", "Security checklist", "SAMPLE ANSWER", "ANSWER_KEY", "FTP_TLS",
       "B310", "61.9", "76.2", "instructor/", "/home/", os.environ.get("USER", "?"), "my_method", "s5_combo", "(15 pts)"]
hits = [(n, b) for n in st.namelist() for b in bad if b in st.read(n).decode("utf8", "ignore")]
print("student zip leak scan:", hits or "none")
for name, zf, p in (("student", st, "secure_codegen_lab/secure_codegen_lab.ipynb"), ("solution", ins, "secure_codegen_lab_instructor/instructor/secure_codegen_lab_SOLUTION.ipynb")):
    nbformat.validate(nbformat.reads(zf.read(p).decode(), as_version=4)); print("valid notebook:", name)
for f in sorted(os.listdir(D)): print(f"{f:55s}{os.path.getsize(D + '/' + f) // 1024:5d} KB")
