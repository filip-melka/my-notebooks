"""Convert a /check-notebook Markdown report into a styled PDF.

Usage: uv run python .claude/scripts/report_to_pdf.py <report.md> <output.pdf>

Renders Markdown -> HTML with python-markdown, then prints it to PDF with
headless Google Chrome (macOS default path, or $CHROME_PATH).
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.45; color: #1d1d1f; }
h1 { font-size: 20pt; margin: 0 0 6pt; border-bottom: 2px solid #1d1d1f; padding-bottom: 4pt; }
h2 { font-size: 13.5pt; margin: 16pt 0 6pt; padding-bottom: 2pt; border-bottom: 1px solid #d2d2d7; }
h2.must { color: #b3261e; } h2.should { color: #9a5b00; } h2.nice { color: #1d6b3a; }
ul { padding-left: 16pt; } li { margin: 0 0 5pt; break-inside: avoid; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 9pt;
       background: #f2f2f5; padding: 0 2pt; border-radius: 3px; }
blockquote { margin: 3pt 0; padding: 2pt 8pt; border-left: 3px solid #d2d2d7; color: #555; }
details { margin-top: 14pt; color: #555; } summary { font-weight: 600; margin-bottom: 4pt; }
p.meta { color: #666; font-size: 9pt; }
"""

CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome"),
    shutil.which("chromium"),
]


def render_html(md_text: str) -> str:
    # print collapsed sections expanded, and let markdown render inside them
    md_text = re.sub(r"<details>", '<details open markdown="1">', md_text)
    # python-markdown needs 4-space indents for nested list content (quotes, paragraphs)
    md_text = re.sub(r"^ {2}(?=\S)", "    ", md_text, flags=re.M)
    # ...and blank lines before a nested quote and before an item that follows nested content
    lines, prev = [], ""
    for line in md_text.splitlines():
        nested_quote = line.lstrip().startswith(">") and line.startswith(" ")
        if prev.strip() and (
            (nested_quote and not prev.lstrip().startswith(">"))
            or (line.startswith("- ") and prev.startswith(" "))
        ):
            lines.append("")
        lines.append(line)
        prev = line
    md_text = "\n".join(lines)
    body = markdown.markdown(
        md_text, extensions=["tables", "fenced_code", "md_in_html", "sane_lists"]
    )
    for level in ("Must", "Should", "Nice"):
        body = body.replace(f"<h2>{level}", f'<h2 class="{level.lower()}">{level}')
    title = re.search(r"^# (.+)$", md_text, re.M)
    title = title.group(1) if title else "Notebook review"
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>'
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
    if not chrome:
        sys.exit("Chrome/Chromium not found; set CHROME_PATH.")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "report.html"
        html.write_text(render_html(src.read_text()), encoding="utf-8")
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={out}", html.as_uri()],
            check=True, capture_output=True,
        )
    print(out)


if __name__ == "__main__":
    main()
