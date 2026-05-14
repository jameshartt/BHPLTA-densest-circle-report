"""Densest tennis-court circle analysis — version 2 with park-filter support.

Computes:
  - All non-private courts: densest 2.26 km circle per city
  - Park courts only (inside leisure=park/recreation_ground/garden/common):
    densest 2.26 km circle per city
  - Brighton's user-defined "Central B&H" circle counts in both modes

Reads:
  data/processed/uk_tennis_facilities_parks.csv (from scripts/14_park_filter.py)
  data/processed/uk_cities.csv

Writes:
  data/processed/uk_densest_circle.csv (both modes)
  reports/uk_densest_all_vs_park.png
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

# Brighton anchors. The user-defined "Central B&H" circle should fully
# contain Queens Park (using the easternmost Queens Park court), Pavilion &
# Avenue, Kingsway/Hove Beach Club, and Blakers Park.
BRIGHTON_QUEENS = (50.82536, -0.12322)        # south-east Queens court (way 127064771); ensures all 6 Queens courts fit inside
BRIGHTON_PAVILION_AVE = (50.84273, -0.16094)  # Pavilion & Avenue (CORRECTED loc)
BRIGHTON_KINGSWAY = (50.82598, -0.18975)      # westernmost Kingsway court
BRIGHTON_BLAKERS = (50.84220, -0.13769)       # Blakers Park

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


def _circumcenter(p1, p2, p3):
    """Circumcenter of a triangle via equirectangular projection."""
    lat0 = (p1[0] + p2[0] + p3[0]) / 3
    lon0 = (p1[1] + p2[1] + p3[1]) / 3
    cos_lat0 = math.cos(math.radians(lat0))

    def to_xy(p):
        return ((p[1] - lon0) * 111_320.0 * cos_lat0,
                (p[0] - lat0) * 111_320.0)

    x1, y1 = to_xy(p1)
    x2, y2 = to_xy(p2)
    x3, y3 = to_xy(p3)
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return None
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) +
          (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) +
          (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    lat = lat0 + uy / 111_320.0
    lon = lon0 + ux / (111_320.0 * cos_lat0)
    return (lat, lon)


def smallest_enclosing_circle(points):
    """Brute-force SEC for small N (<=6). Returns (center_lat, center_lon, radius_m)."""
    n = len(points)
    if n == 0:
        raise ValueError("no points")
    if n == 1:
        return (points[0][0], points[0][1], 0.0)
    best = None
    # All pair midpoint (diameter) candidates
    for i in range(n):
        for j in range(i + 1, n):
            c = midpoint(points[i], points[j])
            r = haversine_m(*c, *points[i])
            if all(haversine_m(*c, *p) <= r + 1.0 for p in points):
                if best is None or r < best[2]:
                    best = (c[0], c[1], r)
    # All triple circumcircle candidates
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                cc = _circumcenter(points[i], points[j], points[k])
                if cc is None:
                    continue
                r = max(haversine_m(*cc, *p) for p in (points[i], points[j], points[k]))
                if all(haversine_m(*cc, *p) <= r + 1.0 for p in points):
                    if best is None or r < best[2]:
                        best = (cc[0], cc[1], r)
    if best is None:
        raise ValueError("SEC computation failed")
    return best


def smallest_enclosing_circle_3(p1, p2, p3):
    """Back-compat shim."""
    return smallest_enclosing_circle([p1, p2, p3])


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


def count_in_circle(points: list[tuple], center: tuple, radius_m: float) -> int:
    return sum(1 for (lat, lon) in points if haversine_m(lat, lon, *center) <= radius_m)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    facilities_csv = PROCESSED / f"{args.region}_tennis_facilities_parks.csv"
    if not facilities_csv.exists():
        print(f"missing {facilities_csv}; run 14_park_filter.py first", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(facilities_csv.open()))
    courts_all = [r for r in rows if r["kind"] == "court" and r["access"] != "private"]
    courts_park = [r for r in courts_all if r["in_park"] == "1"]
    print(f"non-private courts: {len(courts_all)}, of which in parks: {len(courts_park)} "
          f"({len(courts_park)/len(courts_all)*100:.1f}%)")

    sec_lat, sec_lon, sec_r = smallest_enclosing_circle(
        [BRIGHTON_QUEENS, BRIGHTON_PAVILION_AVE, BRIGHTON_KINGSWAY, BRIGHTON_BLAKERS])
    area_km2 = math.pi * (sec_r / 1000) ** 2
    print(f"\nCentral B&H circle:  centre={sec_lat:.5f},{sec_lon:.5f}  "
          f"radius={sec_r:.0f} m ({sec_r/1000:.2f} km)  area={area_km2:.2f} km²\n")

    by_city_all = defaultdict(list)
    by_city_park = defaultdict(list)
    for r in courts_all:
        by_city_all[r["city_name"]].append((float(r["lat"]), float(r["lon"])))
    for r in courts_park:
        by_city_park[r["city_name"]].append((float(r["lat"]), float(r["lon"])))

    # Brighton specifics
    bh_all_pts = by_city_all.get("Brighton and Hove", [])
    bh_park_pts = by_city_park.get("Brighton and Hove", [])
    bh_circle_all = count_in_circle(bh_all_pts, (sec_lat, sec_lon), sec_r)
    bh_circle_park = count_in_circle(bh_park_pts, (sec_lat, sec_lon), sec_r)
    print(f"Brighton 'Central B&H' specific circle:")
    print(f"  all non-private courts inside: {bh_circle_all}")
    print(f"  park courts only inside:       {bh_circle_park}\n")

    # Per-city densest circle in both modes
    results = []
    cities = sorted(set(list(by_city_all.keys()) + list(by_city_park.keys())))
    for city in cities:
        all_pts = by_city_all.get(city, [])
        park_pts = by_city_park.get(city, [])
        d_all = densest_circle(all_pts, sec_r)
        d_park = densest_circle(park_pts, sec_r)
        results.append({
            "city": city,
            "total_courts": len(all_pts),
            "total_park_courts": len(park_pts),
            "densest_all": d_all["count"],
            "densest_all_lat": d_all["center"][0] if d_all["center"] else None,
            "densest_all_lon": d_all["center"][1] if d_all["center"] else None,
            "densest_park": d_park["count"],
            "densest_park_lat": d_park["center"][0] if d_park["center"] else None,
            "densest_park_lon": d_park["center"][1] if d_park["center"] else None,
        })

    # Brighton row enriched
    for r in results:
        if r["city"] == "Brighton and Hove":
            r["central_bh_all"] = bh_circle_all
            r["central_bh_park"] = bh_circle_park
            r["central_bh_lat"] = sec_lat
            r["central_bh_lon"] = sec_lon

    out_csv = PROCESSED / f"{args.region}_densest_circle.csv"
    fields = list(results[0].keys()) + [
        "central_bh_all", "central_bh_park", "central_bh_lat", "central_bh_lon"
    ]
    seen = set()
    fields = [f for f in fields if not (f in seen or seen.add(f))]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r)

    # Rankings
    def print_rank(metric: str, label: str, n: int = 15):
        ranked = sorted(results, key=lambda r: -r[metric])
        print(f"\n=== {label} (radius {sec_r/1000:.2f} km, {area_km2:.1f} km²) ===")
        print(f"{'rank':>4}  {'city':<28} {'total':>6}  {'densest':>8}  centre")
        for i, r in enumerate(ranked[:n], 1):
            mark = " <-- BRIGHTON" if r["city"] == "Brighton and Hove" else ""
            lat = r.get(metric.replace("densest_", "densest_") + "_lat")
            lon = r.get(metric.replace("densest_", "densest_") + "_lon")
            ll = f"({lat:.4f},{lon:.4f})" if lat else ""
            total_key = "total_park_courts" if "park" in metric else "total_courts"
            print(f"{i:>4}  {r['city'][:28]:<28} {r[total_key]:>6}  "
                  f"{r[metric]:>8}  {ll}{mark}")

    print_rank("densest_all",
               "ALL non-private courts: densest 2.26 km circle")
    print_rank("densest_park",
               "PARK courts only: densest 2.26 km circle")

    bh = [r for r in results if r["city"] == "Brighton and Hove"][0]
    print(f"\nBrighton & Hove summary:")
    print(f"  Central B&H circle, all non-private courts: {bh['central_bh_all']}")
    print(f"  Central B&H circle, park courts only:        {bh['central_bh_park']}")
    print(f"  Densest 2.26km circle anywhere (all):        {bh['densest_all']}")
    print(f"  Densest 2.26km circle anywhere (park):       {bh['densest_park']}")

    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
