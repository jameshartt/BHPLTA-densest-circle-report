"""Fetch admin-boundary polygons for every city used in the densest-circle
analysis (UK + global). These are used as 'land masks' so circles drawn over
coastal cities aren't credited for square kilometres of sea.

Outputs:
  data/raw/overpass/uk/boundary_<rank>_<slug>.json
  data/raw/overpass/global/boundary_<slug>.json
"""

from __future__ import annotations

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

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
SLEEP_BETWEEN = 6.0
TIMEOUT = 180

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


def slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


def post_overpass(query: str, attempt: int = 0) -> dict:
    endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
    try:
        r = requests.post(endpoint, data={"data": query},
                          headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if r.status_code == 429 or r.status_code >= 500:
            raise requests.HTTPError(f"{r.status_code} from {endpoint}")
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as e:
        if attempt >= 8:
            raise
        backoff = min(15 * (2 ** (attempt // len(OVERPASS_ENDPOINTS))), 90)
        print(f"  WARN: {e}; retry in {backoff}s")
        time.sleep(backoff)
        return post_overpass(query, attempt + 1)


def fetch_relation(rel_id: int) -> dict:
    q = f"[out:json][timeout:180];relation({rel_id});out geom;"
    return post_overpass(q)


def fetch_uk_boundaries() -> None:
    out_dir = RAW / "overpass" / "uk"
    cities_csv = PROCESSED / "uk_cities.csv"
    cities = list(csv.DictReader(cities_csv.open()))
    for c in cities:
        rank = int(c["rank"])
        refs = json.loads(c["osm_refs"])
        relation_ids = [r.get("osm_id") for r in refs
                        if r.get("osm_type") == "relation" and r.get("osm_id")]
        if not relation_ids:
            # bbox or way-based — skip; we'll fall back to bbox
            print(f"[{rank:3d}] {c['name']}: no relation refs, skipping (bbox fallback)")
            continue
        out_path = out_dir / f"boundary_{rank:03d}_{slug(c['name'])}.json"
        if out_path.exists():
            print(f"[{rank:3d}] {c['name']}: cached")
            continue
        try:
            # Merge multiple relations into one query
            ids_str = "\n  ".join(f"relation({rid});" for rid in relation_ids)
            q = f"[out:json][timeout:180];({ids_str});out geom;"
            data = post_overpass(q)
            out_path.write_text(json.dumps(data))
            print(f"[{rank:3d}] {c['name']}: fetched ({len(relation_ids)} relations)")
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[{rank:3d}] {c['name']}: FAILED {e}")


def fetch_global_boundaries() -> None:
    out_dir = RAW / "overpass" / "global"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Import CITIES from 16_global_densest.py
    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib.machinery import SourceFileLoader
    mod = SourceFileLoader("g", str(ROOT / "scripts" / "16_global_densest.py")).load_module()
    for name, country, scope in mod.CITIES:
        if not isinstance(scope, int):
            print(f"[--] {name}: bbox scope, skipping (no boundary polygon)")
            continue
        out_path = out_dir / f"boundary_{slug(name)}.json"
        if out_path.exists():
            print(f"[--] {name}: cached")
            continue
        try:
            data = fetch_relation(scope)
            out_path.write_text(json.dumps(data))
            print(f"[--] {name}: fetched")
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[--] {name}: FAILED {e}")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="both", choices=["uk", "global", "both"])
    args = ap.parse_args()
    if args.region in ("uk", "both"):
        fetch_uk_boundaries()
    if args.region in ("global", "both"):
        fetch_global_boundaries()
    return 0


if __name__ == "__main__":
    sys.exit(main())
