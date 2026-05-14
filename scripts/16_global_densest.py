"""Densest tennis-court circle: GLOBAL comparison.

For a curated list of tennis-rich world cities, fetch OSM tennis courts and
park polygons, spatial-join, then find the densest 2.26 km circle of park
courts in each. Compare against Brighton.

Output: data/processed/global_densest_circle.csv

Cities chosen for plausibility of beating Brighton on park-court density:
- Paris (Bois de Boulogne / Buttes-Chaumont)
- Madrid (Casa de Campo)
- Barcelona
- Berlin (Tiergarten and others)
- Munich
- Vienna (Prater)
- Amsterdam
- Copenhagen
- Stockholm
- Buenos Aires (Palermo)
- Tokyo (multiple parks)
- Seoul
- Melbourne (Melbourne Park)
- Sydney (Centennial Park / Sydney Olympic Park)
- New York City (Central Park / Flushing Meadows)
- Boston
- San Francisco (Golden Gate Park)
- Toronto
- Auckland
- Wellington
- Cape Town
- Hong Kong
- Singapore

Each city's OSM relation ID is resolved via Nominatim (cached) and used to
scope Overpass queries.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
GLOBAL_DIR = RAW / "overpass" / "global"
GLOBAL_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
SLEEP_BETWEEN = 7.0
TIMEOUT = 240
MAX_ATTEMPTS = 8

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Curated list. Each entry: (name, country, scope) where scope is either an
# int OSM relation id, or a (south, west, north, east) bbox tuple.
CITIES = [
    ("Paris",            "FR", 7444),
    ("Madrid",           "ES", 5326784),
    ("Barcelona",        "ES", 347950),
    ("Berlin",           "DE", 62422),
    ("Munich",           "DE", 62428),
    ("Vienna",           "AT", 109166),
    ("Amsterdam",        "NL", 271110),
    ("Copenhagen",       "DK", 2192363),
    ("Stockholm",        "SE", 398021),
    ("Helsinki",         "FI", 34914),
    ("Oslo",             "NO", 406091),
    ("Buenos Aires",     "AR", 1224652),
    ("Tokyo (23 wards)", "JP", (35.50, 139.55, 35.85, 139.95)),  # bbox
    ("Seoul",            "KR", 2297418),
    ("Melbourne",        "AU", (-37.95, 144.85, -37.70, 145.20)),  # bbox (city of Melbourne is tiny)
    ("Sydney",           "AU", (-34.05, 150.95, -33.75, 151.30)),  # bbox of metro
    ("New York City",    "US", 175905),
    ("Boston",           "US", 2315704),
    ("San Francisco",    "US", 111968),
    ("Los Angeles",      "US", 207359),
    ("Chicago",          "US", 122604),
    ("Toronto",          "CA", 324211),
    ("Auckland",         "NZ", (-37.05, 174.55, -36.75, 174.95)),
    ("Wellington",       "NZ", 2218302),
    ("Cape Town",        "ZA", 4577200),
    ("Singapore",        "SG", 536780),
    ("Rome",             "IT", 41485),
    ("Milan",            "IT", 44915),
    ("Lisbon",           "PT", 5400890),
    ("Brussels",         "BE", 54094),
    ("Zurich",           "CH", 1682248),
    ("Dublin",           "IE", 1109614),
]

EARTH_R = 6_371_000.0


def haversine_m(lat1, lon1, lat2, lon2):
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


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
        print(f"    WARN: {e}; retry {attempt+1}/{MAX_ATTEMPTS} after {backoff}s")
        time.sleep(backoff)
        return fetch_overpass(query, attempt + 1)


def slug(name: str) -> str:
    import re
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


def fetch_city(name: str, scope) -> tuple[dict, dict]:
    if isinstance(scope, int):
        sc = f"area:{3_600_000_000 + scope}"
    else:
        s, w, n, e = scope
        sc = f"{s},{w},{n},{e}"
    courts_q = f"""[out:json][timeout:240];
