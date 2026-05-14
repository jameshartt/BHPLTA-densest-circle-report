"""Spatial-proximity stats per city.

Per-capita rankings can underweight cities that are geographically compact and
densely served. This script computes proximity metrics that don't require an
area or population raster:

  - nn1_m_median        median nearest-neighbour distance between courts
  - nn5_m_median        median distance to 5th nearest court (network density)
  - pct_within_500m     % of courts with another court within 500m
  - pct_within_1km      % of courts with another court within 1km
  - mean_pair_km        mean pairwise distance between courts (compactness)
  - convex_hull_km2     area of the convex hull spanned by all courts
  - courts_per_hull_km2 court density per km2 of convex hull

A city must have >=3 courts to be ranked.

Reads data/processed/uk_clubs.csv (cluster centroids), since these are the
canonical "venues". Uses court_count weights when relevant.

Outputs data/processed/uk_proximity.csv plus a printed ranking summary.
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Andrew's monotone chain. Points are (x, y) -- here we feed a local
    equirectangular projection so distances are roughly correct."""
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


def polygon_area_km2(hull: list[tuple[float, float]]) -> float:
    if len(hull) < 3:
        return 0.0
    s = 0.0
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        s += x1 * y2 - x2 * y1
    # x, y are in metres after our projection, so |s|/2 gives m^2
    return abs(s) / 2 / 1_000_000


def compute_city(rows: list[dict]) -> dict:
    """rows = court rows for one city (kind=court only)."""
    lats = [float(r["lat"]) for r in rows]
    lons = [float(r["lon"]) for r in rows]
    n = len(rows)
    if n < 3:
        return {"n_courts": n}

    # Equirectangular projection at the city centroid (ok for small extents)
    lat0 = sum(lats) / n
    cos0 = math.cos(math.radians(lat0))
    R = 6_371_000.0
    proj = [
        (math.radians(lon - sum(lons) / n) * cos0 * R, math.radians(lat - lat0) * R)
        for lat, lon in zip(lats, lons)
    ]

    # Pairwise distance matrix (O(n^2) — fine up to a few thousand)
    dists: list[list[float]] = [[0.0] * n for _ in range(n)]
    pair_total = 0.0
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_m(lats[i], lons[i], lats[j], lons[j])
            dists[i][j] = d
            dists[j][i] = d
            pair_total += d
            pair_count += 1

    nn1 = []
    nn5 = []
    within_500 = 0
    within_1km = 0
    for i in range(n):
        sorted_d = sorted(dists[i])
        # sorted_d[0] is self (0); take [1] for nearest other.
        if len(sorted_d) >= 2:
            nn1.append(sorted_d[1])
            if sorted_d[1] <= 500:
                within_500 += 1
            if sorted_d[1] <= 1000:
                within_1km += 1
        if len(sorted_d) >= 6:
            nn5.append(sorted_d[5])

    hull = convex_hull(proj)
    hull_area = polygon_area_km2(hull)

    return {
        "n_courts": n,
        "nn1_m_median": statistics.median(nn1) if nn1 else None,
        "nn5_m_median": statistics.median(nn5) if nn5 else None,
        "pct_within_500m": round(within_500 / n * 100, 1),
        "pct_within_1km": round(within_1km / n * 100, 1),
        "mean_pair_km": round(pair_total / pair_count / 1000, 2) if pair_count else None,
        "convex_hull_km2": round(hull_area, 2),
        "courts_per_hull_km2": round(n / hull_area, 2) if hull_area > 0.01 else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    facilities_csv = PROCESSED / f"{args.region}_tennis_facilities.csv"
    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    if not facilities_csv.exists() or not cities_csv.exists():
        print("missing inputs", file=sys.stderr)
        return 1

    cities = {int(r["rank"]): r for r in csv.DictReader(cities_csv.open())}
    facilities = list(csv.DictReader(facilities_csv.open()))
    by_city: dict[int, list[dict]] = defaultdict(list)
    for f in facilities:
        if f["kind"] == "court" and f.get("access") != "private":
            by_city[int(f["city_rank"])].append(f)

    out: list[dict] = []
    for rank in sorted(cities):
        rows = by_city.get(rank, [])
        stats = compute_city(rows)
        record = {
            "rank": rank,
            "name": cities[rank]["name"],
            "population": int(cities[rank]["population"]),
            **stats,
        }
        out.append(record)

    out_csv = PROCESSED / f"{args.region}_proximity.csv"
    fieldnames = [
        "rank", "name", "population", "n_courts",
        "nn1_m_median", "nn5_m_median",
        "pct_within_500m", "pct_within_1km",
        "mean_pair_km", "convex_hull_km2", "courts_per_hull_km2",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"wrote {out_csv} with {len(out)} cities")
    print()

    rankable = [r for r in out if r["n_courts"] and r["n_courts"] >= 5]

    def show_ranking(metric: str, title: str, asc: bool, fmt: str = "{:.0f}"):
        print(f"=== {title} ===")
        rs = [r for r in rankable if r.get(metric) is not None]
        rs.sort(key=lambda r: r[metric], reverse=not asc)
        for i, r in enumerate(rs[:15], 1):
            mark = " <-- BRIGHTON" if r["name"] == "Brighton and Hove" else ""
            print(f"  {i:>3}.  {r['name'][:26]:<26}  n={r['n_courts']:>4}  {metric}={fmt.format(r[metric])}{mark}")
        # Also show Brighton if not in top 15
        if not any(r["name"] == "Brighton and Hove" for r in rs[:15]):
            for i, r in enumerate(rs, 1):
                if r["name"] == "Brighton and Hove":
                    print(f"   ...")
                    print(f"  {i:>3}.  {r['name'][:26]:<26}  n={r['n_courts']:>4}  {metric}={fmt.format(r[metric])}  <-- BRIGHTON")
                    break
        print()

    show_ranking("nn1_m_median", "Median nearest-neighbour distance (LOWER = denser)", asc=True)
    show_ranking("nn5_m_median", "Median 5th-NN distance (LOWER = denser network)", asc=True)
    show_ranking("pct_within_500m", "% of courts with another within 500m (HIGHER = clustered)", asc=False, fmt="{:.1f}%")
    show_ranking("pct_within_1km", "% of courts with another within 1km (HIGHER = clustered)", asc=False, fmt="{:.1f}%")
    show_ranking("courts_per_hull_km2", "Courts per km² of convex hull (HIGHER = denser footprint)", asc=False, fmt="{:.2f}")
    show_ranking("mean_pair_km", "Mean pairwise court distance (LOWER = compact)", asc=True, fmt="{:.2f} km")

    return 0


if __name__ == "__main__":
    sys.exit(main())
