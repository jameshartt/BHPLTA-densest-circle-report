"""Fetch leisure=park / recreation_ground / garden / common polygons for each
UK city.

Writes data/raw/overpass/uk/parks_<rank>_<slug>.json for each city.

Mirrors the strategy of 02_overpass_fetch.py: use each city's resolved OSM
references (relations / ways / bboxes) and pull all park-type polygons inside.
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
TIMEOUT = 180


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


def build_query(osm_refs: list[dict], bbox: tuple | None) -> str:
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

    def emit_block(scope: str) -> str:
        return (
            f'way["leisure"~"^(park|recreation_ground|garden|common|nature_reserve)$"]({scope});\n'
            f'relation["leisure"~"^(park|recreation_ground|garden|common|nature_reserve)$"]({scope});\n'
        )

    parts: list[str] = []
    for a in area_clauses:
        parts.append(emit_block(f"area:{a}"))
    for b in bbox_clauses:
        parts.append(emit_block(b))
    return "[out:json][timeout:180];\n(\n" + "".join(parts) + ");\nout geom;\n"


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only-rank", type=int)
    args = ap.parse_args()

    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    out_dir = OVERPASS_DIR / args.region
    out_dir.mkdir(parents=True, exist_ok=True)

    cities = list(csv.DictReader(cities_csv.open()))
    if args.limit:
        cities = cities[: args.limit]
    if args.only_rank:
        cities = [c for c in cities if int(c["rank"]) == args.only_rank]

    for city in cities:
        rank = int(city["rank"])
        name = city["name"]
        refs = json.loads(city["osm_refs"])
        bbox = None
        if city["bbox_south"]:
            bbox = (float(city["bbox_south"]), float(city["bbox_west"]),
                    float(city["bbox_north"]), float(city["bbox_east"]))
        slug = slugify(name)
        out_path = out_dir / f"parks_{rank:03d}_{slug}.json"

        if out_path.exists() and not args.refresh:
            data = json.loads(out_path.read_text())
            n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
            print(f"[{rank:3d}] {name}: cached ({n_ways} ways)")
            continue

        query = build_query(refs, bbox)
        print(f"[{rank:3d}] {name}: fetching parks ({len(refs)} ref(s))")
        data = fetch_overpass(query)
        out_path.write_text(json.dumps(data))
        n_ways = sum(1 for e in data.get("elements", []) if e["type"] == "way")
        n_rels = sum(1 for e in data.get("elements", []) if e["type"] == "relation")
        print(f"        -> {n_ways} ways, {n_rels} relations")
        time.sleep(SLEEP_BETWEEN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
