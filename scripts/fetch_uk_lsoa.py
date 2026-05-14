"""Fetch UK-wide population-weighted centroids + populations for small areas.

Combines:
  - England + Wales: LSOA 2011 PWC (ArcGIS) + LSOA 2011 mid-year pop (NOMIS)
  - Scotland:        Data Zone 2011 centroids + 2011 population (maps.gov.scot)
  - Northern Ireland: Data Zone 2021 polygons + 2021 census pop (NISRA)

Outputs: data/raw/ons/uk_pwc_pop.csv with columns
  code, country, lat, lon, population
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

EW_CENTROIDS_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LSOA_Dec_2011_PWC_in_England_and_Wales_2022/FeatureServer/0/query"
)
EW_POP_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv"
    "?date=latest&geography=TYPE298&gender=0&c_age=200&measures=20100"
)
SCOTLAND_URL = (
    "https://maps.gov.scot/server/rest/services/ScotGov/StatisticalUnits/"
    "MapServer/4/query"
)
NI_URL = (
    "https://services3.arcgis.com/HRuPlEcokYlz4mdz/arcgis/rest/services/"
    "Population_All_Usual_Residents/FeatureServer/0/query"
)


def fetch_ew(out_rows: list[tuple]) -> None:
    headers = {"User-Agent": USER_AGENT}
    print("EW: fetching LSOA 2011 PWCs ...")
    centroids: dict[str, tuple[float, float]] = {}
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "lsoa11cd",
            "outSR": "4326",
            "f": "json",
            "resultOffset": str(offset),
            "resultRecordCount": "2000",
        }
        r = requests.get(EW_CENTROIDS_URL, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        d = r.json()
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            code = f["attributes"].get("lsoa11cd") or f["attributes"].get("LSOA11CD")
            geom = f["geometry"]
            if code and geom:
                centroids[code] = (geom["y"], geom["x"])
        offset += len(feats)
        if not d.get("exceededTransferLimit"):
            break
    print(f"  EW centroids: {len(centroids):,}")

    print("EW: fetching LSOA 2011 mid-year populations ...")
    populations: dict[str, int] = {}
    offset = 0
    while True:
        url = f"{EW_POP_URL}&RecordOffset={offset}"
        r = requests.get(url, headers=headers, timeout=180)
        r.raise_for_status()
        rdr = csv.DictReader(io.StringIO(r.text))
        page_count = 0
        for row in rdr:
            code = row.get("GEOGRAPHY_CODE")
            val = row.get("OBS_VALUE")
            if code and val:
                try:
                    populations[code] = int(float(val))
                    page_count += 1
                except ValueError:
                    pass
        if page_count == 0 or page_count < 25000:
            break
        offset += page_count
    print(f"  EW populations: {len(populations):,}")

    n = 0
    for code, (lat, lon) in centroids.items():
        if code in populations:
            country = "W" if code.startswith("W") else "E"
            out_rows.append((code, country, lat, lon, populations[code]))
            n += 1
    print(f"  EW joined rows: {n:,}")


def fetch_scotland(out_rows: list[tuple]) -> None:
    headers = {"User-Agent": USER_AGENT}
    print("Scotland: fetching Data Zone 2011 centroids + pop ...")
    offset = 0
    n = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "datazone,respop2011,totpop2011",
            "outSR": "4326",
            "f": "json",
            "resultOffset": str(offset),
            "resultRecordCount": "1000",
        }
        r = requests.get(SCOTLAND_URL, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        d = r.json()
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            attrs = f["attributes"]
            geom = f["geometry"]
            code = attrs.get("datazone") or attrs.get("DATAZONE")
            pop = attrs.get("respop2011") or attrs.get("totpop2011")
            if code and pop and geom:
                out_rows.append((code, "S", geom["y"], geom["x"], int(pop)))
                n += 1
        offset += len(feats)
        if not d.get("exceededTransferLimit"):
            break
    print(f"  Scotland rows: {n:,}")


def fetch_ni(out_rows: list[tuple]) -> None:
    headers = {"User-Agent": USER_AGENT}
    print("NI: fetching Data Zone 2021 polygons + Census 2021 pop ...")
    offset = 0
    n = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "DZ2021_cd,All_usual_",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
            "resultOffset": str(offset),
            "resultRecordCount": "2000",
        }
        r = requests.get(NI_URL, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        d = r.json()
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            attrs = f["attributes"]
            geom = f.get("geometry", {})
            code = attrs.get("DZ2021_cd")
            pop = attrs.get("All_usual_")
            if not code or pop is None or "rings" not in geom:
                continue
            coords = geom["rings"][0]
            cx = sum(c[0] for c in coords) / len(coords)
            cy = sum(c[1] for c in coords) / len(coords)
            out_rows.append((code, "NI", cy, cx, int(pop)))
            n += 1
        offset += len(feats)
        if not d.get("exceededTransferLimit"):
            break
    print(f"  NI rows: {n:,}")


def main() -> int:
    rows: list[tuple] = []
    fetch_ew(rows)
    fetch_scotland(rows)
    fetch_ni(rows)
    out = RAW / "uk_pwc_pop.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "country", "lat", "lon", "population"])
        w.writerows(rows)
    print(f"\nwrote {out} with {len(rows):,} small-area rows ({sum(1 for r in rows if r[1]=='E')} E, "
          f"{sum(1 for r in rows if r[1]=='W')} W, {sum(1 for r in rows if r[1]=='S')} S, "
          f"{sum(1 for r in rows if r[1]=='NI')} NI)")
    print(f"total population coverage: {sum(r[4] for r in rows):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
