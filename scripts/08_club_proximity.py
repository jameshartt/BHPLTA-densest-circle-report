"""Club-level proximity stats.

Court-level metrics are dominated by multi-court facilities (adjacent courts at
the same club). For "community vibrancy" -- how many DISTINCT venues a player
can reach -- the right unit is the facility/club, not the individual court.

For each city we compute, using non-private club centroids only:

  - club_n                       count of non-private clubs/facilities
  - nn1_club_m_median            median nearest-other-club distance
  - other_clubs_within_1km_med   median count of OTHER clubs within 1km of a club
  - other_clubs_within_2km_med   ditto for 2km (~25-min walk)
  - other_clubs_within_5km_med   ditto for 5km (~15-min cycle)
  - pct_clubs_with_neighbour_2km % of clubs with at least one other within 2km
  - club_pairs_under_2km         total pairs of clubs within 2km (network edges)
  - clubs_per_hull_km2           clubs per km^2 of the convex hull of clubs

Cities with <3 clubs are skipped.

Outputs data/processed/uk_club_proximity.csv plus a printed ranking summary
that always shows Brighton's position.
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


def hull_area_km2(hull: list[tuple[float, float]]) -> float:
    if len(hull) < 3:
        return 0.0
    s = 0.0
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 / 1_000_000


def compute_city(clubs: list[dict]) -> dict:
    n = len(clubs)
    if n < 3:
        return {"club_n": n}

    lats = [float(c["lat"]) for c in clubs]
    lons = [float(c["lon"]) for c in clubs]
    lat0 = sum(lats) / n
    lon0 = sum(lons) / n
    cos0 = math.cos(math.radians(lat0))
    R = 6_371_000.0
    proj = [
        (math.radians(lon - lon0) * cos0 * R, math.radians(lat - lat0) * R)
        for lat, lon in zip(lats, lons)
    ]

    dists = [[0.0] * n for _ in range(n)]
    pair_under_2km = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_m(lats[i], lons[i], lats[j], lons[j])
            dists[i][j] = d
            dists[j][i] = d
            if d < 2000:
                pair_under_2km += 1

    nn1 = []
    counts_500m = []
    counts_1km = []
    counts_2km = []
    counts_5km = []
    has_neighbour_2km = 0
    for i in range(n):
        sd = sorted(dists[i])
        # sd[0] is self at 0
        if len(sd) >= 2:
            nn1.append(sd[1])
        c500 = sum(1 for d in dists[i] if 0 < d < 500)
        c1k = sum(1 for d in dists[i] if 0 < d < 1000)
        c2k = sum(1 for d in dists[i] if 0 < d < 2000)
        c5k = sum(1 for d in dists[i] if 0 < d < 5000)
        counts_500m.append(c500)
        counts_1km.append(c1k)
        counts_2km.append(c2k)
        counts_5km.append(c5k)
        if c2k >= 1:
            has_neighbour_2km += 1

    hull = convex_hull(proj)
    hull_a = hull_area_km2(hull)

    return {
        "club_n": n,
        "nn1_club_m_median": int(statistics.median(nn1)) if nn1 else None,
        "other_clubs_within_500m_med": statistics.median(counts_500m),
        "other_clubs_within_1km_med": statistics.median(counts_1km),
        "other_clubs_within_2km_med": statistics.median(counts_2km),
        "other_clubs_within_5km_med": statistics.median(counts_5km),
        "pct_clubs_with_neighbour_2km": round(has_neighbour_2km / n * 100, 1),
        "club_pairs_under_2km": pair_under_2km,
        "clubs_per_hull_km2": round(n / hull_a, 2) if hull_a > 0.05 else None,
    }


def show_ranking(rs: list[dict], metric: str, title: str, asc: bool, fmt: str = "{:.0f}"):
    print(f"=== {title} ===")
    items = [r for r in rs if r.get(metric) is not None]
    items.sort(key=lambda r: r[metric], reverse=not asc)
    shown = []
    for i, r in enumerate(items[:15], 1):
        mark = " <-- BRIGHTON" if r["name"] == "Brighton and Hove" else ""
        v = fmt.format(r[metric])
        shown.append(r["name"])
        print(f"  {i:>3}.  {r['name'][:26]:<26}  clubs={r['club_n']:>3}  pop={r['population']:>10,}  {metric}={v}{mark}")
    if "Brighton and Hove" not in shown:
        for i, r in enumerate(items, 1):
            if r["name"] == "Brighton and Hove":
                print("   ...")
                v = fmt.format(r[metric])
                print(f"  {i:>3}.  {r['name'][:26]:<26}  clubs={r['club_n']:>3}  pop={r['population']:>10,}  {metric}={v}  <-- BRIGHTON")
                break
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    cities_csv = PROCESSED / f"{args.region}_cities.csv"
    clubs_csv = PROCESSED / f"{args.region}_clubs.csv"
    if not cities_csv.exists() or not clubs_csv.exists():
        print("missing inputs", file=sys.stderr)
        return 1

    cities = {int(r["rank"]): r for r in csv.DictReader(cities_csv.open())}
    clubs = list(csv.DictReader(clubs_csv.open()))

    by_city: dict[int, list[dict]] = defaultdict(list)
    for c in clubs:
        if c["primary_access"] == "private":
            continue
        if int(c["members_only"]):
            continue
        by_city[int(c["city_rank"])].append(c)

    out: list[dict] = []
    for rank in sorted(cities):
        city_clubs = by_city.get(rank, [])
        stats = compute_city(city_clubs)
        out.append({
            "rank": rank,
            "name": cities[rank]["name"],
            "population": int(cities[rank]["population"]),
            **stats,
        })

    out_csv = PROCESSED / f"{args.region}_club_proximity.csv"
    fieldnames = [
        "rank", "name", "population", "club_n",
        "nn1_club_m_median",
        "other_clubs_within_500m_med",
        "other_clubs_within_1km_med",
        "other_clubs_within_2km_med",
        "other_clubs_within_5km_med",
        "pct_clubs_with_neighbour_2km",
        "club_pairs_under_2km",
        "clubs_per_hull_km2",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"wrote {out_csv} with {len(out)} cities\n")

    rankable = [r for r in out if r["club_n"] and r["club_n"] >= 5]

    show_ranking(rankable, "nn1_club_m_median",
                 "Median nearest-OTHER-club distance (LOWER = denser network)",
                 asc=True, fmt="{:.0f} m")
    show_ranking(rankable, "other_clubs_within_2km_med",
                 "Median # of OTHER clubs within 2km of a club (~25-min walk)",
                 asc=False, fmt="{:.1f}")
    show_ranking(rankable, "other_clubs_within_1km_med",
                 "Median # of OTHER clubs within 1km of a club (~12-min walk)",
                 asc=False, fmt="{:.1f}")
    show_ranking(rankable, "other_clubs_within_5km_med",
                 "Median # of OTHER clubs within 5km of a club (~cyclable)",
                 asc=False, fmt="{:.1f}")
    show_ranking(rankable, "pct_clubs_with_neighbour_2km",
                 "% of clubs with at least one OTHER club within 2km",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "clubs_per_hull_km2",
                 "Clubs per km² of footprint (clubs/hull-area)",
                 asc=False, fmt="{:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
