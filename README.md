# secure-codegen-lab

Lab assignment for a computer-security course: **prompting strategies for secure code generation**.
A small LLM (Qwen3-1.7B) completes Python functions from the SecurityEval benchmark; students design four prompting strategies and the generated code is scored automatically with Bandit. Runs on a free Google Colab T4.

| folder | who | content |
|---|---|---|
| `student/` | **students** | `secure_codegen_lab.ipynb` (Colab notebook) and `README.md` (handout). No answers. |
| `instructor/` | **instructor only** | answer key, solution notebook, reference solutions, reference results, test tools |
| `lab/` | instructor | source of everything in the notebooks, plus `build_notebook.py` to regenerate them |
| `data/cases.jsonl` | | the 21 benchmark cases |

> **This repo contains the answer key and reference solutions. Do not share it with students.** Give them only `student/` (or the student zip).

Instructor: start with `instructor/README.md` and `instructor/ANSWER_KEY.md`. To try the lab, upload `student/secure_codegen_lab.ipynb` (or `instructor/secure_codegen_lab_SOLUTION.ipynb`) to Google Colab, choose a T4 GPU, and run all cells.
