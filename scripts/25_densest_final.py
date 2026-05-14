"""Final densest-circle analysis using the refined 'public park court'
filter (in_park AND NOT in_club).

Reads uk_tennis_facilities_parks_v2.csv (produced by 24_park_filter_v2.py).
Reads global cached OSM and applies park + club polygon spatial joins.

Outputs:
  data/processed/uk_densest_circle_final.csv
  data/processed/global_densest_circle_final.csv
  data/processed/uk_density_final.csv
  data/processed/global_density_final.csv
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import transform as sh_transform, unary_union
import pyproj

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

# Brighton circle anchors (corrected, with Blakers added)
BRIGHTON_QUEENS = (50.82536, -0.12322)  # way 127064771 — south-east Queens court, ensures all 6 Queens courts fit inside the SEC
BRIGHTON_PAVILION_AVE = (50.84273, -0.16094)
BRIGHTON_KINGSWAY = (50.82598, -0.18975)
BRIGHTON_BLAKERS = (50.84220, -0.13769)

EARTH_R = 6_371_000.0


def slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


def haversine_m(lat1, lon1, lat2, lon2):
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def midpoint(p1, p2):
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat = math.atan2(math.sin(lat1) + math.sin(lat2),
                     math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2))
    lon = lon1 + math.atan2(by, math.cos(lat1) + bx)
    return (math.degrees(lat), math.degrees(lon))


def smallest_enclosing_circle(points):
    n = len(points); best = None
    for i in range(n):
        for j in range(i + 1, n):
            c = midpoint(points[i], points[j])
            r = haversine_m(*c, *points[i])
            if all(haversine_m(*c, *p) <= r + 1.0 for p in points):
                if best is None or r < best[2]:
                    best = (c[0], c[1], r)
    return best


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
        cnt = 0
        for j in range(n):
            lat_j, lon_j = points[j]
            if abs(lat_j - lat_i) > dlat or abs(lon_j - lon_i) > dlon:
                continue
            if haversine_m(lat_i, lon_i, lat_j, lon_j) <= radius_m:
                cnt += 1
        if cnt > best["count"]:
            best = {"count": cnt, "center": (lat_i, lon_i)}
    return best


def build_polygons(data: dict) -> tuple[list, list[str]]:
    polys = []; names = []
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
                        polys.append(p); names.append(el.get("tags", {}).get("name", ""))
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
                        polys.append(mp); names.append(el.get("tags", {}).get("name", ""))
                except Exception:
                    pass
    return polys, names


def stitch_rings(segments):
    rings = []
    remaining = [list(s) for s in segments]
    while remaining:
        ring = remaining.pop(0)
        while ring[0] != ring[-1] and remaining:
            attached = False
            for i, s in enumerate(remaining):
                if s[0] == ring[-1]:
                    ring.extend(s[1:]); remaining.pop(i); attached = True; break
                if s[-1] == ring[-1]:
                    ring.extend(s[-2::-1]); remaining.pop(i); attached = True; break
                if s[0] == ring[0]:
                    ring = list(reversed(s))[:-1] + ring; remaining.pop(i); attached = True; break
                if s[-1] == ring[0]:
                    ring = s[:-1] + ring; remaining.pop(i); attached = True; break
            if not attached:
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def boundary_to_polygon(boundary_json):
    polys = []
    for rel in boundary_json.get("elements", []):
        if rel.get("type") != "relation":
            continue
        outer_rings_raw = []
        for m in rel.get("members", []):
            if m.get("role") == "outer" and "geometry" in m:
                coords = [(n["lon"], n["lat"]) for n in m["geometry"]]
                if len(coords) >= 2:
                    outer_rings_raw.append(coords)
        outers = stitch_rings(outer_rings_raw)
        for outer in outers:
            try:
                p = Polygon(outer)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.is_valid and p.area > 0:
                    polys.append(p)
            except Exception:
                pass
    if not polys:
        return None
    if len(polys) == 1:
        return polys[0]
    try:
        return unary_union(polys)
    except Exception:
        return MultiPolygon(polys)


def water_to_multipolygon(water_json):
    """Build a single (multi)polygon of water bodies from natural=water /
    waterway=riverbank ways and relations. Used to subtract rivers/lakes
    from the circle ∩ admin intersection."""
    if not water_json:
        return None
    polys = []
    for el in water_json.get("elements", []):
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
            for outer in outers:
                try:
                    p = Polygon(outer)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.is_valid and p.area > 0:
                        polys.append(p)
                except Exception:
                    pass
    if not polys:
        return None
    try:
        return unary_union(polys)
    except Exception:
        return MultiPolygon(polys) if len(polys) > 1 else polys[0]


def land_area_km2(center_lat, center_lon, radius_m, boundary, water=None):
    """Land area = (circle ∩ admin polygon) − water polygons.
    When the admin polygon is None we fall back to the full disc area; when
    water is None we skip the water subtraction (e.g. for cities without a
    cached water_*.json yet)."""
    disc_km2 = math.pi * (radius_m / 1000) ** 2
    if boundary is None:
        # Even bbox-only cities can have water subtracted if available.
        inter_km2 = disc_km2
        if water is None:
            return inter_km2
    to_local = pyproj.Transformer.from_crs(
        "EPSG:4326",
        f"+proj=aeqd +lat_0={center_lat} +lon_0={center_lon} +datum=WGS84 +units=m",
        always_xy=True,
    ).transform
    local_circle = Polygon([(radius_m * math.cos(math.radians(a)),
                             radius_m * math.sin(math.radians(a))) for a in range(0, 360)])
    try:
        if boundary is None:
            inter = local_circle
        else:
            b_local = sh_transform(to_local, boundary)
            inter = local_circle.intersection(b_local)
        if water is not None:
            try:
                w_local = sh_transform(to_local, water)
                inter = inter.difference(w_local)
            except Exception:
                pass
        return inter.area / 1e6
    except Exception:
        return disc_km2


def process_uk(sec_lat, sec_lon, sec_r):
    fac = list(csv.DictReader(open(PROCESSED / "uk_tennis_facilities_parks_v2.csv")))
    courts = [r for r in fac if r["kind"] == "court" and r["access"] != "private"]
    park_public = [r for r in courts if r.get("park_public") == "1"]
    print(f"UK: {len(courts)} non-private courts, {len(park_public)} public-park (in park AND NOT in club)")

    cities = {c["name"]: int(c["rank"]) for c in csv.DictReader(open(PROCESSED / "uk_cities.csv"))}
    by_city_all = defaultdict(list)
    by_city_pub = defaultdict(list)
    for r in courts:
        by_city_all[r["city_name"]].append((float(r["lat"]), float(r["lon"])))
    for r in park_public:
        by_city_pub[r["city_name"]].append((float(r["lat"]), float(r["lon"])))

    results = []
    for city in sorted(set(list(by_city_all.keys()) + list(by_city_pub.keys()))):
        d_all = densest_circle(by_city_all.get(city, []), sec_r)
        d_pub = densest_circle(by_city_pub.get(city, []), sec_r)
        rank = cities.get(city)
        boundary = None
        water = None
        if rank:
            cands = list((RAW / "overpass" / "uk").glob(f"boundary_{rank:03d}_*.json"))
            if cands:
                boundary = boundary_to_polygon(json.loads(cands[0].read_text()))
            water_cands = list((RAW / "overpass" / "uk").glob(f"water_{rank:03d}_*.json"))
            if water_cands:
                water = water_to_multipolygon(json.loads(water_cands[0].read_text()))
        disc_km2 = math.pi * (sec_r / 1000) ** 2
        land_pub = land_area_km2(*d_pub["center"], sec_r, boundary, water) if d_pub["center"] else disc_km2
        results.append({
            "city": city,
            "total_courts": len(by_city_all.get(city, [])),
            "total_public_park": len(by_city_pub.get(city, [])),
            "densest_public_park": d_pub["count"],
            "densest_public_park_lat": d_pub["center"][0] if d_pub["center"] else None,
            "densest_public_park_lon": d_pub["center"][1] if d_pub["center"] else None,
            "densest_all": d_all["count"],
            "land_km2": round(land_pub, 2),
            "density_public_park_per_km2_land": round(d_pub["count"] / land_pub, 2) if land_pub > 0 else 0,
        })

    # Brighton's user circle
    bh_pts_all = by_city_all.get("Brighton and Hove", [])
    bh_pts_pub = by_city_pub.get("Brighton and Hove", [])
    bh_all_uc = sum(1 for p in bh_pts_all if haversine_m(p[0], p[1], sec_lat, sec_lon) <= sec_r)
    bh_pub_uc = sum(1 for p in bh_pts_pub if haversine_m(p[0], p[1], sec_lat, sec_lon) <= sec_r)
    cands = list((RAW / "overpass" / "uk").glob("boundary_015_*.json"))
    bh_boundary = boundary_to_polygon(json.loads(cands[0].read_text())) if cands else None
    bh_water_cands = list((RAW / "overpass" / "uk").glob("water_015_*.json"))
    bh_water = water_to_multipolygon(json.loads(bh_water_cands[0].read_text())) if bh_water_cands else None
    bh_uc_land = land_area_km2(sec_lat, sec_lon, sec_r, bh_boundary, bh_water)
    for r in results:
        if r["city"] == "Brighton and Hove":
            r["central_bh_all"] = bh_all_uc
            r["central_bh_public_park"] = bh_pub_uc
            r["central_bh_land_km2"] = round(bh_uc_land, 2)
            r["central_bh_density_per_km2_land"] = round(bh_pub_uc / bh_uc_land, 2)

    out_csv = PROCESSED / "uk_density_final.csv"
    fields = list(results[0].keys()) + ["central_bh_all", "central_bh_public_park",
                                         "central_bh_land_km2", "central_bh_density_per_km2_land"]
    seen = set(); fields = [f for f in fields if not (f in seen or seen.add(f))]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\nwrote {out_csv}")

    results.sort(key=lambda r: -r["density_public_park_per_km2_land"])
    print("\n=== UK: PUBLIC PARK courts per km² LAND (densest 2.34 km circle) ===")
    print(f"{'rank':>4}  {'city':<28} {'park':>5} {'land':>6}  {'per km²':>8}")
    for i, r in enumerate(results[:15], 1):
        mark = " <-- BRIGHTON" if r["city"] == "Brighton and Hove" else ""
        print(f"{i:>4}  {r['city'][:28]:<28} {r['densest_public_park']:>5} "
              f"{r['land_km2']:>6.2f}  {r['density_public_park_per_km2_land']:>8.2f}{mark}")

    bh = [r for r in results if r["city"] == "Brighton and Hove"][0]
    print(f"\nBrighton & Hove Central B&H circle (user-defined):")
    print(f"  all non-private courts in circle: {bh.get('central_bh_all','?')}")
    print(f"  PUBLIC park courts in circle:     {bh.get('central_bh_public_park','?')}")
    print(f"  LAND area:                         {bh.get('central_bh_land_km2','?')} km²")
    print(f"  density:                           {bh.get('central_bh_density_per_km2_land','?')} public-park courts/km² land")


def process_global(sec_r):
    glob_dir = RAW / "overpass" / "global"
    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib.machinery import SourceFileLoader
    mod = SourceFileLoader("g", str(ROOT / "scripts" / "16_global_densest.py")).load_module()
    print(f"\nGLOBAL: re-filtering park courts with club exclusion ...")

    results = []
    for name, country, scope in mod.CITIES:
        s = slug(name)
        courts_path = glob_dir / f"courts_{s}.json"
        parks_path = glob_dir / f"parks_{s}.json"
        clubs_path = glob_dir / f"clubs_{s}.json"
        if not courts_path.exists():
            print(f"  {name}: missing courts")
            continue
        courts_json = json.loads(courts_path.read_text())
        parks_json = json.loads(parks_path.read_text()) if parks_path.exists() else {"elements": []}
        clubs_json = json.loads(clubs_path.read_text()) if clubs_path.exists() else {"elements": []}

        # Build points + filter non-private
        courts = []
        for el in courts_json.get("elements", []):
            t = el.get("tags", {})
            if t.get("leisure") != "pitch":
                continue
            if t.get("access") == "private":
                continue
            if "lat" in el:
                lat, lon = el["lat"], el["lon"]
            elif "center" in el:
                lat, lon = el["center"]["lat"], el["center"]["lon"]
            else:
                continue
            courts.append((lat, lon))

        park_polys, _ = build_polygons(parks_json)
        club_polys, _ = build_polygons(clubs_json)
        park_tree = STRtree(park_polys) if park_polys else None
        club_tree = STRtree(club_polys) if club_polys else None

        park_public = []
        for (lat, lon) in courts:
            pt = Point(lon, lat)
            in_park = False
            if park_tree:
                for idx in park_tree.query(pt):
                    if park_polys[int(idx)].contains(pt):
                        in_park = True; break
            if not in_park:
                continue
            in_club = False
            if club_tree:
                for idx in club_tree.query(pt):
                    if club_polys[int(idx)].contains(pt):
                        in_club = True; break
            if not in_club:
                park_public.append((lat, lon))

        d_pub = densest_circle(park_public, sec_r)
        d_all = densest_circle(courts, sec_r)

        boundary = None
        b_path = glob_dir / f"boundary_{s}.json"
        if b_path.exists():
            boundary = boundary_to_polygon(json.loads(b_path.read_text()))
        water = None
        water_path = glob_dir / f"water_{s}.json"
        if water_path.exists():
            water = water_to_multipolygon(json.loads(water_path.read_text()))
        disc_km2 = math.pi * (sec_r / 1000) ** 2
        land_pub = land_area_km2(*d_pub["center"], sec_r, boundary, water) if d_pub["center"] else disc_km2

        results.append({
            "city": name,
            "country": country,
            "total_courts": len(courts),
            "total_public_park": len(park_public),
            "densest_all": d_all["count"],
            "densest_public_park": d_pub["count"],
            "densest_public_park_lat": d_pub["center"][0] if d_pub["center"] else None,
            "densest_public_park_lon": d_pub["center"][1] if d_pub["center"] else None,
            "land_km2": round(land_pub, 2),
            "density_public_park_per_km2_land": round(d_pub["count"] / land_pub, 2) if land_pub > 0 else 0,
            "has_boundary": "yes" if boundary is not None else "no",
            "has_water": "yes" if water is not None else "no",
        })

    out_csv = PROCESSED / "global_density_final.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"wrote {out_csv}")

    results.sort(key=lambda r: -r["density_public_park_per_km2_land"])
    print("\n=== GLOBAL: PUBLIC PARK courts per km² LAND (densest 2.34 km circle, club-exclusion applied) ===")
    print(f"{'rank':>4}  {'city':<22} {'country':>3} {'park':>5} {'land':>6}  {'per km²':>8}  bound?")
    for i, r in enumerate(results, 1):
        print(f"{i:>4}  {r['city'][:22]:<22} {r['country']:>3} "
              f"{r['densest_public_park']:>5} {r['land_km2']:>6.2f}  "
              f"{r['density_public_park_per_km2_land']:>8.2f}  {r['has_boundary']}")


def main() -> int:
    sec_lat, sec_lon, sec_r = smallest_enclosing_circle(
        [BRIGHTON_QUEENS, BRIGHTON_PAVILION_AVE, BRIGHTON_KINGSWAY, BRIGHTON_BLAKERS])
    print(f"Central B&H circle: centre=({sec_lat:.5f},{sec_lon:.5f})  r={sec_r:.0f} m")
    process_uk(sec_lat, sec_lon, sec_r)
    process_global(sec_r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
