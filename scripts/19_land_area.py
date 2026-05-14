"""Compute the LAND area of Brighton's Central B&H circle.

The circle, drawn just to enclose Queens Park, Pavilion & Avenue, Kingsway,
and Blakers, extends south into the English Channel. About a third of its
disc area is sea, which inflates the denominator when computing "courts per
km²". This script intersects the circle with the Brighton & Hove unitary
authority polygon (OSM relation 114085) to get true land area.

Output: prints circle area, land area, % sea, courts/km² (raw) and
courts/km² (land-only).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import transform
import pyproj

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

BRIGHTON_QUEENS = (50.82536, -0.12322)  # way 127064771 — south-east Queens court, ensures all 6 Queens courts fit inside the SEC
BRIGHTON_PAVILION_AVE = (50.84273, -0.16094)
BRIGHTON_KINGSWAY = (50.82598, -0.18975)
BRIGHTON_BLAKERS = (50.84220, -0.13769)

EARTH_R = 6_371_000.0


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
    n = len(points)
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            c = midpoint(points[i], points[j])
            r = haversine_m(*c, *points[i])
            if all(haversine_m(*c, *p) <= r + 1.0 for p in points):
                if best is None or r < best[2]:
                    best = (c[0], c[1], r)
    # circumcenter cases skipped (always reachable via diameter for our anchors)
    return best


def build_ua_polygon(rel_data) -> MultiPolygon:
    """Stitch outer/inner rings of a multipolygon relation into a (Multi)Polygon."""
    rel = rel_data["elements"][0]
    # Build raw segments by member
    outer_rings = []
    inner_rings = []
    for m in rel.get("members", []):
        role = m.get("role")
        geom = m.get("geometry")
        if not geom:
            continue
        coords = [(n["lon"], n["lat"]) for n in geom]
        if role == "outer":
            outer_rings.append(coords)
        elif role == "inner":
            inner_rings.append(coords)

    # Stitch segments into closed rings
    def stitch(segments):
        rings = []
        remaining = [list(s) for s in segments]
        while remaining:
            ring = remaining.pop(0)
            while ring[0] != ring[-1] and remaining:
                # find a segment that starts/ends where ring ends
                attached = False
                for i, s in enumerate(remaining):
                    if s[0] == ring[-1]:
                        ring.extend(s[1:])
                        remaining.pop(i)
                        attached = True
                        break
                    elif s[-1] == ring[-1]:
                        ring.extend(s[-2::-1])
                        remaining.pop(i)
                        attached = True
                        break
                    elif s[0] == ring[0]:
                        ring = list(reversed(s))[:-1] + ring
                        remaining.pop(i)
                        attached = True
                        break
                    elif s[-1] == ring[0]:
                        ring = s[:-1] + ring
                        remaining.pop(i)
                        attached = True
                        break
                if not attached:
                    break
            if ring[0] == ring[-1] and len(ring) >= 4:
                rings.append(ring)
        return rings

    outer_closed = stitch(outer_rings)
    inner_closed = stitch(inner_rings)
    polys = []
    for outer in outer_closed:
        # Naive: just take outer rings as polygons; ignore inners that may be
        # nested in OTHER outers. For UA usage this is fine.
        try:
            p = Polygon(outer)
            if p.is_valid and p.area > 0:
                polys.append(p)
        except Exception:
            pass
    if len(polys) == 1:
        return polys[0]
    return MultiPolygon(polys)


def main() -> int:
    # Compute circle
    sec_lat, sec_lon, sec_r = smallest_enclosing_circle(
        [BRIGHTON_QUEENS, BRIGHTON_PAVILION_AVE, BRIGHTON_KINGSWAY, BRIGHTON_BLAKERS])
    print(f"Central B&H circle: centre=({sec_lat:.5f},{sec_lon:.5f})  r={sec_r:.0f} m")

    # Load Brighton UA polygon
    ua_path = RAW / "overpass" / "uk" / "brighton_ua.json"
    ua_data = json.loads(ua_path.read_text())
    ua = build_ua_polygon(ua_data)
    print(f"Brighton & Hove UA polygon: type={ua.geom_type}, "
          f"{len(list(ua.geoms)) if ua.geom_type == 'MultiPolygon' else 1} parts")

    # Build the circle as a polygon (high-resolution, geographic)
    # We project to a local equidistant projection centered on the circle for
    # accurate area.
    project_to_local = pyproj.Transformer.from_crs(
        "EPSG:4326",
        f"+proj=aeqd +lat_0={sec_lat} +lon_0={sec_lon} +datum=WGS84 +units=m",
        always_xy=True,
    ).transform
    project_back = pyproj.Transformer.from_crs(
        f"+proj=aeqd +lat_0={sec_lat} +lon_0={sec_lon} +datum=WGS84 +units=m",
        "EPSG:4326",
        always_xy=True,
    ).transform

    # Circle as polygon in local CRS = circle of radius sec_r centered at (0,0)
    angles = [math.radians(a) for a in range(0, 360)]
    local_circle = Polygon([(sec_r * math.cos(a), sec_r * math.sin(a)) for a in angles])

    # Project UA to local CRS
    ua_local = transform(project_to_local, ua)

    # Intersect: circle ∩ admin polygon
    land = local_circle.intersection(ua_local)

    # Also subtract OSM water (lakes, docks etc.) inside the admin polygon —
    # for Brighton specifically there's essentially no inland water inside
    # the circle (the Channel is already excluded by the coast boundary),
    # but doing the subtraction keeps the pipeline parallel to other cities.
    water_path = RAW / "overpass" / "uk" / "water_015_brighton_and_hove.json"
    water_area_km2 = 0.0
    if water_path.exists():
        from shapely.geometry import Polygon as _P, MultiPolygon as _MP
        from shapely.ops import unary_union as _uu
        wjson = json.loads(water_path.read_text())
        wpolys = []
        for el in wjson.get("elements", []):
            if el["type"] == "way" and "geometry" in el:
                coords = [(n["lon"], n["lat"]) for n in el["geometry"]]
                if len(coords) >= 4:
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    try:
                        p = _P(coords)
                        if not p.is_valid:
                            p = p.buffer(0)
                        if p.is_valid and p.area > 0:
                            wpolys.append(p)
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
                                p = _P(coords)
                                if not p.is_valid:
                                    p = p.buffer(0)
                                if p.is_valid and p.area > 0:
                                    wpolys.append(p)
                            except Exception:
                                pass
        if wpolys:
            water = _uu(wpolys) if len(wpolys) > 1 else wpolys[0]
            water_local = transform(project_to_local, water)
            land = land.difference(water_local)
            water_area_km2 = water_local.intersection(local_circle).area / 1e6

    disc_area_km2 = (math.pi * sec_r ** 2) / 1e6
    land_area_km2 = land.area / 1e6
    sea_area_km2 = disc_area_km2 - land_area_km2 - water_area_km2
    pct_sea = sea_area_km2 / disc_area_km2 * 100

    print(f"\nCircle disc area: {disc_area_km2:.2f} km²")
    print(f"Land area within circle: {land_area_km2:.2f} km² (admin ∩ circle − inland water)")
    print(f"Inland water within circle: {water_area_km2:.3f} km²")
    print(f"Sea (English Channel) area within circle: {sea_area_km2:.2f} km² ({pct_sea:.1f}%)")

    # Brighton's park courts in circle from CSV
    import csv
    rows = list(csv.DictReader(open(ROOT / "data" / "processed" / "uk_tennis_facilities_parks.csv")))
    bh = [r for r in rows if r["city_name"] == "Brighton and Hove" and r["kind"] == "court"
          and r["access"] != "private"]
    bh_park = [r for r in bh if r["in_park"] == "1"]

    in_circle_all = sum(1 for r in bh if haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)
    in_circle_park = sum(1 for r in bh_park if haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)

    print(f"\nCourts in circle: {in_circle_all} all non-private  |  {in_circle_park} park")
    print(f"\nDensity per km² of DISC (includes sea):")
    print(f"  all non-private: {in_circle_all/disc_area_km2:.2f}/km²")
    print(f"  park only:       {in_circle_park/disc_area_km2:.2f}/km²")
    print(f"\nDensity per km² of LAND (sea-corrected):")
    print(f"  all non-private: {in_circle_all/land_area_km2:.2f}/km²")
    print(f"  park only:       {in_circle_park/land_area_km2:.2f}/km²")

    # Save the land polygon for map use
    out = {
        "center_lat": sec_lat,
        "center_lon": sec_lon,
        "radius_m": sec_r,
        "disc_area_km2": disc_area_km2,
        "land_area_km2": land_area_km2,
        "water_area_km2": water_area_km2,
        "sea_area_km2": sea_area_km2,
        "pct_sea": pct_sea,
        "all_courts_in_circle": in_circle_all,
        "park_courts_in_circle": in_circle_park,
    }
    (ROOT / "data" / "processed" / "brighton_circle_land.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote brighton_circle_land.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
