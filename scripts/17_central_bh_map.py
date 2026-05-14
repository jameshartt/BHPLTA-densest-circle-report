"""Map of Brighton & Hove's Central B&H circle with park-courts highlighted.

Carto Positron basemap, the SEC circle drawn, park courts as pink dots,
non-park courts as faint white dots.
"""

from __future__ import annotations

import csv
import io
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import json as _json
import requests
from PIL import Image
from shapely.geometry import Polygon as ShPolygon, MultiPolygon as ShMultiPolygon
from shapely.ops import transform as sh_transform
import pyproj

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
IMAGERY = ROOT / "data" / "imagery"

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
BRIGHTON_PINK = "#e3174a"
BRIGHTON_DEEP = "#9d0f33"

# Anchor points — parks-league venues that define / sit inside the circle
QUEENS = (50.82536, -0.12322)       # Queens Park (east anchor — way 127064771, the southernmost-east court, so all 6 Queens courts fit inside)
KINGSWAY = (50.82598, -0.18975)     # Kingsway / Hove Beach Park (west anchor)
BLAKERS = (50.84220, -0.13769)      # Blakers Park (north anchor)
ST_ANNS = (50.83059, -0.15764)      # St Ann's Well Gardens (BHPLTA member's club)
# Hollingbury Park — parks-league venue outside the central circle.
# BHCC-listed park; OSM has the courts mapped (Court 1..6) but the park
# boundary isn't tagged as `leisure=park`, so the strict filter misses
# them. (The 2 OSM courts ~1.5 km north at 50.865 are the now-defunct
# Rookery Tennis Club and are NOT Hollingbury Park.)
HOLLINGBURY = (50.84920, -0.13440)
# Club sites the circle passes through — shown for orientation only,
# not parks-league venues
PAVILION = (50.84273, -0.16094)     # Pavilion & Avenue Tennis Club (club)
PRESTON = (50.84293, -0.14888)      # Preston Lawn Tennis Club (club)

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
    lat0 = (p1[0] + p2[0] + p3[0]) / 3
    lon0 = (p1[1] + p2[1] + p3[1]) / 3
    cos_lat0 = math.cos(math.radians(lat0))
    def to_xy(p):
        return ((p[1] - lon0) * 111_320.0 * cos_lat0,
                (p[0] - lat0) * 111_320.0)
    x1, y1 = to_xy(p1); x2, y2 = to_xy(p2); x3, y3 = to_xy(p3)
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
    n = len(points)
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            c = midpoint(points[i], points[j])
            r = haversine_m(*c, *points[i])
            if all(haversine_m(*c, *p) <= r + 1.0 for p in points):
                if best is None or r < best[2]:
                    best = (c[0], c[1], r)
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
    return best


def deg2num_float(lat, lon, z):
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def num2deg(xt, yt, z):
    n = 2.0 ** z
    lon = xt / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yt / n))))
    return lat, lon


