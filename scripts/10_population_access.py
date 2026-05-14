"""Population-weighted accessibility per city.

For each city, find the LSOAs whose population-weighted centroids fall inside
the city's Nominatim bbox. For each such LSOA, compute the distance from its
centroid to the nearest non-private court IN THAT CITY. Then compute the
population-weighted fraction of residents within X metres of a court.

Inputs:
  data/raw/ons/lsoa_pwc_2021.csv      -- LSOA21CD, lat, lon (35,672)
  data/raw/ons/lsoa_pop_2011.csv      -- LSOA 2011 code, population (34,753)
  data/processed/uk_cities.csv        -- city bbox
  data/processed/uk_tennis_facilities.csv -- court coordinates

Caveats:
  - LSOA 2011 vs 2021 boundaries differ for ~5% of areas; we inner-join on
    code and skip the rest. For UK cities of >100k this is a tiny effect.
  - This dataset is England + Wales only. UK cities in Scotland (Glasgow,
    Edinburgh, Aberdeen, Dundee, Motherwell) and Northern Ireland (Belfast)
    will not have pop-weighted access reported.
  - LSOAs assigned to a city by bbox containment of their PWC. For very large
    metro bboxes this may include some peri-urban LSOAs; documented.

Output:
  data/processed/uk_pop_access.csv with per-city: pop_in_bbox, lsoa_n,
  pct_pop_within_500m, pct_pop_within_1km, pct_pop_within_2km, median_distance_m.
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
ONS = ROOT / "data" / "raw" / "ons"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def project_eq(lats: list[float], lons: list[float], lat0: float, lon0: float) -> list[tuple[float, float]]:
    cos0 = math.cos(math.radians(lat0))
    R = 6_371_000.0
    return [
        (math.radians(lon - lon0) * cos0 * R, math.radians(lat - lat0) * R)
        for lat, lon in zip(lats, lons)
    ]


def show_ranking(rows: list[dict], metric: str, title: str, asc: bool, fmt: str = "{:.0f}"):
    print(f"=== {title} ===")
    items = [r for r in rows if r.get(metric) is not None]
    items.sort(key=lambda r: r[metric], reverse=not asc)
    shown = []
    for i, r in enumerate(items[:15], 1):
        mark = " <-- BRIGHTON" if r["name"] == "Brighton and Hove" else ""
        v = fmt.format(r[metric])
        shown.append(r["name"])
        print(f"  {i:>3}.  {r['name'][:26]:<26}  pop={r['population']:>10,}  bbox_pop={int(r.get('pop_in_bbox',0)):>10,}  lsoas={r.get('lsoa_n',0):>5}  {metric}={v}{mark}")
    if "Brighton and Hove" not in shown:
        for i, r in enumerate(items, 1):
            if r["name"] == "Brighton and Hove":
                print("   ...")
                v = fmt.format(r[metric])
                print(f"  {i:>3}.  {r['name'][:26]:<26}  pop={r['population']:>10,}  bbox_pop={int(r.get('pop_in_bbox',0)):>10,}  lsoas={r.get('lsoa_n',0):>5}  {metric}={v}  <-- BRIGHTON")
                break
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    # Load unified UK-wide small-area centroids + populations
    # (E+W LSOA 2011, Scotland DZ 2011, NI DZ 2021)
    joined: dict[str, dict] = {}
    by_country = {"E": 0, "W": 0, "S": 0, "NI": 0}
    with (ONS / "uk_pwc_pop.csv").open() as f:
        for r in csv.DictReader(f):
            joined[r["code"]] = {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "pop": int(r["population"]),
                "country": r["country"],
            }
            by_country[r["country"]] = by_country.get(r["country"], 0) + 1
    print(f"loaded {len(joined):,} small areas: "
          f"E={by_country['E']:,} W={by_country['W']:,} "
          f"S={by_country['S']:,} NI={by_country['NI']:,}")

    # Load cities
    cities = list(csv.DictReader((PROCESSED / f"{args.region}_cities.csv").open()))

    # Load courts
    facilities = list(csv.DictReader((PROCESSED / f"{args.region}_tennis_facilities.csv").open()))
    courts_by_city: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for f in facilities:
        if f["kind"] == "court" and f.get("access") != "private":
            courts_by_city[int(f["city_rank"])].append((float(f["lat"]), float(f["lon"])))

    out: list[dict] = []
    for city in cities:
        rank = int(city["rank"])
        name = city["name"]
        pop_total = int(city["population"])
        if not city["bbox_south"]:
            out.append({"rank": rank, "name": name, "population": pop_total, "note": "no bbox"})
            continue
        s, w, n_, e = (
            float(city["bbox_south"]),
            float(city["bbox_west"]),
            float(city["bbox_north"]),
            float(city["bbox_east"]),
        )
        # Find LSOAs whose centroid falls in the city's bbox
        in_bbox = []
        for code, info in joined.items():
            if s <= info["lat"] <= n_ and w <= info["lon"] <= e:
                in_bbox.append(info)
        if not in_bbox:
            out.append({
                "rank": rank, "name": name, "population": pop_total,
                "lsoa_n": 0, "note": "no LSOAs in bbox (Scotland/NI?)",
            })
            continue
        # Project LSOAs and courts in same equirectangular plane
        court_pts = courts_by_city.get(rank, [])
        if len(court_pts) < 5:
            out.append({
                "rank": rank, "name": name, "population": pop_total,
                "lsoa_n": len(in_bbox),
                "note": f"only {len(court_pts)} non-private courts",
            })
            continue
        all_lats = [x["lat"] for x in in_bbox] + [p[0] for p in court_pts]
        all_lons = [x["lon"] for x in in_bbox] + [p[1] for p in court_pts]
        lat0 = sum(all_lats) / len(all_lats)
        lon0 = sum(all_lons) / len(all_lons)
        lsoa_proj = project_eq([x["lat"] for x in in_bbox], [x["lon"] for x in in_bbox], lat0, lon0)
        court_proj = project_eq([p[0] for p in court_pts], [p[1] for p in court_pts], lat0, lon0)

        pop_total_bbox = 0
        pop_500 = 0
        pop_1000 = 0
        pop_2000 = 0
        weighted_dist_total = 0.0
        per_lsoa_dists: list[tuple[float, int]] = []
        for (sx, sy), info in zip(lsoa_proj, in_bbox):
            best = float("inf")
            for cx, cy in court_proj:
                d2 = (sx - cx) ** 2 + (sy - cy) ** 2
                if d2 < best:
                    best = d2
            d = math.sqrt(best)
            p = info["pop"]
            pop_total_bbox += p
            weighted_dist_total += d * p
            per_lsoa_dists.append((d, p))
            if d <= 500:
                pop_500 += p
            if d <= 1000:
                pop_1000 += p
            if d <= 2000:
                pop_2000 += p

        # Pop-weighted median distance
        per_lsoa_dists.sort(key=lambda x: x[0])
        cumulative = 0
        median_d = 0.0
        for d, p in per_lsoa_dists:
            cumulative += p
            if cumulative >= pop_total_bbox / 2:
                median_d = d
                break

        out.append({
            "rank": rank,
            "name": name,
            "population": pop_total,
            "lsoa_n": len(in_bbox),
            "pop_in_bbox": pop_total_bbox,
            "pct_pop_within_500m": round(pop_500 / pop_total_bbox * 100, 1),
            "pct_pop_within_1km": round(pop_1000 / pop_total_bbox * 100, 1),
            "pct_pop_within_2km": round(pop_2000 / pop_total_bbox * 100, 1),
            "median_distance_m": int(median_d),
            "mean_distance_m": int(weighted_dist_total / pop_total_bbox),
        })

    out_csv = PROCESSED / f"{args.region}_pop_access.csv"
    fieldnames = [
        "rank", "name", "population", "lsoa_n", "pop_in_bbox",
        "pct_pop_within_500m", "pct_pop_within_1km", "pct_pop_within_2km",
        "median_distance_m", "mean_distance_m",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"wrote {out_csv}\n")

    rankable = [r for r in out if r.get("pct_pop_within_1km") is not None]
    print(f"ranked {len(rankable)} of {len(out)} cities\n")

    show_ranking(rankable, "pct_pop_within_500m",
                 "% of city residents within 500m of a tennis court (UK)",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "pct_pop_within_1km",
                 "% of city residents within 1km of a tennis court",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "pct_pop_within_2km",
                 "% of city residents within 2km of a tennis court",
                 asc=False, fmt="{:.1f}%")
    show_ranking(rankable, "median_distance_m",
                 "Population-weighted median distance to nearest court (LOWER = closer for typical resident)",
                 asc=True, fmt="{:.0f} m")

    return 0


if __name__ == "__main__":
    sys.exit(main())
