"""Derive a fallback bbox for every city from its cached OSM tennis features.

For composite / manual-override cities, Nominatim never populated bbox in
data/processed/uk_cities.csv. We backfill those rows with the bbox of all
mapped tennis features in that city's cached Overpass response, expanded by
a small buffer so peri-urban LSOAs get included.

Modifies data/processed/uk_cities.csv in place.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_OVERPASS = ROOT / "data" / "raw" / "overpass" / "uk"

BUFFER_DEG = 0.02  # ~2 km north-south, ~1.3 km east-west (approx)


def main() -> int:
    cities_csv = PROCESSED / "uk_cities.csv"
    rows = list(csv.DictReader(cities_csv.open()))
    updated = 0

    for row in rows:
        if row["bbox_south"]:
            continue
        rank = int(row["rank"])
        # Find cached overpass file
        files = sorted(RAW_OVERPASS.glob(f"{rank:03d}_*.json"))
        if not files:
            continue
        data = json.loads(files[0].read_text())
        lats: list[float] = []
        lons: list[float] = []
        for el in data.get("elements", []):
            if "lat" in el:
                lats.append(el["lat"])
                lons.append(el["lon"])
            elif "center" in el:
                lats.append(el["center"]["lat"])
                lons.append(el["center"]["lon"])
        if not lats:
            continue
        row["bbox_south"] = f"{min(lats) - BUFFER_DEG:.6f}"
        row["bbox_north"] = f"{max(lats) + BUFFER_DEG:.6f}"
        row["bbox_west"] = f"{min(lons) - BUFFER_DEG:.6f}"
        row["bbox_east"] = f"{max(lons) + BUFFER_DEG:.6f}"
        if not row["centroid_lat"]:
            row["centroid_lat"] = f"{sum(lats) / len(lats):.6f}"
            row["centroid_lon"] = f"{sum(lons) / len(lons):.6f}"
        updated += 1
        print(f"backfilled bbox for {row['name']} ({len(lats)} courts)")

    fields = list(rows[0].keys())
    with cities_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"\nupdated {updated} city rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
