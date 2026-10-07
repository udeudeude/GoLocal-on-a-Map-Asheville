#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
LIMIT=$(python - <<'PY'
from golocal_common import load_config
print(int(load_config().get('test_limit', 5)))
PY
)
python import_to_google_maps.py --limit "$LIMIT"

echo
echo "Test run finished. Check Google Maps: Saved/You > Go Local Card."
echo "If the places look right, run 4_IMPORT_ALL.command."
read -r -p "Press Return to close..." _
