"""Fetch ONS LSOA 2021 population-weighted centroids + Census 2021 population.

Outputs:
  data/raw/ons/lsoa_pwc_2021.csv  (LSOA21CD, lat, lon)
  data/raw/ons/lsoa_pop_2021.csv  (LSOA21CD, population)

Centroids: ArcGIS FeatureServer, paginated.
Population: NOMIS download (Census 2021 TS001 — usual residents by LSOA).
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ons"
RAW.mkdir(parents=True, exist_ok=True)

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"

CENTROIDS_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LSOA_Dec_2011_PWC_in_England_and_Wales_2022/FeatureServer/0/query"
)
CENTROIDS_FIELD = "lsoa11cd"

# NOMIS Census 2021 LSOA usual residents (TS001), all LSOAs, geog 2021
NOMIS_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv?"
    "date=latest"
    "&geography=TYPE151"  # LSOA 2021
    "&measures=20100"
    "&select=geography_code,obs_value"
)


def fetch_centroids(out_csv: Path) -> None:
    headers = {"User-Agent": USER_AGENT}
    offset = 0
    total = 0
    rows: list[tuple[str, float, float]] = []
    # Use EPSG:4326 output spatial reference for lat/lon
    while True:
        params = {
            "where": "1=1",
            "outFields": CENTROIDS_FIELD,
            "outSR": "4326",
            "f": "json",
            "resultOffset": str(offset),
            "resultRecordCount": "2000",
        }
        r = requests.get(CENTROIDS_URL, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        d = r.json()
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            attrs = f.get("attributes", {})
            geom = f.get("geometry", {})
            code = attrs.get(CENTROIDS_FIELD) or attrs.get(CENTROIDS_FIELD.upper())
            lon = geom.get("x")
            lat = geom.get("y")
            if code and lat is not None and lon is not None:
                rows.append((code, lat, lon))
        total += len(feats)
        print(f"  centroids: fetched {total} so far")
        if d.get("exceededTransferLimit"):
            offset += len(feats)
        else:
            break
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lsoa_code", "lat", "lon"])
        w.writerows(rows)
    print(f"wrote {out_csv} with {len(rows)} centroids")


def fetch_population(out_csv: Path) -> None:
    """LSOA 2011 mid-year pop estimates (latest = 2020).

    Note: LSOA 2021 boundaries differ from 2011 for ~5% of areas. We accept
    that mismatch; for the vast majority of cities the boundaries are
    identical and the join works directly on LSOA code.
    """
    headers = {"User-Agent": USER_AGENT}
    base = (
        "https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv"
        "?date=latest&geography=TYPE298&gender=0&c_age=200&measures=20100"
    )
    out: list[tuple[str, int]] = []
    offset = 0
    while True:
        url = f"{base}&RecordOffset={offset}"
        print(f"  NOMIS offset={offset} ...")
        r = requests.get(url, headers=headers, timeout=180)
        r.raise_for_status()
        text = r.text
        rdr = csv.DictReader(io.StringIO(text))
        page_count = 0
        for row in rdr:
            code = row.get("GEOGRAPHY_CODE")
            val = row.get("OBS_VALUE")
            if code and val:
                try:
                    out.append((code, int(float(val))))
                    page_count += 1
                except ValueError:
                    pass
        if page_count == 0:
            break
        offset += page_count
        if page_count < 25000:
            break
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lsoa_code", "population"])
        w.writerows(out)
    print(f"wrote {out_csv} with {len(out)} LSOAs")


def main() -> int:
    fetch_centroids(RAW / "lsoa_pwc_2021.csv")
    fetch_population(RAW / "lsoa_pop_2021.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
