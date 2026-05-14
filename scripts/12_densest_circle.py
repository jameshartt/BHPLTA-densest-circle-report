"""Find the densest tennis-court circle in each city.

The challenge: is Central Brighton & Hove the densest tennis-court area in the
UK / world?

Brighton's "Central B&H" circle is the smallest enclosing circle of three
reference clusters:
  - Queens Park courts (east)
  - Pavilion & Avenue Tennis Club (north)
  - Kingsway / King Alfred (Hove Beach Club) courts (west)

For every city in our dataset we then slide a circle of the SAME radius across
all court positions and report the maximum count — the densest sub-circle in
that city.

Outputs:
  data/processed/uk_densest_circle.csv
  reports/densest_uk_ranking.png
  reports/brighton_central_circle.png  (map of Brighton's circle)
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

# Three reference court centroids in Brighton (from our OSM data):
BRIGHTON_QUEENS = (50.82397, -0.12476)        # Queens Park courts
BRIGHTON_PAVILION_AVE = (50.84293, -0.14888)  # Pavilion & Avenue Tennis Club
BRIGHTON_KINGSWAY = (50.82590, -0.18895)      # Kingsway / King Alfred / Hove Beach Club

EARTH_R = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def midpoint(p1: tuple, p2: tuple) -> tuple:
    """Geographic midpoint of two lat/lon points."""
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat = math.atan2(math.sin(lat1) + math.sin(lat2),
                     math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2))
    lon = lon1 + math.atan2(by, math.cos(lat1) + bx)
    return (math.degrees(lat), math.degrees(lon))


def circumcenter(p1: tuple, p2: tuple, p3: tuple) -> tuple | None:
    """Compute the circumcenter of a triangle (planar approximation in metres
    via equirectangular projection around the centroid)."""
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
    # back to lat/lon
    lat = lat0 + uy / 111_320.0
    lon = lon0 + ux / (111_320.0 * cos_lat0)
    return (lat, lon)


def smallest_enclosing_circle_3(p1: tuple, p2: tuple, p3: tuple) -> tuple:
    """SEC of three points (lat, lon). Returns (center_lat, center_lon, radius_m).

    For 3 points: if any one of the three diameter circles already encloses the
    third point, that's the SEC. Otherwise the circumscribed circle is the SEC.
    """
    candidates = []
    for (a, b, c) in [(p1, p2, p3), (p1, p3, p2), (p2, p3, p1)]:
        center = midpoint(a, b)
        r = haversine_m(*center, *a)
        if haversine_m(*center, *c) <= r + 0.5:  # 0.5m tolerance
            candidates.append((r, center, "diameter", (a, b, c)))
    if candidates:
        candidates.sort()
        r, center, kind, refs = candidates[0]
        return (center[0], center[1], r)
    cc = circumcenter(p1, p2, p3)
    if cc is None:
        raise ValueError("degenerate points")
    r = max(haversine_m(*cc, *p) for p in (p1, p2, p3))
    return (cc[0], cc[1], r)


def densest_circle(points: list[tuple], radius_m: float) -> dict:
    """Find the densest circle of given radius. Candidate centers = each point.

    Returns {count, center, indices_inside}.
    """
    n = len(points)
    if n == 0:
        return {"count": 0, "center": None, "indices_inside": []}
    best = {"count": 0, "center": None, "indices_inside": []}
    for i in range(n):
        lat_i, lon_i = points[i]
        # quick-reject via lat band
        dlat = radius_m / 111_320.0
        cos_lat = math.cos(math.radians(lat_i))
        dlon = radius_m / (111_320.0 * max(cos_lat, 0.01))
        inside = []
        for j in range(n):
            lat_j, lon_j = points[j]
            if abs(lat_j - lat_i) > dlat or abs(lon_j - lon_i) > dlon:
                continue
            if haversine_m(lat_i, lon_i, lat_j, lon_j) <= radius_m:
                inside.append(j)
        if len(inside) > best["count"]:
            best = {"count": len(inside), "center": (lat_i, lon_i),
                    "indices_inside": inside}
    return best


def count_in_circle(points: list[tuple], center: tuple, radius_m: float) -> list[int]:
    cnt = []
    for i, (lat, lon) in enumerate(points):
        if haversine_m(lat, lon, *center) <= radius_m:
            cnt.append(i)
    return cnt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    ap.add_argument("--include-private", action="store_true",
                    help="include access=private courts in the density count")
    args = ap.parse_args()

    facilities_path = PROCESSED / f"{args.region}_tennis_facilities.csv"
    rows = list(csv.DictReader(facilities_path.open()))
    courts = [r for r in rows if r["kind"] == "court"]
    if not args.include_private:
        courts = [r for r in courts if r["access"] != "private"]
    print(f"Total courts in dataset: {len(courts)} "
          f"({'incl. private' if args.include_private else 'non-private only'})")

    # Compute Brighton's SEC
    sec_lat, sec_lon, sec_r = smallest_enclosing_circle_3(
        BRIGHTON_QUEENS, BRIGHTON_PAVILION_AVE, BRIGHTON_KINGSWAY)
    print(f"\nBrighton 'Central B&H' circle:")
    print(f"  centre: {sec_lat:.5f}, {sec_lon:.5f}")
    print(f"  radius: {sec_r:.0f} m ({sec_r/1000:.2f} km)")
    print(f"  area:   {math.pi * (sec_r/1000)**2:.2f} km²")

    # Group courts by city
    by_city: dict[str, list[tuple]] = defaultdict(list)
    for c in courts:
        by_city[c["city_name"]].append((float(c["lat"]), float(c["lon"])))

    # Brighton's specific (user-defined) circle count
    bh_pts = by_city.get("Brighton and Hove", [])
    bh_specific = count_in_circle(bh_pts, (sec_lat, sec_lon), sec_r)
    print(f"\nCourts within Brighton's Central B&H circle (OSM data): "
          f"{len(bh_specific)} of {len(bh_pts)} total Brighton non-private")

    # For every city, find max-density sub-circle of the SAME radius
    results = []
    for city, pts in sorted(by_city.items()):
        d = densest_circle(pts, sec_r)
        results.append({
            "city": city,
            "total_courts": len(pts),
            "densest_count": d["count"],
            "densest_lat": d["center"][0] if d["center"] else None,
            "densest_lon": d["center"][1] if d["center"] else None,
        })

    # Brighton's specific circle is ADDITIONAL info; the "densest" column is
    # the max anywhere in that city.
    for r in results:
        if r["city"] == "Brighton and Hove":
            r["central_bh_circle_count"] = len(bh_specific)
            r["central_bh_circle_lat"] = sec_lat
            r["central_bh_circle_lon"] = sec_lon

    # Output CSV
    out_csv = PROCESSED / f"{args.region}_densest_circle.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["city", "total_courts", "densest_count", "densest_lat",
                  "densest_lon", "central_bh_circle_count",
                  "central_bh_circle_lat", "central_bh_circle_lon"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in results:
            w.writerow(r)

    # Print ranking
    results.sort(key=lambda r: -r["densest_count"])
    print(f"\n=== Densest circle by city (radius {sec_r/1000:.2f} km, "
          f"area {math.pi*(sec_r/1000)**2:.2f} km²) ===")
    print(f"{'rank':>4}  {'city':<28} {'total':>6}  {'densest':>8}  centre")
    for i, r in enumerate(results[:25], 1):
        mark = " <-- BRIGHTON" if r["city"] == "Brighton and Hove" else ""
        print(f"{i:>4}  {r['city'][:28]:<28} {r['total_courts']:>6}  "
              f"{r['densest_count']:>8}  "
              f"({r['densest_lat']:.4f},{r['densest_lon']:.4f}){mark}")

    bh = [r for r in results if r["city"] == "Brighton and Hove"][0]
    print(f"\nBrighton & Hove:")
    print(f"  densest sub-circle anywhere in the city: {bh['densest_count']} courts at "
          f"({bh['densest_lat']:.4f},{bh['densest_lon']:.4f})")
    print(f"  Central B&H circle (Queens-Pavilion-Kingsway SEC): "
          f"{bh['central_bh_circle_count']} courts")

    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
