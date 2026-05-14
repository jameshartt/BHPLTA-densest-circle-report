"""Fetch natural=water polygons (rivers, lakes, docks, harbours) for each UK
and global city. These are subtracted from circle ∩ admin-polygon when
computing the "land" area inside the densest 2.34 km circle — otherwise
cities with major rivers running through them (London / Thames, NYC /
Harlem & East rivers) get a falsely high land denominator because their
admin polygons include the river surface.

Outputs:
  data/raw/overpass/uk/water_{rank:03d}_<slug>.json
  data/raw/overpass/global/water_<slug>.json

Mirrors 13_fetch_parks.py for UK and 16_global_densest.py's fetch loop for
global; cached on disk so subsequent runs skip the Overpass call.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
OVERPASS_DIR = RAW / "overpass"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
SLEEP_BETWEEN = 7.0
MAX_ATTEMPTS = 10
TIMEOUT = 240


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


def fetch_overpass(query: str, attempt: int = 0) -> dict:
    endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
    try:
        r = requests.post(endpoint, data={"data": query},
                          headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if r.status_code == 429 or r.status_code >= 500:
            raise requests.HTTPError(f"{r.status_code} from {endpoint}")
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as e:
        if attempt >= MAX_ATTEMPTS:
            raise
        backoff = min(15 * (2 ** (attempt // len(OVERPASS_ENDPOINTS))), 90)
        print(f"  WARN: {e}; retry {attempt+1}/{MAX_ATTEMPTS} after {backoff}s")
        time.sleep(backoff)
        return fetch_overpass(query, attempt + 1)


def water_block(scope: str) -> str:
    # natural=water covers rivers (with water=river), lakes, docks, harbours.
    # Also pull waterway=riverbank for older mappings.
    return (
        f'way["natural"="water"]({scope});\n'
        f'relation["natural"="water"]({scope});\n'
        f'way["waterway"="riverbank"]({scope});\n'
        f'relation["waterway"="riverbank"]({scope});\n'
    )


def build_uk_query(osm_refs: list[dict], bbox: tuple | None) -> str:
    area_clauses: list[str] = []
    bbox_clauses: list[str] = []
    for ref in osm_refs:
        osm_type = ref.get("osm_type")
        if osm_type == "bbox":
            bbox_clauses.append(
                f'{ref["south"]},{ref["west"]},{ref["north"]},{ref["east"]}')
            continue
        osm_id = ref.get("osm_id")
        if not osm_id:
            continue
        if osm_type == "relation":
            area_clauses.append(str(3_600_000_000 + int(osm_id)))
        elif osm_type == "way":
            area_clauses.append(str(2_400_000_000 + int(osm_id)))
        elif osm_type == "node" and bbox:
            bbox_clauses.append(f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}")
    parts: list[str] = []
    for a in area_clauses:
        parts.append(water_block(f"area:{a}"))
    for b in bbox_clauses:
        parts.append(water_block(b))
    return "[out:json][timeout:240];\n(\n" + "".join(parts) + ");\nout geom;\n"


def fetch_uk() -> None:
    cities_csv = PROCESSED / "uk_cities.csv"
    out_dir = OVERPASS_DIR / "uk"
    out_dir.mkdir(parents=True, exist_ok=True)
    cities = list(csv.DictReader(cities_csv.open()))
    for city in cities:
        rank = int(city["rank"])
        name = city["name"]
        refs = json.loads(city["osm_refs"])
        bbox = None
        if city["bbox_south"]:
            bbox = (float(city["bbox_south"]), float(city["bbox_west"]),
                    float(city["bbox_north"]), float(city["bbox_east"]))
        slug = slugify(name)
        out_path = out_dir / f"water_{rank:03d}_{slug}.json"
        if out_path.exists():
            data = json.loads(out_path.read_text())
            n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
            print(f"[{rank:3d}] {name}: cached ({n_ways} ways)")
            continue
        query = build_uk_query(refs, bbox)
        print(f"[{rank:3d}] {name}: fetching water")
        data = fetch_overpass(query)
        out_path.write_text(json.dumps(data))
        n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
        n_rels = sum(1 for e in data.get("elements", []) if e["type"] == "relation")
        print(f"        -> {n_ways} ways, {n_rels} relations")
        time.sleep(SLEEP_BETWEEN)


def fetch_global() -> None:
    """Fetch water for the curated global CITIES list from 16_global_densest."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib.machinery import SourceFileLoader
    mod = SourceFileLoader("g", str(ROOT / "scripts" / "16_global_densest.py")).load_module()

    out_dir = OVERPASS_DIR / "global"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, country, scope in mod.CITIES:
        slug = slugify(name)
        out_path = out_dir / f"water_{slug}.json"
        if out_path.exists():
            data = json.loads(out_path.read_text())
            n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
            print(f"  {name}: cached ({n_ways} ways)")
            continue
        if isinstance(scope, int):
            scope_clause = f"area:{3_600_000_000 + int(scope)}"
        else:
            s, w, n, e = scope
            scope_clause = f"{s},{w},{n},{e}"
        query = "[out:json][timeout:240];\n(\n" + water_block(scope_clause) + ");\nout geom;\n"
        print(f"  {name}: fetching water")
        data = fetch_overpass(query)
        out_path.write_text(json.dumps(data))
        n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
        n_rels = sum(1 for e in data.get("elements", []) if e["type"] == "relation")
        print(f"    -> {n_ways} ways, {n_rels} relations")
        time.sleep(SLEEP_BETWEEN)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", choices=["uk", "global", "both"], default="both")
    args = ap.parse_args()
    if args.region in ("uk", "both"):
        fetch_uk()
    if args.region in ("global", "both"):
        fetch_global()
    return 0


if __name__ == "__main__":
    sys.exit(main())
