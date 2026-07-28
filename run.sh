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
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtualenv in $VENV"
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"

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
  exit 0
fi

echo "==> Building today's digest"
python main.py

# --- open -------------------------------------------------------------------
PAGE="docs/index.html"
if [ "$OPEN_PAGE" -eq 0 ] || [ ! -f "$PAGE" ]; then
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
