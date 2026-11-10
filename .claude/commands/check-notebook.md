---
description: Review a marimo notebook before publishing it on the blog (technical, marimo, flow, writing, engagement), with a skeptic pass that verifies every finding
argument-hint: <path-to-notebook.py>
allowed-tools: Read, Glob, Grep, Write, Bash(uv run marimo check:*), Bash(uv run python .claude/scripts/report_to_pdf.py:*), Agent, AskUserQuestion
---

# Check a marimo notebook for publication

Target: `$ARGUMENTS`

You are orchestrating a pre-publication review of a marimo notebook that will be published on a blog. The goal is a notebook that is **informative, engaging and easy to follow**. This is a **report-only** review: **do not edit the notebook or any other file.** The only files you may create are the optional PDF report and its temporary Markdown source (Step 7).

## Audience brief (pass to every agent)

Blog readers: technically curious, comfortable reading some Python, but not necessarily experts in the topic. They read top-to-bottom, may run the notebook themselves, and leave if they get bored or lost.

## Step 1 — Resolve and validate the target

1. Take `$ARGUMENTS`, strip any leading `@` and surrounding whitespace/quotes. If empty, stop and reply: `Usage: /check-notebook @path/to/notebook.py`.
2. If the file doesn't exist, try a Glob for a close match; if still not found, stop with a clear error.
3. Read the file. It must contain `import marimo` and `marimo.App(`. If not, stop and say it isn't a marimo notebook.

## Step 2 — Build the cell index

Number every `@app.cell` (and `@app.function` / `@app.class_definition`) in file order, starting at 1. For each, record:

- cell number and the line number of its decorator
- type: `markdown` (body is essentially a `mo.md(...)` call), `code`, or `mixed`
- whether `hide_code=True`
- a short label: the first heading in the markdown, or the first meaningful line of code

Format it as a compact table. Every agent receives this exact table and must cite cells as `cell N`.

## Step 3 — Run the five reviewers in parallel

Launch these subagents **in a single message** (parallel), using the Agent tool with the given `subagent_type`:

| subagent_type | ID prefix | Focus |
|---|---|---|
| `notebook-technical-reviewer` | T | code correctness and factual accuracy |
| `notebook-marimo-reviewer` | M | marimo best practices and publishability |
| `notebook-flow-reviewer` | F | structure and flow of ideas |
| `notebook-writing-reviewer` | W | prose quality |
| `notebook-engagement-reviewer` | E | reader experience and interactivity |

Each prompt must contain: the absolute notebook path, the cell index, the audience brief, and the line: "Return findings and ideas in the output format defined in your instructions. Do not edit any files."

## Step 4 — Merge

1. Collect all findings. Assign IDs per reviewer in order (`T1, T2…`, `M1…`, `F1…`, `W1…`, `E1…`). Ideas get IDs `I1, I2…` (note which reviewer proposed each).
2. Dedupe: when two findings describe the same problem in the same cell, keep the more specific one and note both areas (e.g. `writing+flow`).
3. Do not re-judge findings yourself yet — that's the skeptic's job.

## Step 5 — Skeptic pass

Launch `notebook-skeptic` with: the notebook path, the cell index, the audience brief, and the full merged list of findings and ideas (with IDs, severity, cell, quote, issue, suggestion). Wait for its verdicts.

## Step 6 — Final report

Apply the skeptic's verdicts: remove `drop` items, apply `adjust` changes (severity / suggestion), keep `keep` items. Then print the report in this shape:

```markdown
# Notebook review: <filename>

**Verdict:** Ready to publish | Minor fixes | Needs work
<2–3 sentence summary of the notebook's state and the most important thing to do next>

## Must fix
- **[cell N · area]** <issue> → <suggested change>
  > <quote, if useful>
  Suggested rewrite: "<rewritten text>" (when relevant)

## Should fix
- ...

## Nice to have
- ...

## What works well
- <3–5 short bullets drawn from the reviewers' strengths notes>

## Ideas & improvements
- **<idea>** (cell N / global) — <why it helps the reader>

<details><summary>Dropped by skeptic (k)</summary>

- `ID` <one-line finding> — <skeptic's reason>
</details>
```

Rules for the report:
- Order items within a section by cell number.
- Omit empty sections, except always include **Verdict** and **What works well**. Include **Ideas & improvements** only if at least one idea survived.
- Verdict: any `must` → "Needs work"; only `should`/`nice` with ≥ 5 `should` → "Minor fixes"; otherwise "Ready to publish" or "Minor fixes" by judgment.
- Keep it scannable: one finding per bullet, concrete suggestions, no generic advice.
- End with one line: the number of findings kept vs. dropped by the skeptic.

## Step 7 — Offer a PDF version

After printing the report, use AskUserQuestion to ask: "Do you want a PDF version of this report?" with the options **Yes, save as PDF** and **No**.

- **No:** stop.
- **Yes:**
  1. Write the exact final report from Step 6 (unchanged Markdown) to a temporary file: `<scratchpad>/<notebook-stem>_report.md` if a scratchpad directory is available, otherwise `/tmp/<notebook-stem>_report.md`.
  2. Convert it, saving the PDF to the `notebook-reports/` directory at the project root:
     `uv run python .claude/scripts/report_to_pdf.py <temp.md> notebook-reports/<notebook-stem>_report.pdf`
     (`<notebook-stem>` is the notebook filename without `.py`, e.g. `neural-network-training_report.pdf`. If that file already exists, overwrite it. The script creates the directory if needed.)
  3. Reply with the path of the saved PDF. If the script fails (e.g. Chrome not found), show its error message and do not retry with other tools.

Do not modify the notebook.
