#!/usr/bin/env bash
#
# Run the digest and open it in your browser.
#
#   ./run.sh                        # daily digest -> opens the newspaper page
#   ./run.sh "speculative decoding" # on-demand topic briefing (prints to terminal)
#   ./run.sh --no-open              # generate only, don't open a browser
#
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
OPEN_PAGE=1
TOPIC=""

for arg in "$@"; do
  case "$arg" in
    --no-open) OPEN_PAGE=0 ;;
    -h|--help) sed -n '3,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) TOPIC="$arg" ;;
  esac
done

# --- python env -------------------------------------------------------------
# Find a Python 3. Windows usually has `python` or the `py` launcher rather
# than `python3` (where `python3` is often a Store stub that does nothing).
find_python() {
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info[0] != 3)' >/dev/null 2>&1; then
      echo "$candidate"; return 0
    fi
  done
  if command -v py >/dev/null 2>&1 && py -3 -c '' >/dev/null 2>&1; then
    echo "py -3"; return 0
  fi
  return 1
}

if ! PYTHON="$(find_python)"; then
  echo "ERROR: no Python 3 found on PATH." >&2
  echo "  Install it from https://python.org (tick 'Add Python to PATH')." >&2
  exit 1
fi

if [ ! -d "$VENV" ]; then
  echo "==> Creating virtualenv in $VENV"
  $PYTHON -m venv "$VENV"
fi

# venv puts its activate script in bin/ on Unix, Scripts/ on Windows.
if [ -f "$VENV/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$VENV/bin/activate"
elif [ -f "$VENV/Scripts/activate" ]; then
  # shellcheck disable=SC1091
  . "$VENV/Scripts/activate"
else
  echo "ERROR: couldn't find the activate script in $VENV." >&2
  echo "  Delete the $VENV directory and re-run to rebuild it." >&2
  exit 1
fi

# Reinstall only when requirements.txt is newer than the last install stamp.
STAMP="$VENV/.deps-installed"
if [ ! -f "$STAMP" ] || [ requirements.txt -nt "$STAMP" ]; then
  echo "==> Installing dependencies"
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  touch "$STAMP"
fi

# --- credentials ------------------------------------------------------------
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set." >&2
  echo "  Put it in a .env file (see .env.example) or export it in your shell." >&2
  exit 1
fi

# --- run --------------------------------------------------------------------
if [ -n "$TOPIC" ]; then
  echo "==> Topic briefing: $TOPIC"
  python -m daily_digest.topic_search "$TOPIC"
  # topic_search prints "Wrote <path>" lines; grab the .html one
  PAGE="$(ls -t reports/topic-*.html 2>/dev/null | head -1 || true)"
else
  echo "==> Building today's digest"
  python main.py
  PAGE="docs/index.html"
fi

# --- open -------------------------------------------------------------------
if [ "$OPEN_PAGE" -eq 0 ] || [ -z "${PAGE:-}" ] || [ ! -f "$PAGE" ]; then
  exit 0
fi

# Browsers need an absolute path.
ABS="$(cd "$(dirname "$PAGE")" && pwd)/$(basename "$PAGE")"

if command -v xdg-open >/dev/null 2>&1; then   # Linux
  xdg-open "$ABS" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then      # macOS
  open "$ABS"
elif command -v wslview >/dev/null 2>&1; then   # WSL
  wslview "$ABS"
elif command -v explorer.exe >/dev/null 2>&1; then  # Git Bash / WSL fallback
  explorer.exe "$(cygpath -w "$ABS" 2>/dev/null || echo "$ABS")" || true
else
  echo "==> Open this in your browser: $ABS"
fi
