#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
python import_to_google_maps.py
python update_benefits.py

echo
echo "Import pass finished. Rerunning this file resumes rather than starting over."
python status.py
read -r -p "Press Return to close..." _
