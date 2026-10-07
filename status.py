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
    benefits = read_json("benefits_progress.json", {})
    benefits_failed = read_json("benefits_failed.json", {})
    total = len(rows)
    good = len(progress)
    bad = len(failed)
    remaining = max(0, total - good - bad)
    offers = sum(1 for row in rows if (row.get("offer") or "").strip())
    print("Go Local on a Map status")
    print(f"  Mappable businesses collected: {total}")
    print(f"  Saved/already in list:         {good}")
    print(f"  Unresolved place failures:     {bad}")
    print(f"  Not attempted yet:             {remaining}")
    print(f"  Places with published offers:  {offers}")
    print(f"  Benefit notes verified:        {len(benefits)}")
    print(f"  Benefit-note failures:         {len(benefits_failed)}")
    if bad:
        print("\nRerunning the importer retries place failures and skips successful places.")
    if benefits_failed:
        print("Run 6_UPDATE_BENEFITS.command to retry benefit notes without rebuilding the list.")


if __name__ == "__main__":
    main()
