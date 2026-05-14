"""Refined park-court filter that excludes club courts inside park polygons.

For each court, mark:
  in_park    -- inside a leisure=park/recreation_ground/garden/common polygon
  in_club    -- inside a leisure=sports_centre OR club=tennis polygon

True "public park court" = in_park AND NOT in_club.

Output: data/processed/uk_tennis_facilities_parks_v2.csv with both flags.
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


def build_polygons(data: dict) -> tuple[list, list[str]]:
    polys = []
    names = []
    for el in data.get("elements", []):
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
    out_csv = PROCESSED / f"{args.region}_tennis_facilities_parks_v2.csv"

    cities = {c["name"]: int(c["rank"]) for c in csv.DictReader(cities_csv.open())}
    rows = list(csv.DictReader(facilities_csv.open()))
    by_city = defaultdict(list)
    for r in rows:
        by_city[r["city_name"]].append(r)

    augmented = []
    for city, courts in by_city.items():
        rank = cities.get(city)
        # Park polygons
        park_polys, park_names = [], []
        if rank is not None:
            park_files = list((OVERPASS_DIR / args.region).glob(f"parks_{rank:03d}_*.json"))
            if park_files:
                park_polys, park_names = build_polygons(json.loads(park_files[0].read_text()))
        park_tree = STRtree(park_polys) if park_polys else None
        # Club polygons
        club_polys, club_names = [], []
        if rank is not None:
            club_files = list((OVERPASS_DIR / args.region).glob(f"clubs_{rank:03d}_*.json"))
            if club_files:
                club_polys, club_names = build_polygons(json.loads(club_files[0].read_text()))
        club_tree = STRtree(club_polys) if club_polys else None

        for r in courts:
            r["in_park"] = "0"; r["park_name"] = ""
            r["in_club"] = "0"; r["club_name_match"] = ""
            pt = Point(float(r["lon"]), float(r["lat"]))
            if park_tree:
                for idx in park_tree.query(pt):
                    if park_polys[int(idx)].contains(pt):
                        r["in_park"] = "1"
                        r["park_name"] = park_names[int(idx)]
                        break
            if club_tree:
                for idx in club_tree.query(pt):
                    if club_polys[int(idx)].contains(pt):
                        r["in_club"] = "1"
                        r["club_name_match"] = club_names[int(idx)]
                        break
            r["park_public"] = "1" if (r["in_park"] == "1" and r["in_club"] != "1") else "0"
            augmented.append(r)
        n_courts = sum(1 for r in courts if r["kind"] == "court")
        n_park = sum(1 for r in courts if r["kind"] == "court" and r["in_park"] == "1")
        n_club = sum(1 for r in courts if r["kind"] == "court" and r["in_club"] == "1")
        n_public_park = sum(1 for r in courts if r["kind"] == "court"
                             and r["in_park"] == "1" and r["in_club"] == "0")
        if n_courts:
            print(f"[{rank or '--':>3}] {city:28s}: {n_courts:>5} courts, "
                  f"{n_park:>4} in parks, {n_club:>4} in clubs, "
                  f"{n_public_park:>4} public-park-only")

    fields = list(rows[0].keys()) + ["in_park", "park_name", "in_club",
                                      "club_name_match", "park_public"]
    seen = set()
    fields = [f for f in fields if not (f in seen or seen.add(f))]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in augmented:
            w.writerow(r)
    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
