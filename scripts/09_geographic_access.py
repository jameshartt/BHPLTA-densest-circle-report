"""Geographic accessibility per city.

For each city, define a "tennis catchment polygon" as the convex hull of all
non-private court coordinates (a defensible proxy for the populated tennis-
relevant area, especially for compact / coastal cities). Then uniformly sample
random points inside that polygon and measure how close each lies to the
nearest court.

Outputs per-city:
  hull_km2                 area of the hull (km^2)
  pct_hull_within_500m     % of hull area within 500m of any court
  pct_hull_within_1km      % of hull area within 1km of any court
  pct_hull_within_2km      % of hull area within 2km of any court
  median_distance_m        median distance from a hull point to the nearest court
  mean_distance_m          mean distance

Cities with <5 courts are skipped.

Note: this measures GEOGRAPHIC coverage of the tennis footprint, not population
coverage. The follow-on script `10_population_access.py` will weight by LSOA
population.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

N_SAMPLES = 4000
SEED = 42


def project_eq(lats: list[float], lons: list[float], lat0: float, lon0: float) -> list[tuple[float, float]]:
    cos0 = math.cos(math.radians(lat0))
    R = 6_371_000.0
    return [
        (math.radians(lon - lon0) * cos0 * R, math.radians(lat - lat0) * R)
        for lat, lon in zip(lats, lons)
    ]


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def polygon_area(poly: list[tuple[float, float]]) -> float:
    """Shoelace, returns signed area in same units as inputs squared."""
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def point_in_poly(point: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    x, y = point
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def sample_in_hull(poly: list[tuple[float, float]], n: int, rng: random.Random) -> list[tuple[float, float]]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    out: list[tuple[float, float]] = []
    attempts = 0
    while len(out) < n and attempts < n * 50:
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        if point_in_poly((x, y), poly):
            out.append((x, y))
        attempts += 1
    return out


def compute_city(name: str, court_rows: list[dict]) -> dict:
    n = len(court_rows)
    if n < 5:
        return {"n_courts": n}
    lats = [float(r["lat"]) for r in court_rows]
    lons = [float(r["lon"]) for r in court_rows]
    lat0 = sum(lats) / n
    lon0 = sum(lons) / n
    proj_courts = project_eq(lats, lons, lat0, lon0)
    hull = convex_hull(proj_courts)
    if len(hull) < 3:
        return {"n_courts": n}

    rng = random.Random(SEED ^ hash(name))
    samples = sample_in_hull(hull, N_SAMPLES, rng)
    if not samples:
        return {"n_courts": n, "note": "hull degenerate"}

    # For each sample, distance to nearest court
    dists: list[float] = []
    for sx, sy in samples:
        best = float("inf")
        for cx, cy in proj_courts:
            d2 = (sx - cx) ** 2 + (sy - cy) ** 2
            if d2 < best:
                best = d2
        dists.append(math.sqrt(best))

    hull_km2 = polygon_area(hull) / 1_000_000
    return {
        "n_courts": n,
        "hull_km2": round(hull_km2, 2),
        "samples": len(samples),
        "pct_hull_within_500m": round(sum(1 for d in dists if d <= 500) / len(dists) * 100, 1),
        "pct_hull_within_1km": round(sum(1 for d in dists if d <= 1000) / len(dists) * 100, 1),
        "pct_hull_within_2km": round(sum(1 for d in dists if d <= 2000) / len(dists) * 100, 1),
        "median_distance_m": int(statistics.median(dists)),
        "mean_distance_m": int(statistics.mean(dists)),
    }


def show_ranking(rows: list[dict], metric: str, title: str, asc: bool, fmt: str = "{:.0f}"):
    print(f"=== {title} ===")
    items = [r for r in rows if r.get(metric) is not None]
    items.sort(key=lambda r: r[metric], reverse=not asc)
    shown = []
    for i, r in enumerate(items[:15], 1):
        mark = " <-- BRIGHTON" if r["name"] == "Brighton and Hove" else ""
        v = fmt.format(r[metric])
        shown.append(r["name"])
        print(f"  {i:>3}.  {r['name'][:26]:<26}  pop={r['population']:>10,}  hull={r.get('hull_km2',0):>5.1f}km²  {metric}={v}{mark}")
    if "Brighton and Hove" not in shown:
        for i, r in enumerate(items, 1):
            if r["name"] == "Brighton and Hove":
                print("   ...")
                v = fmt.format(r[metric])
                print(f"  {i:>3}.  {r['name'][:26]:<26}  pop={r['population']:>10,}  hull={r.get('hull_km2',0):>5.1f}km²  {metric}={v}  <-- BRIGHTON")
                break
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    facilities_csv = PROCESSED / f"{args.region}_tennis_facilities.csv"
    cities = {int(r["rank"]): r for r in csv.DictReader(cities_csv.open())}
    facilities = list(csv.DictReader(facilities_csv.open()))
    by_city: dict[int, list[dict]] = defaultdict(list)
    for f in facilities:
        if f["kind"] == "court" and f.get("access") != "private":
            by_city[int(f["city_rank"])].append(f)

    out: list[dict] = []
    for rank in sorted(cities):
        rows = by_city.get(rank, [])
        stats = compute_city(cities[rank]["name"], rows)
        out.append({
            "rank": rank,
            "name": cities[rank]["name"],
            "population": int(cities[rank]["population"]),
            **stats,
        })

    out_csv = PROCESSED / f"{args.region}_geo_access.csv"
    fieldnames = [
        "rank", "name", "population", "n_courts", "hull_km2", "samples",
        "pct_hull_within_500m", "pct_hull_within_1km", "pct_hull_within_2km",
        "median_distance_m", "mean_distance_m",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"wrote {out_csv}\n")

    rankable = [r for r in out if r.get("hull_km2") is not None]

    show_ranking(rankable, "pct_hull_within_500m",
                 "% of court-footprint area within 500m of a court (HIGHER = denser coverage)",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "pct_hull_within_1km",
                 "% of court-footprint area within 1km of a court",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "median_distance_m",
                 "Median distance from a random hull point to nearest court (LOWER = denser)",
                 asc=True, fmt="{:.0f} m")
    show_ranking(rankable, "mean_distance_m",
                 "Mean distance from a random hull point to nearest court",
                 asc=True, fmt="{:.0f} m")

    return 0


if __name__ == "__main__":
    sys.exit(main())
