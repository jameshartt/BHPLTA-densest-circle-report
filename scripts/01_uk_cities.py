"""Resolve UK city names to OSM boundary relations via Nominatim.

Reads data/raw/uk_cities_raw.tsv and writes data/processed/uk_cities.csv with:
  rank, name, population, search_name, osm_type, osm_id, lat, lon,
  bbox_south, bbox_west, bbox_north, bbox_east, display_name, notes

Conurbations (slash-separated names) are split and resolved to multiple OSM
relations; the city record stores a JSON list of OSM IDs.

Nominatim policy: <= 1 req/sec, descriptive User-Agent. Results cached to
data/raw/nominatim_cache.json so re-runs are free.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CACHE_PATH = RAW / "nominatim_cache.json"
INPUT_TSV = RAW / "uk_cities_raw.tsv"
OUTPUT_CSV = PROCESSED / "uk_cities.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
SLEEP_SECONDS = 1.1

# For conurbations / built-up areas without a single OSM relation, list the
# component areas to Nominatim-resolve. These names are searched as-is.
# Cities that ARE separately ranked in our top-76 are intentionally omitted.
COMPOSITE_AREAS: dict[str, list[str]] = {
    "Tyneside": ["Newcastle upon Tyne", "Gateshead", "North Tyneside", "South Tyneside"],
    "Teesside": ["Middlesbrough", "Stockton-on-Tees", "Redcar and Cleveland", "Hartlepool"],
    "South Hampshire": ["Southampton", "Portsmouth", "Fareham", "Gosport", "Eastleigh", "Havant"],
    "Bournemouth/Poole": ["Bournemouth", "Poole", "Christchurch"],
    "Barnsley/Dearne Valley": ["Barnsley"],
    "Accrington/Rossendale": ["Accrington", "Rossendale"],
    "Torquay/Paignton": ["Torbay"],
    "Farnborough/Aldershot": ["Rushmoor"],
}

# Direct OSM relation overrides — used where Nominatim is ambiguous and we've
# verified the relation exists. These IDs were sanity-checked against real
# Overpass responses.
MANUAL_OVERRIDES: dict[str, list[dict]] = {
    "Greater London": [{"osm_type": "relation", "osm_id": 175342}],
    "Greater Manchester": [{"osm_type": "relation", "osm_id": 88084}],
    "West Midlands": [{"osm_type": "relation", "osm_id": 57516}],
    "West Yorkshire": [{"osm_type": "relation", "osm_id": 88079}],
    "Greater Glasgow": [{"osm_type": "relation", "osm_id": 1906767}],
    "Medway Towns": [{"osm_type": "relation", "osm_id": 158019}],
    "Thanet": [{"osm_type": "relation", "osm_id": 1605596}],
    # Belfast NI has no clean OSM boundary relation; use a hand-crafted bbox
    # covering the Belfast metropolitan urban area.
    "Belfast": [{"osm_type": "bbox", "south": 54.49, "west": -6.10, "north": 54.69, "east": -5.78}],
    # Rushmoor borough covers both Farnborough and Aldershot
    "Rushmoor": [{"osm_type": "relation", "osm_id": 127187}],
    "Basingstoke": [{"osm_type": "relation", "osm_id": 127249, "note": "Basingstoke and Deane borough"}],
    # No clean BUA relation for Motherwell; use North Lanarkshire council area
    # (overcounts vs the BUA boundary -- documented caveat in report)
    "Motherwell": [{"osm_type": "relation", "osm_id": 1920584, "note": "North Lanarkshire UA (BUA proxy)"}],
}


@dataclass
class CityRecord:
    rank: int
    name: str
    population: int
    search_parts: list[str]
    osm_refs: list[dict]
    centroid_lat: float | None
    centroid_lon: float | None
    bbox: list[float] | None  # south, west, north, east
    notes: str


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def split_conurbation(name: str) -> list[str]:
    # If we have an explicit composite mapping for the full name, use it.
    if name in COMPOSITE_AREAS:
        return COMPOSITE_AREAS[name]
    return [p.strip() for p in name.split("/") if p.strip()]


def query_nominatim(name: str, cache: dict) -> dict | None:
    if name in cache:
        return cache[name]
    params = {
        "q": f"{name}, United Kingdom",
        "format": "jsonv2",
        "addressdetails": 0,
        "polygon_geojson": 0,
        "limit": 5,
    }
    headers = {"User-Agent": USER_AGENT}
    print(f"  nominatim: {name!r}")
    r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    results = r.json()
    time.sleep(SLEEP_SECONDS)
    # Prefer results with osm_type=relation and a boundary class
    pick = None
    for res in results:
        if res.get("osm_type") == "relation" and res.get("category") in {
            "boundary",
            "place",
        }:
            pick = res
            break
    if pick is None and results:
        pick = results[0]
    cache[name] = pick
    save_cache(cache)
    return pick


def resolve_one_part(part: str, cache: dict) -> dict | None:
    if part in MANUAL_OVERRIDES:
        overrides = MANUAL_OVERRIDES[part]
        if not overrides:
            return None
        # If override has only osm_type+osm_id, enrich with a Nominatim lookup
        # to grab lat/lon/bbox by reverse query.
        return {"manual": overrides}
    return query_nominatim(part, cache)


def build_record(rank: int, name: str, population: int, cache: dict) -> CityRecord:
    parts = split_conurbation(name)
    refs: list[dict] = []
    notes_bits: list[str] = []
    centroid_lats: list[float] = []
    centroid_lons: list[float] = []
    bboxes: list[list[float]] = []

    for part in parts:
        manual_or_nominatim = resolve_one_part(part, cache)
        if manual_or_nominatim is None:
            notes_bits.append(f"{part}: unresolved")
            continue
        if "manual" in manual_or_nominatim:
            for entry in manual_or_nominatim["manual"]:
                ref = dict(entry)
                ref.setdefault("source", "manual_override")
                ref["search_name"] = part
                refs.append(ref)
                # If override is a bbox, capture bounding box at the city level
                if entry.get("osm_type") == "bbox":
                    bboxes.append([entry["south"], entry["west"], entry["north"], entry["east"]])
                    centroid_lats.append((entry["south"] + entry["north"]) / 2)
                    centroid_lons.append((entry["west"] + entry["east"]) / 2)
        else:
            res = manual_or_nominatim
            ref = {
                "osm_type": res.get("osm_type"),
                "osm_id": int(res.get("osm_id")) if res.get("osm_id") else None,
                "source": "nominatim",
                "search_name": part,
                "display_name": res.get("display_name"),
            }
            refs.append(ref)
            if res.get("lat") and res.get("lon"):
                centroid_lats.append(float(res["lat"]))
                centroid_lons.append(float(res["lon"]))
            bb = res.get("boundingbox")  # [south, north, west, east] as strings
            if bb:
                south, north, west, east = (float(x) for x in bb)
                bboxes.append([south, west, north, east])

    centroid_lat = sum(centroid_lats) / len(centroid_lats) if centroid_lats else None
    centroid_lon = sum(centroid_lons) / len(centroid_lons) if centroid_lons else None
    if bboxes:
        bbox = [
            min(b[0] for b in bboxes),
            min(b[1] for b in bboxes),
            max(b[2] for b in bboxes),
            max(b[3] for b in bboxes),
        ]
    else:
        bbox = None

    return CityRecord(
        rank=rank,
        name=name,
        population=population,
        search_parts=parts,
        osm_refs=refs,
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
        bbox=bbox,
        notes="; ".join(notes_bits),
    )


def main() -> int:
    if not INPUT_TSV.exists():
        print(f"missing input: {INPUT_TSV}", file=sys.stderr)
        return 1
    PROCESSED.mkdir(parents=True, exist_ok=True)
    cache = load_cache()
    records: list[CityRecord] = []

    with INPUT_TSV.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rank = int(row["rank"])
            name = row["name"]
            population = int(row["population"])
            print(f"[{rank:3d}] {name} ({population:,})")
            rec = build_record(rank, name, population, cache)
            records.append(rec)

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "name",
            "population",
            "search_parts",
            "osm_refs",
            "centroid_lat",
            "centroid_lon",
            "bbox_south",
            "bbox_west",
            "bbox_north",
            "bbox_east",
            "notes",
        ])
        for r in records:
            bb = r.bbox or [None, None, None, None]
            writer.writerow([
                r.rank,
                r.name,
                r.population,
                json.dumps(r.search_parts),
                json.dumps(r.osm_refs),
                r.centroid_lat,
                r.centroid_lon,
                bb[0],
                bb[1],
                bb[2],
                bb[3],
                r.notes,
            ])

    print(f"\nwrote {OUTPUT_CSV} with {len(records)} cities")
    unresolved = [r for r in records if not r.osm_refs]
    if unresolved:
        print(f"WARN: {len(unresolved)} unresolved: {[r.name for r in unresolved]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
