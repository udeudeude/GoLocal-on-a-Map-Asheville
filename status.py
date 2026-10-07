#!/usr/bin/env python3
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_json(name, default):
    p = HERE / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    rows = read_json("golocal_physical.json", [])
    progress = read_json("progress.json", {})
    failed = read_json("failed.json", {})
    total = len(rows)
    good = len(progress)
    bad = len(failed)
    remaining = max(0, total - good - bad)
    print("Go Local on a Map status")
    print(f"  Mappable businesses collected: {total}")
    print(f"  Saved/already in list:         {good}")
    print(f"  Unresolved failures:           {bad}")
    print(f"  Not attempted yet:             {remaining}")
    if bad:
        print("\nRerunning the importer retries failures and skips successful places.")


if __name__ == "__main__":
    main()
