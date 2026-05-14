"""Fetch tennis courts/clubs from Overpass API for each resolved UK city.

Reads data/processed/uk_cities.csv and writes:
  - data/raw/overpass/uk/<rank>_<slug>.json  (raw Overpass JSON per city)
  - data/processed/uk_tennis_facilities.csv  (flat one-row-per-element)

Element types collected:
  - leisure=pitch + sport=tennis    -> court
  - leisure=sports_centre + sport=tennis -> sports_centre (counts as a club)
  - club=tennis                      -> tennis_club

Polite usage: 5s sleep between queries. Cached responses are reused unless
--refresh is passed.
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
SLEEP_BETWEEN = 7.0  # seconds between Overpass queries (polite)
TIMEOUT = 180
MAX_ATTEMPTS = 10
DEFAULT_BUFFER_DEG = 0.15  # ~16km when we only have a node centroid


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
    return s


def build_query(osm_refs: list[dict], bbox: tuple | None) -> str:
    """Build Overpass QL query for a city.

    Uses (area:<id>) for each relation ref. If the ref is a node, falls back
    to a bbox buffer around it. If the ref is a way, uses its area too.
    """
    area_clauses: list[str] = []
    bbox_clauses: list[str] = []

    for ref in osm_refs:
        osm_type = ref.get("osm_type")
        if osm_type == "bbox":
            bbox_clauses.append(
                f'{ref["south"]},{ref["west"]},{ref["north"]},{ref["east"]}'
            )
            continue
        osm_id = ref.get("osm_id")
        if not osm_id:
            continue
        if osm_type == "relation":
            area_id = 3_600_000_000 + int(osm_id)
            area_clauses.append(str(area_id))
        elif osm_type == "way":
            # Some boundaries are mapped as ways; area derivation uses 2.4B
            area_id = 2_400_000_000 + int(osm_id)
            area_clauses.append(str(area_id))
        elif osm_type == "node":
            # Use the city CSV bbox if present, else fall back to a small buffer
            if bbox:
                bbox_clauses.append(f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}")

    # We expect either area_clauses or bbox_clauses. Build a union.
    qparts: list[str] = []

    def emit_tag_block(scope: str) -> str:
        return (
            f'node["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'way["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'relation["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'node["leisure"="sports_centre"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'way["leisure"="sports_centre"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'relation["leisure"="sports_centre"]["sport"~"(^|;)tennis(;|$)"]({scope});\n'
            f'node["club"="tennis"]({scope});\n'
            f'way["club"="tennis"]({scope});\n'
            f'relation["club"="tennis"]({scope});\n'
        )

    for area_id in area_clauses:
        qparts.append(emit_tag_block(f"area:{area_id}"))
    for bbox_str in bbox_clauses:
        qparts.append(emit_tag_block(bbox_str))

    body = "".join(qparts)
    return (
        "[out:json][timeout:120];\n"
        "(\n"
        f"{body}"
        ");\n"
        "out center tags;\n"
    )


def fetch_overpass(query: str, attempt: int = 0) -> dict:
    endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.post(
            endpoint,
            data={"data": query},
            headers=headers,
            timeout=TIMEOUT,
        )
        if r.status_code == 429 or r.status_code >= 500:
            raise requests.HTTPError(f"{r.status_code} from {endpoint}")
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as e:
        if attempt >= MAX_ATTEMPTS:
            raise
        # Exponential backoff capped at 90s
        backoff = min(15 * (2 ** (attempt // len(OVERPASS_ENDPOINTS))), 90)
        print(f"  WARN: {e}; retry {attempt + 1}/{MAX_ATTEMPTS} after {backoff}s")
        time.sleep(backoff)
        return fetch_overpass(query, attempt + 1)


def classify_element(tags: dict) -> str:
    leisure = tags.get("leisure")
    if tags.get("club") == "tennis":
        return "tennis_club"
    if leisure == "sports_centre":
        return "sports_centre"
    if leisure == "pitch":
        return "court"
    return "other"


def flatten_elements(data: dict, city_rank: int, city_name: str) -> list[dict]:
    rows: list[dict] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        if "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        rows.append({
            "city_rank": city_rank,
            "city_name": city_name,
            "osm_type": el.get("type"),
            "osm_id": el.get("id"),
            "lat": lat,
            "lon": lon,
            "kind": classify_element(tags),
            "leisure": tags.get("leisure", ""),
            "sport": tags.get("sport", ""),
            "club": tags.get("club", ""),
            "access": tags.get("access", ""),
            "name": tags.get("name", ""),
            "operator": tags.get("operator", ""),
            "tennis_courts_tag": tags.get("tennis:courts", "") or tags.get("courts", ""),
            "surface": tags.get("surface", ""),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    ap.add_argument("--refresh", action="store_true", help="ignore cached responses")
    ap.add_argument("--limit", type=int, help="only process first N cities (testing)")
    ap.add_argument("--only-rank", type=int, help="only fetch this rank (testing)")
    args = ap.parse_args()

    if args.region != "uk":
        print(f"region {args.region!r} not yet supported", file=sys.stderr)
        return 1

    cities_csv = PROCESSED / "uk_cities.csv"
    if not cities_csv.exists():
        print(f"missing {cities_csv}; run scripts/01_uk_cities.py first", file=sys.stderr)
        return 1

    out_dir = OVERPASS_DIR / args.region
    out_dir.mkdir(parents=True, exist_ok=True)
    flat_csv = PROCESSED / "uk_tennis_facilities.csv"

    all_rows: list[dict] = []
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
            bbox = (
                float(city["bbox_south"]),
                float(city["bbox_west"]),
                float(city["bbox_north"]),
                float(city["bbox_east"]),
            )

        slug = slugify(name)
        out_path = out_dir / f"{rank:03d}_{slug}.json"

        if out_path.exists() and not args.refresh:
            print(f"[{rank:3d}] {name}: cached")
            data = json.loads(out_path.read_text())
        else:
            query = build_query(refs, bbox)
            print(f"[{rank:3d}] {name}: fetching ({len(refs)} ref(s))")
            data = fetch_overpass(query)
            out_path.write_text(json.dumps(data))
            time.sleep(SLEEP_BETWEEN)

        rows = flatten_elements(data, rank, name)
        all_rows.extend(rows)
        print(f"        -> {len(rows)} elements")

    # Write flat CSV (overwrite when run over all cities; otherwise append-safe-ish)
    fieldnames = [
        "city_rank",
        "city_name",
        "osm_type",
        "osm_id",
        "lat",
        "lon",
        "kind",
        "leisure",
        "sport",
        "club",
        "access",
        "name",
        "operator",
        "tennis_courts_tag",
        "surface",
    ]
    with flat_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"\nwrote {flat_csv} with {len(all_rows)} elements across {len(cities)} cities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