(
  node["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({sc});
  way["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({sc});
  relation["leisure"="pitch"]["sport"~"(^|;)tennis(;|$)"]({sc});
);
out center tags;
"""
    parks_q = f"""[out:json][timeout:240];
(
  way["leisure"~"^(park|recreation_ground|garden|common|nature_reserve)$"]({sc});
  relation["leisure"~"^(park|recreation_ground|garden|common|nature_reserve)$"]({sc});
);
out geom;
"""
    s = slug(name)
    courts_path = GLOBAL_DIR / f"courts_{s}.json"
    parks_path = GLOBAL_DIR / f"parks_{s}.json"

    if courts_path.exists():
        courts = json.loads(courts_path.read_text())
        print(f"  courts: cached ({len(courts.get('elements', []))} els)")
    else:
        print(f"  fetching courts ...")
        courts = fetch_overpass(courts_q)
        courts_path.write_text(json.dumps(courts))
        print(f"  courts: {len(courts.get('elements', []))} els")
        time.sleep(SLEEP_BETWEEN)

    if parks_path.exists():
        parks = json.loads(parks_path.read_text())
        ways = sum(1 for e in parks.get("elements", []) if e["type"] == "way")
        print(f"  parks: cached ({ways} ways)")
    else:
        print(f"  fetching parks ...")
        parks = fetch_overpass(parks_q)
        parks_path.write_text(json.dumps(parks))
        ways = sum(1 for e in parks.get("elements", []) if e["type"] == "way")
        print(f"  parks: {ways} ways")
        time.sleep(SLEEP_BETWEEN)

    return courts, parks


def build_park_polys(parks_json: dict) -> tuple[list, list[str]]:
    """Repair invalid polygons via buffer(0) — mirrors the fix in
    14_park_filter.py / 24_park_filter_v2.py so Step 3 and Step 4
    operate on the same park polygon set."""
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


def courts_with_coords(courts_json: dict) -> list[dict]:
    out = []
    for el in courts_json.get("elements", []):
        tags = el.get("tags", {})
        if tags.get("leisure") != "pitch":
            continue
        if tags.get("access") == "private":
            continue
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        out.append({"lat": lat, "lon": lon, "id": el.get("id"),
                    "type": el.get("type"), "tags": tags})
    return out


def filter_park_courts(courts: list[dict], polys: list) -> list[dict]:
    if not polys:
        return []
    tree = STRtree(polys)
    park_courts = []
    for c in courts:
        pt = Point(c["lon"], c["lat"])
        for idx in tree.query(pt):
            if polys[int(idx)].contains(pt):
                park_courts.append(c)
                break
    return park_courts


def densest_circle(points: list[tuple], radius_m: float) -> dict:
    n = len(points)
    if n == 0:
        return {"count": 0, "center": None}
    best = {"count": 0, "center": None}
    for i in range(n):
        lat_i, lon_i = points[i]
        dlat = radius_m / 111_320.0
        cos_lat = math.cos(math.radians(lat_i))
        dlon = radius_m / (111_320.0 * max(cos_lat, 0.01))
        count = 0
        for j in range(n):
            lat_j, lon_j = points[j]
            if abs(lat_j - lat_i) > dlat or abs(lon_j - lon_i) > dlon:
                continue
            if haversine_m(lat_i, lon_i, lat_j, lon_j) <= radius_m:
                count += 1
        if count > best["count"]:
            best = {"count": count, "center": (lat_i, lon_i)}
    return best


def main() -> int:
    # Brighton radius from updated SEC (Queens-east, Pavilion, Kingsway, Blakers)
    sec_r = 2342.0  # metres

    out = []
    for name, country, scope in CITIES:
        print(f"\n=== {name} ({country}) scope={scope} ===")
        try:
            courts_json, parks_json = fetch_city(name, scope)
        except Exception as e:
            print(f"  ERROR fetching: {e}")
            out.append({"city": name, "country": country, "error": str(e)})
            continue

        courts = courts_with_coords(courts_json)
        polys, _ = build_park_polys(parks_json)
        park_courts = filter_park_courts(courts, polys)
        print(f"  total non-private courts: {len(courts)}, "
              f"park courts: {len(park_courts)}")

        all_pts = [(c["lat"], c["lon"]) for c in courts]
        park_pts = [(c["lat"], c["lon"]) for c in park_courts]
        d_all = densest_circle(all_pts, sec_r)
        d_park = densest_circle(park_pts, sec_r)
        print(f"  densest 2.26km circle  all: {d_all['count']}  park: {d_park['count']}")
        out.append({
            "city": name,
            "country": country,
            "total_courts": len(courts),
            "total_park_courts": len(park_courts),
            "densest_all": d_all["count"],
            "densest_all_lat": d_all["center"][0] if d_all["center"] else None,
            "densest_all_lon": d_all["center"][1] if d_all["center"] else None,
            "densest_park": d_park["count"],
            "densest_park_lat": d_park["center"][0] if d_park["center"] else None,
            "densest_park_lon": d_park["center"][1] if d_park["center"] else None,
        })

    csv_path = PROCESSED / "global_densest_circle.csv"
    keys = ["city", "country", "total_courts", "total_park_courts",
            "densest_all", "densest_all_lat", "densest_all_lon",
            "densest_park", "densest_park_lat", "densest_park_lon", "error"]
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in out:
            for k in keys:
                row.setdefault(k, "")
            w.writerow(row)

    # Ranking
    valid = [r for r in out if not r.get("error")]
    valid.sort(key=lambda r: -r["densest_park"])
    print(f"\n=== GLOBAL densest 2.26 km park-courts circle ===")
    print(f"{'rank':>4}  {'city':<22} {'country':>3}  {'total':>5}  "
          f"{'parkc':>5}  {'densest':>7}")
    for i, r in enumerate(valid, 1):
        print(f"{i:>4}  {r['city']:<22} {r['country']:>3}  "
              f"{r['total_courts']:>5}  {r['total_park_courts']:>5}  "
              f"{r['densest_park']:>7}")
    print(f"\nwrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
