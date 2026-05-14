"""Cluster individual tennis courts into clubs/facilities.

Reads data/processed/uk_tennis_facilities.csv (raw flat OSM elements per city)
and emits data/processed/uk_clubs.csv:

  city_rank, city_name, club_id, club_name, court_count, lat, lon,
  has_sports_centre, has_club_tag, has_private_court, members_only,
  primary_access, surfaces

Clustering policy:
- All elements with kind in {court, sports_centre, tennis_club} are candidates.
- Cluster by greedy proximity union-find: two elements link if within EPS_M (75m).
- One cluster = one club/facility.
- court_count = number of elements with kind=court in the cluster (sports_centre
  on its own without distinct pitch ways may be a single multi-court site -- if
  no pitch elements link to it, we treat it as a single facility but count
  tennis:courts tag or default to 2 as a fallback heuristic).

Access policy for the club:
- If any element in cluster has access=private and NO public/customers element:
    primary_access = private  -> EXCLUDED from main stats (but counted separately)
- If access=members on all elements with explicit access: members_only=True
- Otherwise: primary_access in {public, customers, yes, permissive, unknown}.
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

EPS_M = 75.0  # cluster radius


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def cluster_city(rows: list[dict]) -> list[dict]:
    n = len(rows)
    dsu = DSU(n)
    # O(n^2) is fine — typical city <500 elements
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_m(
                float(rows[i]["lat"]),
                float(rows[i]["lon"]),
                float(rows[j]["lat"]),
                float(rows[j]["lon"]),
            )
            if d <= EPS_M:
                dsu.union(i, j)

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[dsu.find(i)].append(i)
    return [
        {"members": [rows[i] for i in idxs]} for idxs in clusters.values()
    ]


def summarize_cluster(cluster: dict, city_rank: int, city_name: str, club_id: int) -> dict:
    members = cluster["members"]
    courts = [m for m in members if m["kind"] == "court"]
    sports_centres = [m for m in members if m["kind"] == "sports_centre"]
    club_tags = [m for m in members if m["kind"] == "tennis_club"]

    # Infer court count
    if courts:
        # Sum tennis:courts tag where present (parent pitch ways tagged with N courts)
        # Otherwise treat each pitch as 1 court.
        total = 0
        for c in courts:
            tag = c.get("tennis_courts_tag", "")
            try:
                n = int(tag) if tag else 1
            except ValueError:
                n = 1
            total += n
        court_count = total
    elif sports_centres:
        # sports_centre without any pitch element — try the tag, else assume 2
        total = 0
        for sc in sports_centres:
            tag = sc.get("tennis_courts_tag", "")
            try:
                total += int(tag) if tag else 0
            except ValueError:
                pass
        court_count = total if total > 0 else 2  # heuristic fallback
    elif club_tags:
        court_count = 2  # club node with no mapped courts; conservative fallback
    else:
        court_count = 0

    # Aggregate access
    accesses = {m["access"] for m in members if m["access"]}
    has_private = "private" in accesses
    has_public_signal = bool(accesses & {"public", "customers", "yes", "permissive"})
    members_only = bool(accesses) and accesses.issubset({"members"})
    if has_private and not has_public_signal and not (accesses - {"private"}):
        primary_access = "private"
    elif members_only:
        primary_access = "members"
    elif accesses & {"public", "yes", "permissive"}:
        primary_access = "public"
    elif "customers" in accesses:
        primary_access = "customers"
    else:
        primary_access = "unknown"

    # Centroid
    lat = sum(float(m["lat"]) for m in members) / len(members)
    lon = sum(float(m["lon"]) for m in members) / len(members)

    name = ""
    operators = []
    surfaces = set()
    for m in members:
        if m.get("name"):
            if not name:
                name = m["name"]
            elif m["name"] != name:
                pass
        if m.get("operator"):
            operators.append(m["operator"])
        if m.get("surface"):
            surfaces.add(m["surface"])

    return {
        "city_rank": city_rank,
        "city_name": city_name,
        "club_id": f"{city_rank:03d}_{club_id:04d}",
        "club_name": name,
        "court_count": court_count,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "has_sports_centre": int(bool(sports_centres)),
        "has_club_tag": int(bool(club_tags)),
        "primary_access": primary_access,
        "members_only": int(members_only),
        "surfaces": ";".join(sorted(surfaces)),
        "element_count": len(members),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    in_csv = PROCESSED / f"{args.region}_tennis_facilities.csv"
    out_csv = PROCESSED / f"{args.region}_clubs.csv"

    if not in_csv.exists():
        print(f"missing {in_csv}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(in_csv.open()))
    by_city: dict[int, list[dict]] = defaultdict(list)
    city_names: dict[int, str] = {}
    for r in rows:
        rank = int(r["city_rank"])
        by_city[rank].append(r)
        city_names[rank] = r["city_name"]

    all_clubs: list[dict] = []
    for rank, city_rows in sorted(by_city.items()):
        clusters = cluster_city(city_rows)
        # Sort clusters by court count desc for stable IDs
        clusters.sort(key=lambda c: -len(c["members"]))
        for i, cl in enumerate(clusters):
            summary = summarize_cluster(cl, rank, city_names[rank], i)
            all_clubs.append(summary)
        print(f"[{rank:3d}] {city_names[rank]}: {len(city_rows)} elements -> {len(clusters)} clubs")

    fieldnames = [
        "city_rank",
        "city_name",
        "club_id",
        "club_name",
        "court_count",
        "lat",
        "lon",
        "has_sports_centre",
        "has_club_tag",
        "primary_access",
        "members_only",
        "surfaces",
        "element_count",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in all_clubs:
            w.writerow(row)
    print(f"\nwrote {out_csv} with {len(all_clubs)} clubs across {len(by_city)} cities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