def fetch_tile(x, y, z):
    cache = IMAGERY / "carto" / f"z{z}_x{x}_y{y}.png"
    if cache.exists():
        try:
            return Image.open(cache).convert("RGB")
        except Exception:
            cache.unlink(missing_ok=True)
    url = f"https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        r.raise_for_status()
    except requests.RequestException:
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(r.content)
    try:
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def main() -> int:
    # Three parks-league anchors define the circle; P&A and Preston (clubs)
    # happen to lie inside it.
    sec_lat, sec_lon, sec_r = smallest_enclosing_circle(
        [QUEENS, KINGSWAY, BLAKERS])
    print(f"circle: centre=({sec_lat:.5f},{sec_lon:.5f})  radius={sec_r:.0f} m")

    # Land-area data (pre-computed by 19_land_area.py)
    land_path = ROOT / "data" / "processed" / "brighton_circle_land.json"
    land_info = _json.loads(land_path.read_text()) if land_path.exists() else None

    # Build the land-clipped circle for drawing
    ua_path = ROOT / "data" / "raw" / "overpass" / "uk" / "brighton_ua.json"
    land_poly_latlon = None
    if ua_path.exists():
        ua_data = _json.loads(ua_path.read_text())
        # Use the build_ua_polygon logic from 19_land_area.py
        rel = ua_data["elements"][0]
        outer_rings = []
        for m in rel.get("members", []):
            if m.get("role") == "outer" and "geometry" in m:
                outer_rings.append([(n["lon"], n["lat"]) for n in m["geometry"]])

        def _stitch(segments):
            rings = []; remaining = [list(s) for s in segments]
            while remaining:
                ring = remaining.pop(0)
                while ring[0] != ring[-1] and remaining:
                    att = False
                    for i, s in enumerate(remaining):
                        if s[0] == ring[-1]:
                            ring.extend(s[1:]); remaining.pop(i); att = True; break
                        if s[-1] == ring[-1]:
                            ring.extend(s[-2::-1]); remaining.pop(i); att = True; break
                        if s[0] == ring[0]:
                            ring = list(reversed(s))[:-1] + ring; remaining.pop(i); att = True; break
                        if s[-1] == ring[0]:
                            ring = s[:-1] + ring; remaining.pop(i); att = True; break
                    if not att: break
                if ring[0] == ring[-1] and len(ring) >= 4:
                    rings.append(ring)
            return rings

        outer_closed = _stitch(outer_rings)
        polys = []
        for outer in outer_closed:
            try:
                p = ShPolygon(outer)
                if p.is_valid:
                    polys.append(p)
            except Exception:
                pass
        ua = polys[0] if len(polys) == 1 else ShMultiPolygon(polys)

        project_to_local = pyproj.Transformer.from_crs(
            "EPSG:4326",
            f"+proj=aeqd +lat_0={sec_lat} +lon_0={sec_lon} +datum=WGS84 +units=m",
            always_xy=True,
        ).transform
        project_back = pyproj.Transformer.from_crs(
            f"+proj=aeqd +lat_0={sec_lat} +lon_0={sec_lon} +datum=WGS84 +units=m",
            "EPSG:4326",
            always_xy=True,
        ).transform

        local_circle = ShPolygon([(sec_r * math.cos(math.radians(a)),
                                   sec_r * math.sin(math.radians(a))) for a in range(0, 360)])
        ua_local = sh_transform(project_to_local, ua)
        land_local = local_circle.intersection(ua_local)
        land_poly_latlon = sh_transform(project_back, land_local)

    facilities_path = PROCESSED / "uk_tennis_facilities_parks_v2.csv"
    if not facilities_path.exists():
        facilities_path = PROCESSED / "uk_tennis_facilities_parks.csv"
    if not facilities_path.exists():
        facilities_path = PROCESSED / "uk_tennis_facilities.csv"
    rows = list(csv.DictReader(facilities_path.open()))
    bh = [r for r in rows if r["city_name"] == "Brighton and Hove" and r["kind"] == "court" and r["access"] != "private"]

    # Ground-truth overrides for OSM gaps where BHCC manages the area as a
    # park but OSM doesn't tag it as `leisure=park`:
    #   - Hove Beach Park (Kingsway / former King Alfred site)
    #   - Hollingbury Park (north of the circle)
    def is_kingsway(r):
        lat, lon = float(r["lat"]), float(r["lon"])
        return 50.825 < lat < 50.828 and -0.192 < lon < -0.187

    def is_hollingbury(r):
        # Real Hollingbury Park courts (the "Court 1..6" cluster). The
        # bbox is tightened so that Varndean School's tennis court at
        # (50.8500, -0.1384) — a school court, not parks-league — is
        # excluded.
        lat, lon = float(r["lat"]), float(r["lon"])
        return 50.848 < lat < 50.850 and -0.136 < lon < -0.132

    park_courts = []
    other_courts = []
    for r in bh:
        is_park = (r.get("park_public") == "1") or is_kingsway(r) or is_hollingbury(r)
        if is_park:
            park_courts.append(r)
        else:
            other_courts.append(r)

    # Bounding box for map: circle ± a small pad, slightly extended north
    # so Hollingbury Park (the actual parks-league site at lat ~50.849)
    # sits comfortably within the frame rather than at the edge.
    pad_lat = (sec_r * 1.25) / 111_320.0
    pad_lon = pad_lat / max(math.cos(math.radians(sec_lat)), 0.1)
    minlat = sec_lat - pad_lat
    maxlat = max(sec_lat + pad_lat, HOLLINGBURY[0] + 0.004)
    minlon = sec_lon - pad_lon
    maxlon = sec_lon + pad_lon

    zoom = 14
    x_min, y_max = deg2num_float(minlat, minlon, zoom)
    x_max, y_min = deg2num_float(maxlat, maxlon, zoom)
    x_lo, x_hi = int(math.floor(x_min)), int(math.ceil(x_max))
    y_lo, y_hi = int(math.floor(y_min)), int(math.ceil(y_max))
    cols = x_hi - x_lo
    rows_ = y_hi - y_lo
    canvas = Image.new("RGB", (cols * 256, rows_ * 256), color=(245, 246, 248))
    for dx in range(cols):
        for dy in range(rows_):
            t = fetch_tile(x_lo + dx, y_lo + dy, zoom)
            if t is not None:
                canvas.paste(t, (dx * 256, dy * 256))
    canvas_minlat, canvas_minlon = num2deg(x_lo, y_hi, zoom)
    canvas_maxlat, canvas_maxlon = num2deg(x_hi, y_lo, zoom)

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(canvas, extent=(canvas_minlon, canvas_maxlon, canvas_minlat, canvas_maxlat),
              aspect="auto", interpolation="bilinear")

    # Parks-league anchor stars (Queens, Kingsway, Blakers, St Ann's — all
    # parks venues). Plus orientation stars for the two clubs the circle
    # happens to pass through (P&A, Preston LTC), drawn fainter.
    # Labels only — no stars (they would obscure the court dots).
    # Parks-league venues in bold pink, club sites in faint grey italic.
    HOVE_PARK = (50.84005, -0.17260)
    DYKE_ROAD = (50.83760, -0.15470)
    PRESTON_PARK = (50.83870, -0.14580)
    parks_labels = [
        (QUEENS,        "Queens Park",        ( 12,   6)),
        (KINGSWAY,      "Kingsway / Hove Beach Park", (10,   6)),
        (BLAKERS,       "Blakers Park",       ( 10,   6)),
        (ST_ANNS,       "St Ann's Well Gardens", (10,   6)),
        (HOLLINGBURY,   "Hollingbury Park",   ( 12,   6)),
        (HOVE_PARK,     "Hove Park",          ( 12,   6)),
        (DYKE_ROAD,     "Dyke Road Park",     ( 12,  -14)),
        (PRESTON_PARK,  "Preston Park",       ( 12,    6)),
    ]
    club_labels = [
        (PAVILION, "Pavilion & Avenue", (10, 6)),
        (PRESTON,  "Preston LTC",       (10, 6)),
    ]
    for p, label, (dx, dy) in parks_labels:
        ax.annotate(label, (p[1], p[0]), xytext=(dx, dy),
                    textcoords="offset points",
                    fontsize=10, fontweight="bold",
                    color=BRIGHTON_DEEP, zorder=6,
                    bbox=dict(facecolor="white", alpha=0.75, edgecolor="none",
                              boxstyle="round,pad=0.18"))
    for p, label, (dx, dy) in club_labels:
        ax.annotate(label, (p[1], p[0]), xytext=(dx, dy),
                    textcoords="offset points",
                    fontsize=9, style="italic", color="#666", zorder=6,
                    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none",
                              boxstyle="round,pad=0.15"))

    # Draw circle outline
    r_lat_deg = sec_r / 111_320.0
    r_lon_deg = sec_r / (111_320.0 * math.cos(math.radians(sec_lat)))
    angles = [math.radians(a) for a in range(0, 361, 2)]
    xs = [sec_lon + r_lon_deg * math.cos(a) for a in angles]
    ys = [sec_lat + r_lat_deg * math.sin(a) for a in angles]
    ax.plot(xs, ys, color=BRIGHTON_PINK, linewidth=2.5, alpha=0.85, zorder=4)

    # Fill ONLY the land portion (clipped to UA polygon)
    if land_poly_latlon is not None:
        geoms = land_poly_latlon.geoms if hasattr(land_poly_latlon, "geoms") else [land_poly_latlon]
        for g in geoms:
            if g.geom_type != "Polygon":
                continue
            xs_p, ys_p = zip(*list(g.exterior.coords))
            ax.fill(xs_p, ys_p, color=BRIGHTON_PINK, alpha=0.13, zorder=3)
    else:
        ax.fill(xs, ys, color=BRIGHTON_PINK, alpha=0.07, zorder=3)

    # Park courts
    pc_lats = [float(r["lat"]) for r in park_courts]
    pc_lons = [float(r["lon"]) for r in park_courts]
    in_circle_park = sum(1 for r in park_courts if haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)
    ax.scatter(pc_lons, pc_lats, s=46, color=BRIGHTON_PINK, edgecolor="white",
               linewidth=0.8, alpha=0.95, zorder=4,
               label=f"Park courts ({len(park_courts)} city-wide)")

    # Non-park (clubs / outside parks)
    oc_lats = [float(r["lat"]) for r in other_courts]
    oc_lons = [float(r["lon"]) for r in other_courts]
    ax.scatter(oc_lons, oc_lats, s=32, facecolor="white", edgecolor="#666",
               linewidth=0.8, alpha=0.85, zorder=3,
               label=f"Other non-private courts ({len(other_courts)})")

    in_circle_all = sum(1 for r in bh if haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)
    in_circle_park = sum(1 for r in park_courts if haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)
    # BHPLTA ground-truth: of the 7-8 OSM-tagged "tennis" pitches at Kingsway
    # / Hove Beach Park, 2 have been converted to padel. The pink dots show
    # what OSM tags as tennis; the title uses the BHPLTA-correct headline
    # (subtract 2 for the padel conversions, but not below 6 — the BHPLTA
    # operating count for Kingsway tennis).
    in_circle_kingsway = sum(1 for r in park_courts
                              if is_kingsway(r) and
                              haversine_m(float(r["lat"]), float(r["lon"]), sec_lat, sec_lon) <= sec_r)
    in_circle_park_bhplta = in_circle_park - max(0, in_circle_kingsway - 6)

    ax.set_xlim(minlon, maxlon)
    ax.set_ylim(minlat, maxlat)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    land_str = ""
    if land_info:
        land_str = (f" — {land_info['land_area_km2']:.1f} km² land "
                    f"({land_info['pct_sea']:.0f}% of the disc is sea)")
    ax.set_title(
        f"Central Brighton & Hove — {in_circle_park_bhplta} park courts in a "
        f"{sec_r/1000:.2f} km radius circle{land_str}\n"
        f"(includes Hove Beach Park courts at Kingsway — BHCC parks-and-green-spaces, OSM gap)",
        fontsize=11, color="#222", loc="left", pad=10, fontweight="bold")
    ax.legend(loc="lower left", fontsize=10, frameon=True, facecolor="white",
              edgecolor="#cccccc")
    fig.text(0.99, 0.01, "© OpenStreetMap • Carto basemap • jim.tennis",
             ha="right", color="#666", fontsize=8)
    fig.tight_layout()
    out = REPORTS / "brighton_central_circle.png"
    fig.savefig(out, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    print(f"  in-circle: {in_circle_all} all, {in_circle_park} park")
    return 0


if __name__ == "__main__":
    sys.exit(main())
