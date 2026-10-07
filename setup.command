#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3, then run this again."
  read -r -p "Press Return to close..." _
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f "config.json" ] && [ -f "config.example.json" ]; then
  cp config.example.json config.json
fi

echo
echo "Setup complete."
echo "Next: double-click 1_COLLECT.command"
read -r -p "Press Return to close..." _
