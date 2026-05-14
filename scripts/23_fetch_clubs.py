"""Fetch club/sports-centre POLYGONS for every city so we can exclude club
courts that sit physically inside a park polygon (e.g. Roland Garros inside
the Bois de Boulogne).

We fetch:
  leisure=sports_centre  (ways + relations, with geometry)
  club=tennis            (ways + relations, with geometry)

Output:
  data/raw/overpass/uk/clubs_<rank>_<slug>.json
  data/raw/overpass/global/clubs_<slug>.json
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


def build_query(scope: str) -> str:
    return f"""[out:json][timeout:180];
(
  way["leisure"="sports_centre"]({scope});
  relation["leisure"="sports_centre"]({scope});
  way["club"="tennis"]({scope});
  relation["club"="tennis"]({scope});
);
out geom;
"""


def fetch_uk():
    out_dir = RAW / "overpass" / "uk"
    cities_csv = PROCESSED / "uk_cities.csv"
    for c in csv.DictReader(cities_csv.open()):
        rank = int(c["rank"])
        refs = json.loads(c["osm_refs"])
        out_path = out_dir / f"clubs_{rank:03d}_{slug(c['name'])}.json"
        if out_path.exists():
            print(f"[{rank:3d}] {c['name']}: cached")
            continue
        scopes = []
        for r in refs:
            t = r.get("osm_type")
            if t == "relation":
                scopes.append(f"area:{3_600_000_000 + int(r['osm_id'])}")
            elif t == "way":
                scopes.append(f"area:{2_400_000_000 + int(r['osm_id'])}")
            elif t == "bbox":
                scopes.append(f"{r['south']},{r['west']},{r['north']},{r['east']}")
        if not scopes:
            print(f"[{rank:3d}] {c['name']}: no scope, skipping")
            continue
        parts = []
        for s in scopes:
            parts.append(
                f'way["leisure"="sports_centre"]({s});'
                f'relation["leisure"="sports_centre"]({s});'
                f'way["club"="tennis"]({s});'
                f'relation["club"="tennis"]({s});'
            )
        q = "[out:json][timeout:180];\n(\n" + "\n".join(parts) + "\n);\nout geom;\n"
        try:
            data = post_overpass(q)
            out_path.write_text(json.dumps(data))
            els = data.get("elements", [])
            n_w = sum(1 for e in els if e["type"] == "way")
            n_r = sum(1 for e in els if e["type"] == "relation")
            print(f"[{rank:3d}] {c['name']}: {n_w} ways, {n_r} rels")
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[{rank:3d}] {c['name']}: FAILED {e}")


def fetch_global():
    out_dir = RAW / "overpass" / "global"
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib.machinery import SourceFileLoader
    mod = SourceFileLoader("g", str(ROOT / "scripts" / "16_global_densest.py")).load_module()
    for name, country, scope in mod.CITIES:
        out_path = out_dir / f"clubs_{slug(name)}.json"
        if out_path.exists():
            print(f"[--] {name}: cached")
            continue
        if isinstance(scope, int):
            sc = f"area:{3_600_000_000 + scope}"
        else:
            s, w, n, e = scope
            sc = f"{s},{w},{n},{e}"
        q = build_query(sc)
        try:
            data = post_overpass(q)
            out_path.write_text(json.dumps(data))
            els = data.get("elements", [])
            n_w = sum(1 for e in els if e["type"] == "way")
            n_r = sum(1 for e in els if e["type"] == "relation")
            print(f"[--] {name}: {n_w} ways, {n_r} rels")
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[--] {name}: FAILED {e}")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="both", choices=["uk", "global", "both"])
    args = ap.parse_args()
    if args.region in ("uk", "both"):
        fetch_uk()
    if args.region in ("global", "both"):
        fetch_global()
    return 0


if __name__ == "__main__":
    sys.exit(main())
