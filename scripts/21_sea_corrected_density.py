"""Sea-corrected densest-circle density analysis.

For every city (UK + global) with a fetched boundary polygon, compute:
  - the densest 2.34 km circle's centre (already known)
  - the LAND area within that circle (circle ∩ city polygon)
  - density = courts / land_area  (a fair per-km² metric)

Cities defined by bbox (no boundary polygon) report density per km² DISC
with a flag — those numbers are upper bounds since they may include water.

Outputs:
  data/processed/uk_density_sea_corrected.csv
  data/processed/global_density_sea_corrected.csv
  Prints rankings.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import transform as sh_transform, unary_union
import pyproj

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

# Brighton circle parameters (consistent across the analysis)
SEC_RADIUS_M = 2337.0


def slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


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


def boundary_to_polygon(boundary_json) -> Polygon | MultiPolygon | None:
    """Build a shapely polygon from one or more OSM relation boundaries."""
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
                if p.is_valid and p.area > 0:
                    polys.append(p)
                else:
                    p2 = p.buffer(0)
                    if p2.is_valid and p2.area > 0:
                        polys.append(p2)
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
    """Build a single (multi)polygon of inland water bodies."""
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
            for m in el["members"]:
                if m.get("role") == "outer" and "geometry" in m:
                    coords = [(n["lon"], n["lat"]) for n in m["geometry"]]
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
    if not polys:
        return None
    try:
        return unary_union(polys)
    except Exception:
        return MultiPolygon(polys) if len(polys) > 1 else polys[0]


def land_area_in_circle(center_lat: float, center_lon: float, radius_m: float,
                        boundary: Polygon | MultiPolygon | None,
                        water: Polygon | MultiPolygon | None = None) -> tuple[float, float]:
    """Returns (disc_area_km2, land_area_km2). land = (circle ∩ admin) − water."""
    disc_km2 = math.pi * (radius_m / 1000) ** 2
    if boundary is None and water is None:
        return disc_km2, disc_km2
    to_local = pyproj.Transformer.from_crs(
        "EPSG:4326",
        f"+proj=aeqd +lat_0={center_lat} +lon_0={center_lon} +datum=WGS84 +units=m",
        always_xy=True,
    ).transform
    local_circle = Polygon([(radius_m * math.cos(math.radians(a)),
                             radius_m * math.sin(math.radians(a)))
                            for a in range(0, 360)])
    try:
        if boundary is not None:
            boundary_local = sh_transform(to_local, boundary)
            land_local = local_circle.intersection(boundary_local)
        else:
            land_local = local_circle
        if water is not None:
            try:
                water_local = sh_transform(to_local, water)
                land_local = land_local.difference(water_local)
            except Exception:
                pass
        return disc_km2, land_local.area / 1e6
    except Exception as e:
        print(f"  warn: intersection failed: {e}")
        return disc_km2, disc_km2


def process_uk():
    densest_csv = PROCESSED / "uk_densest_circle.csv"
    cities_csv = PROCESSED / "uk_cities.csv"
    uk_dir = RAW / "overpass" / "uk"

    rows = list(csv.DictReader(densest_csv.open()))
    cities = {c["name"]: c for c in csv.DictReader(cities_csv.open())}

    results = []
    for r in rows:
        city = r["city"]
        if not r.get("densest_park") or float(r["densest_park"]) == 0:
            continue
        densest_lat = float(r["densest_park_lat"])
        densest_lon = float(r["densest_park_lon"])
        densest_all_lat = float(r["densest_all_lat"]) if r.get("densest_all_lat") else None
        densest_all_lon = float(r["densest_all_lon"]) if r.get("densest_all_lon") else None
        densest_all = int(r["densest_all"])
        densest_park = int(r["densest_park"])

        c = cities.get(city)
        rank = int(c["rank"]) if c else 0
        candidates = list(uk_dir.glob(f"boundary_{rank:03d}_*.json"))
        boundary = None
        if candidates:
            data = json.loads(candidates[0].read_text())
            boundary = boundary_to_polygon(data)
        water_cands = list(uk_dir.glob(f"water_{rank:03d}_*.json"))
        water = water_to_multipolygon(json.loads(water_cands[0].read_text())) if water_cands else None
        # Park-circle land area
        _, park_land_km2 = land_area_in_circle(densest_lat, densest_lon, SEC_RADIUS_M, boundary, water)
        disc_km2 = math.pi * (SEC_RADIUS_M / 1000) ** 2
        # All-circle land area
        if densest_all_lat:
            _, all_land_km2 = land_area_in_circle(densest_all_lat, densest_all_lon, SEC_RADIUS_M, boundary, water)
        else:
            all_land_km2 = disc_km2

        # Brighton's user circle
        bh_park_uc = None
        bh_all_uc = None
        bh_uc_land = None
        if city == "Brighton and Hove" and r.get("central_bh_lat"):
            uc_lat = float(r["central_bh_lat"]); uc_lon = float(r["central_bh_lon"])
            _, bh_uc_land = land_area_in_circle(uc_lat, uc_lon, SEC_RADIUS_M, boundary, water)
            bh_park_uc = int(r["central_bh_park"])
            bh_all_uc = int(r["central_bh_all"])

        results.append({
            "city": city,
            "densest_park": densest_park,
            "densest_all": densest_all,
            "disc_km2": round(disc_km2, 2),
            "park_land_km2": round(park_land_km2, 2),
            "all_land_km2": round(all_land_km2, 2),
            "density_park_per_km2_disc": round(densest_park / disc_km2, 2),
            "density_park_per_km2_land": round(densest_park / park_land_km2, 2) if park_land_km2 > 0 else 0,
            "density_all_per_km2_disc": round(densest_all / disc_km2, 2),
            "density_all_per_km2_land": round(densest_all / all_land_km2, 2) if all_land_km2 > 0 else 0,
            "central_bh_park": bh_park_uc if bh_park_uc is not None else "",
            "central_bh_all": bh_all_uc if bh_all_uc is not None else "",
            "central_bh_land_km2": round(bh_uc_land, 2) if bh_uc_land else "",
            "central_bh_park_per_km2_land": round(bh_park_uc / bh_uc_land, 2) if bh_park_uc and bh_uc_land else "",
        })

    out_csv = PROCESSED / "uk_density_sea_corrected.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)

    print("\n=== UK: park-court density per km² LAND ===")
    results.sort(key=lambda r: -r["density_park_per_km2_land"])
    print(f"{'rank':>4}  {'city':<28} {'park':>5} {'land_km²':>9}  {'park/km²':>9}")
    for i, r in enumerate(results[:15], 1):
        mark = " <-- BRIGHTON" if r["city"] == "Brighton and Hove" else ""
        print(f"{i:>4}  {r['city'][:28]:<28} {r['densest_park']:>5} "
              f"{r['park_land_km2']:>9.2f}  {r['density_park_per_km2_land']:>9.2f}{mark}")

    print(f"\nwrote {out_csv}")
    return results


def process_global():
    densest_csv = PROCESSED / "global_densest_circle.csv"
    global_dir = RAW / "overpass" / "global"
    rows = list(csv.DictReader(densest_csv.open()))

    results = []
    for r in rows:
        if not r.get("densest_park") or float(r["densest_park"]) == 0:
            continue
        densest_lat = float(r["densest_park_lat"])
        densest_lon = float(r["densest_park_lon"])
        densest_all_lat = float(r["densest_all_lat"]) if r.get("densest_all_lat") else None
        densest_all_lon = float(r["densest_all_lon"]) if r.get("densest_all_lon") else None
        densest_all = int(r["densest_all"])
        densest_park = int(r["densest_park"])
        candidates = list(global_dir.glob(f"boundary_{slug(r['city'])}.json"))
        boundary = None
        if candidates:
            data = json.loads(candidates[0].read_text())
            boundary = boundary_to_polygon(data)
        water_path = global_dir / f"water_{slug(r['city'])}.json"
        water = water_to_multipolygon(json.loads(water_path.read_text())) if water_path.exists() else None
        disc_km2 = math.pi * (SEC_RADIUS_M / 1000) ** 2
        _, park_land_km2 = land_area_in_circle(densest_lat, densest_lon, SEC_RADIUS_M, boundary, water)
        if densest_all_lat:
            _, all_land_km2 = land_area_in_circle(densest_all_lat, densest_all_lon, SEC_RADIUS_M, boundary, water)
        else:
            all_land_km2 = disc_km2
        results.append({
            "city": r["city"],
            "country": r["country"],
            "has_boundary": "yes" if boundary is not None else "no (bbox)",
            "densest_park": densest_park,
            "densest_all": densest_all,
            "disc_km2": round(disc_km2, 2),
            "park_land_km2": round(park_land_km2, 2),
            "density_park_per_km2_disc": round(densest_park / disc_km2, 2),
            "density_park_per_km2_land": round(densest_park / park_land_km2, 2) if park_land_km2 > 0 else 0,
            "density_all_per_km2_land": round(densest_all / all_land_km2, 2) if all_land_km2 > 0 else 0,
        })

    out_csv = PROCESSED / "global_density_sea_corrected.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)

    results.sort(key=lambda r: -r["density_park_per_km2_land"])
    print("\n=== GLOBAL: park-court density per km² LAND ===")
    print(f"{'rank':>4}  {'city':<22} {'country':>3} {'park':>5} {'land_km²':>9} {'park/km²':>9}  bbox?")
    for i, r in enumerate(results, 1):
        print(f"{i:>4}  {r['city'][:22]:<22} {r['country']:>3} "
              f"{r['densest_park']:>5} {r['park_land_km2']:>9.2f} "
              f"{r['density_park_per_km2_land']:>9.2f}  {r['has_boundary']}")
    print(f"\nwrote {out_csv}")
    return results


def main() -> int:
    process_uk()
    process_global()
    return 0


if __name__ == "__main__":
    sys.exit(main())
