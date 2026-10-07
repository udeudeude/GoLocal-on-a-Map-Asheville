#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -f ".venv/bin/activate" ]; then
  echo "Run setup.command first."
  read -r -p "Press Return to close..." _
  exit 1
fi
source .venv/bin/activate
python open_maps_browser.py

echo
echo "Sign into Google Maps in the dedicated browser window and leave it open."
echo "Then run 3_TEST_IMPORT.command."
read -r -p "Press Return to close this Terminal window..." _
