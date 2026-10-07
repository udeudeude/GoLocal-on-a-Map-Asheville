#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -f ".venv/bin/activate" ]; then
  echo "Run setup.command first."
  read -r -p "Press Return to close..." _
  exit 1
fi
source .venv/bin/activate
python collect_golocal.py

echo
echo "Collection complete. Next: double-click 2_OPEN_MAPS_BROWSER.command"
read -r -p "Press Return to close..." _
