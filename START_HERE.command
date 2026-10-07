#!/bin/bash
set -e
cd "$(dirname "$0")"

printf '\nGo Local on a Map: Asheville\n'
printf '================================\n\n'
echo "This will build a normal Google Maps Saved list from the current Go Local Asheville directory."
echo "It will also add each published Go Local benefit as a note on that saved place."
echo "It uses a separate Brave/Chrome profile and never asks for your Google password."
printf '\n'

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3, then run this launcher again."
  read -r -p "Press Return to close..." _
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "First-run setup..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

if [ ! -f "config.json" ]; then
  cp config.example.json config.json
fi

python - <<'PY'
from golocal_common import find_browser
name, path = find_browser()
if not path:
    raise SystemExit("Brave Browser or Google Chrome was not found. Install one and run this again.")
print(f"Browser found: {name}")
PY

if [ -f "golocal_physical.json" ]; then
  read -r -p "Existing Go Local directory data found. Refresh it now? [y/N] " REFRESH
else
  REFRESH="y"
fi

case "$REFRESH" in
  y|Y|yes|YES)
    echo
    python collect_golocal.py
    ;;
  *)
    echo "Using the existing collected directory data."
    ;;
esac

echo
python open_maps_browser.py
echo
read -r -p "Sign into Google Maps in that dedicated browser window. When Maps is ready, press Return here..." _

echo
LIMIT=$(python - <<'PY'
from golocal_common import load_config
print(int(load_config().get('test_limit', 5)))
PY
)
echo "Running a ${LIMIT}-place test, including benefit notes..."
python import_to_google_maps.py --limit "$LIMIT"
python update_benefits.py --limit "$LIMIT"

echo
python status.py
echo
read -r -p "Check the Go Local Card list in Google Maps. Do the test places and benefit notes look correct? [y/N] " CONTINUE
case "$CONTINUE" in
  y|Y|yes|YES)
    echo
    echo "Starting the full import. You can stop it and rerun later; progress is saved after every place."
    python import_to_google_maps.py
    python update_benefits.py
    echo
    python status.py
    ;;
  *)
    echo
    echo "Stopped after the test. Nothing else will be changed."
    echo "When ready, run 4_IMPORT_ALL.command to continue."
    ;;
esac

echo
read -r -p "Press Return to close..." _
