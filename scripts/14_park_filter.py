"""Augment uk_tennis_facilities.csv with an `in_park` flag and `park_name`
column based on spatial intersection with leisure=park/recreation_ground/
garden/common polygons fetched by scripts/13_fetch_parks.py.

Output: data/processed/uk_tennis_facilities_parks.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OVERPASS_DIR = ROOT / "data" / "raw" / "overpass"


def build_polygons_for_city(parks_json: dict) -> tuple[list, list[str]]:
    """Build park polygons from OSM. Invalid polygons (self-intersections,
    common in OSM) are repaired with shapely's buffer(0) so they're not
    silently dropped — without this, Step 3 misses parks that Step 4's
    24_park_filter_v2.py recovers, producing the apparent paradox of
    Step 4 having more park courts than Step 3 (LA, Auckland, Chicago,
    Greater London)."""
    polys = []
    names = []
    for el in parks_json.get("elements", []):
        if el["type"] == "way" and "geometry" in el:
            coords = [(n["lon"], n["lat"]) for n in el["geometry"]]
            if len(coords) >= 4:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                try:
                    p = Polygon(coords)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.is_valid and p.area > 0:
                        polys.append(p)
                        names.append(el.get("tags", {}).get("name", ""))
                except Exception:
                    pass
        elif el["type"] == "relation" and "members" in el:
            outers = []
            for m in el["members"]:
                if m.get("role") == "outer" and "geometry" in m:
                    coords = [(n["lon"], n["lat"]) for n in m["geometry"]]
                    if len(coords) >= 4:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        outers.append(coords)
            if outers:
                try:
                    mp = MultiPolygon([Polygon(o) for o in outers])
                    if not mp.is_valid:
                        mp = mp.buffer(0)
                    if mp.is_valid and mp.area > 0:
                        polys.append(mp)
                        names.append(el.get("tags", {}).get("name", ""))
                except Exception:
                    pass
    return polys, names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    facilities_csv = PROCESSED / f"{args.region}_tennis_facilities.csv"
    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    out_csv = PROCESSED / f"{args.region}_tennis_facilities_parks.csv"

    cities = {c["name"]: int(c["rank"])
              for c in csv.DictReader(cities_csv.open())}

    # Group courts by city
    rows = list(csv.DictReader(facilities_csv.open()))
    courts_by_city: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        courts_by_city[r["city_name"]].append(r)

    augmented = []
    for city, courts in courts_by_city.items():
        rank = cities.get(city)
        if rank is None:
            for r in courts:
                r["in_park"] = "0"
                r["park_name"] = ""
                augmented.append(r)
            continue
        # Find parks JSON
        candidates = list((OVERPASS_DIR / args.region).glob(f"parks_{rank:03d}_*.json"))
        if not candidates:
            print(f"warn: no parks cache for {city} (rank {rank})")
            for r in courts:
                r["in_park"] = "0"
                r["park_name"] = ""
                augmented.append(r)
            continue
        data = json.loads(candidates[0].read_text())
        polys, names = build_polygons_for_city(data)
        if not polys:
            for r in courts:
                r["in_park"] = "0"
                r["park_name"] = ""
                augmented.append(r)
            continue
        tree = STRtree(polys)
        in_park_n = 0
        for r in courts:
            pt = Point(float(r["lon"]), float(r["lat"]))
            hits = tree.query(pt)
            r["in_park"] = "0"
            r["park_name"] = ""
            for idx in hits:
                if polys[int(idx)].contains(pt):
                    r["in_park"] = "1"
                    r["park_name"] = names[int(idx)]
                    in_park_n += 1
                    break
            augmented.append(r)
        n_courts = sum(1 for r in courts if r["kind"] == "court")
        n_park_courts = sum(1 for r in courts if r["kind"] == "court" and r["in_park"] == "1")
        print(f"[{rank:3d}] {city:28s}: {n_courts:>5} courts, {n_park_courts:>5} in parks "
              f"({n_park_courts/n_courts*100:.0f}% park-rate)" if n_courts else f"[{rank:3d}] {city}: 0 courts")

    fields = list(rows[0].keys()) + ["in_park", "park_name"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in augmented:
            w.writerow(r)
    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
