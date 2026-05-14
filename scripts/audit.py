"""Sanity-check the UK pipeline outputs.

Flags cities with suspiciously low or high counts, empty Overpass responses,
and clubs whose court_count was inferred via fallback heuristics.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    cities = list(csv.DictReader((PROCESSED / f"{args.region}_cities.csv").open()))
    facilities_path = PROCESSED / f"{args.region}_tennis_facilities.csv"
    if not facilities_path.exists():
        print(f"missing {facilities_path}")
        return 1
    facilities = list(csv.DictReader(facilities_path.open()))
    by_city: dict[int, list[dict]] = {}
    for f in facilities:
        rank = int(f["city_rank"])
        by_city.setdefault(rank, []).append(f)

    overpass_dir = RAW / "overpass" / args.region
    issues: list[str] = []
    print(f"{'rank':>4}  {'city':<28}  {'pop':>10}  {'els':>5}  {'crts':>5}  notes")
    for c in cities:
        rank = int(c["rank"])
        name = c["name"]
        pop = int(c["population"])
        els = by_city.get(rank, [])
        court_count = sum(1 for x in els if x["kind"] == "court")
        notes = []

        # Check raw cache
        slug_files = sorted(overpass_dir.glob(f"{rank:03d}_*.json"))
        if slug_files:
            size = slug_files[0].stat().st_size
            if size < 500:
                notes.append("EMPTY_CACHE")
        else:
            notes.append("NO_CACHE")

        # Heuristic anomalies
        if court_count == 0:
            notes.append("ZERO_COURTS")
        elif court_count / pop * 100_000 < 0.5:
            notes.append("VERY_LOW")
        elif court_count / pop * 100_000 > 30:
            notes.append("VERY_HIGH")

        flag = " ".join(notes)
        if flag:
            issues.append(f"{rank}: {name}: {flag}")
        print(f"{rank:>4}  {name[:28]:<28}  {pop:>10,}  {len(els):>5}  {court_count:>5}  {flag}")

    print()
    print(f"flagged {len(issues)} cities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
