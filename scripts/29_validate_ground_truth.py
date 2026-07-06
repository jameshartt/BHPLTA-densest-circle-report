"""Validate data/processed/ground_truth.csv — the canonical Step 6 / Step 7
table — for internal arithmetic consistency, and cross-check the headline
numbers quoted in reports/densest_circle_full_writeup.md.

Checks:
  1. delta == gt_count − osm_strict
  2. adminclip_density == gt_count / adminclip_land_km2  (±0.01)
  3. fair_land_km2 == DISC_KM2 − disc_water_km2          (±0.01)
  4. fair_density == gt_count / fair_land_km2            (±0.01)
  5. the writeup quotes every fair_density and adminclip_density value

Exit code 0 = all good; 1 = at least one failure (printed).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "processed" / "ground_truth.csv"
WRITEUP = ROOT / "reports" / "densest_circle_full_writeup.md"

DISC_KM2 = 17.15  # pi * 2.33678^2 (SEC radius of the Brighton anchors)
TOL = 0.011


def main() -> int:
    failures: list[str] = []
    rows = list(csv.DictReader(CSV_PATH.open()))
    text = WRITEUP.read_text()

    for r in rows:
        city = r["city"]
        strict, gt = int(r["osm_strict"]), int(r["gt_count"])

        delta = int(r["delta"].replace("−", "-").replace("+", ""))
        if delta != gt - strict:
            failures.append(f"{city}: delta {delta} != {gt}-{strict}")

        if r["adminclip_land_km2"]:
            land = float(r["adminclip_land_km2"])
            want = gt / land
            got = float(r["adminclip_density"])
            if abs(want - got) > TOL:
                failures.append(
                    f"{city}: adminclip {got} != {gt}/{land} = {want:.3f}")

        water = float(r["disc_water_km2"])
        fair_land = float(r["fair_land_km2"])
        if abs((DISC_KM2 - water) - fair_land) > TOL:
            failures.append(
                f"{city}: fair_land {fair_land} != {DISC_KM2}-{water}")
        want = gt / fair_land
        got = float(r["fair_density"])
        if abs(want - got) > TOL:
            failures.append(
                f"{city}: fair_density {got} != {gt}/{fair_land} = {want:.3f}")

        for col in ("adminclip_density", "fair_density"):
            val = r[col]
            if val and val not in text:
                failures.append(f"{city}: {col} {val} not quoted in writeup")

    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"OK: {len(rows)} cities, all arithmetic + writeup cross-checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
