#!/usr/bin/env bash
# Build the static site into _site/ (used by CI and for local preview).
#
#   scripts/build-site.sh            # build only
#   scripts/build-site.sh --serve    # build, then serve on http://localhost:8000
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/_site"
marimo="marimo@0.25.2"

rm -rf "$out"
mkdir -p "$out"

# Landing page (if present)
if [ -d "$root/site" ]; then cp -r "$root/site/." "$out/"; fi

# Every notebook in notebooks/ is published as a WebAssembly app.
# Work in progress and anything that can't run in the browser
# (e.g. YOLO: PyTorch, webcam) lives in drafts/ and is not published.
for f in "$root"/notebooks/*.py; do
  name=$(basename "$f" .py)
  # Run from notebooks/ so marimo finds head.html next to the notebook.
  (cd "$root/notebooks" && uvx "$marimo" export html-wasm "$name.py" \
    -o "$out/$name" --mode run)
  # Replace marimo's default icons with ours (same file names).
  cp "$root"/site/favicon.svg "$root"/site/favicon.ico \
     "$root"/site/apple-touch-icon.png "$out/$name/"
done

if [ "${1:-}" = "--serve" ]; then
  echo "Serving $out at http://localhost:8000"
  python3 -m http.server 8000 --directory "$out"
fi
