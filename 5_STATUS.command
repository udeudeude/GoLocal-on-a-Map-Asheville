#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
python status.py
read -r -p "Press Return to close..." _
