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
echo "Leave the dedicated Google Maps browser window open and signed in."
read -r -p "When Maps is ready, press Return to update Go Local benefit notes..." _
python update_benefits.py

echo
python status.py
read -r -p "Press Return to close..." _
