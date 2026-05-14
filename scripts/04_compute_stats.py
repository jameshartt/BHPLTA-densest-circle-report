"""Join cities, clubs, courts and compute per-100k statistics.

Reads:
  data/processed/uk_cities.csv
  data/processed/uk_clubs.csv

Writes:
  data/processed/uk_stats.csv  -- one row per city with totals + per-100k
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    clubs_csv = PROCESSED / f"{args.region}_clubs.csv"
    out_csv = PROCESSED / f"{args.region}_stats.csv"

    if not cities_csv.exists() or not clubs_csv.exists():
        print("missing inputs; run earlier scripts first", file=sys.stderr)
        return 1

    cities = {int(r["rank"]): r for r in csv.DictReader(cities_csv.open())}
    clubs = list(csv.DictReader(clubs_csv.open()))

    # Aggregate per city
    by_city: dict[int, dict] = defaultdict(lambda: {
        "total_clubs": 0,
        "total_courts": 0,
        "public_clubs": 0,
        "public_courts": 0,
        "members_clubs": 0,
        "members_courts": 0,
        "private_clubs": 0,
        "private_courts": 0,
    })

    for c in clubs:
        rank = int(c["city_rank"])
        court_count = int(c["court_count"])
        access = c["primary_access"]
        members = int(c["members_only"])
        agg = by_city[rank]

        if access == "private":
            agg["private_clubs"] += 1
            agg["private_courts"] += court_count
            continue
        if members or access == "members":
            agg["members_clubs"] += 1
            agg["members_courts"] += court_count
            continue
        # public/customers/yes/permissive/unknown -> counted as primary stat
        agg["public_clubs"] += 1
        agg["public_courts"] += court_count
        agg["total_clubs"] += 1
        agg["total_courts"] += court_count

    rows: list[dict] = []
    for rank, city in sorted(cities.items()):
        agg = by_city.get(rank, {})
        pop = int(city["population"])
        clubs_n = agg.get("total_clubs", 0)
        courts_n = agg.get("total_courts", 0)
        rows.append({
            "rank": rank,
            "name": city["name"],
            "population": pop,
            "courts": courts_n,
            "clubs": clubs_n,
            "courts_per_100k": round(courts_n / pop * 100_000, 2) if pop else 0,
            "clubs_per_100k": round(clubs_n / pop * 100_000, 2) if pop else 0,
            "public_clubs": agg.get("public_clubs", 0),
            "public_courts": agg.get("public_courts", 0),
            "members_clubs": agg.get("members_clubs", 0),
            "members_courts": agg.get("members_courts", 0),
            "private_clubs": agg.get("private_clubs", 0),
            "private_courts": agg.get("private_courts", 0),
        })

    fieldnames = list(rows[0].keys()) if rows else []
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"wrote {out_csv} with {len(rows)} cities")

    # Print top 10 by courts/100k for sanity
    ranked = sorted(rows, key=lambda r: -r["courts_per_100k"])
    print("\nTop 10 cities by courts per 100k:")
    print(f"  {'rank':>4}  {'city':<26}  {'pop':>10}  {'courts':>7}  {'clubs':>6}  {'c/100k':>7}  {'cl/100k':>7}")
    for r in ranked[:10]:
        print(f"  {r['rank']:>4}  {r['name'][:26]:<26}  {r['population']:>10,}  "
              f"{r['courts']:>7}  {r['clubs']:>6}  {r['courts_per_100k']:>7.2f}  {r['clubs_per_100k']:>7.2f}")

    print("\nBottom 10 cities by courts per 100k:")
    for r in ranked[-10:][::-1]:
        print(f"  {r['rank']:>4}  {r['name'][:26]:<26}  {r['population']:>10,}  "
              f"{r['courts']:>7}  {r['clubs']:>6}  {r['courts_per_100k']:>7.2f}  {r['clubs_per_100k']:>7.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
