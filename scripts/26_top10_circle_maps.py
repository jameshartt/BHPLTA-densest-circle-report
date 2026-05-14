"""Top-10 densest-park-tennis circles as a small-multiples comparison map.

For each of the top 10 cities by public-park-courts per km² of LAND, render
a panel showing the city's densest 2.34 km circle on a Carto basemap, with
the public-park courts plotted as dots. Brighton's panel uses the
USER-defined Central B&H circle (not the city's densest-anywhere).

Output: reports/top10_circle_maps.png
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import requests
from PIL import Image
from shapely.geometry import Polygon, Point

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
IMAGERY = ROOT / "data" / "imagery"

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
BRIGHTON_PINK = "#e3174a"
BRIGHTON_DEEP = "#9d0f33"

# Brighton's USER circle parameters (with Hove Beach Park ground-truth correction).
# Anchors: Queens (south-east court, way 127064771) / Kingsway / Blakers / Pavilion & Avenue.
BH_CIRCLE = {
    "city": "Brighton and Hove",
    "country": "UK",
    "lat": 50.82567,
    "lon": -0.15648,
    "radius_m": 2336.78,
    "park_courts": 43,  # 37 OSM-strict + 6 Hove Beach Park (BHCC-confirmed)
    "land_km2": 10.9,
    "density": 3.94,
    "annotation": "user-defined circle\nQueens / Pavilion & Avenue / Kingsway / Blakers",
}


# Per-city ground-truth corrections sourced from `reports/ground_truth/*.md`.
# `add_ways`: OSM way IDs to include even though the strict pipeline excluded them
#   (typically `leisure=sports_centre` polygons wrapping municipal venues that are
#    publicly bookable on the day — the same false-exclusion pattern that affected
#    Brighton's Kingsway / Hove Beach Park).
# `gt_count`: BHPLTA-equivalent ground-truth court count for this city.
# `gt_density`: STEP 6 admin-clip ground-truth density (Paris 4.48 etc.).
# `fair_land`: STEP 7 fair-denominator land = disc − water (no admin-clip).
# `fair_density`: gt_count / fair_land — Step 7's "fair-denominator" density.
#   This is the metric on which Brighton lands at #1 once Tokyo is asterisked
#   on bbox-scope grounds.
GROUND_TRUTH = {
    "paris": {
        "gt_count": 43,
        "gt_density": 4.48,
        "fair_land": 16.78,
        "fair_density": 2.56,
        "add_ways": [
            # Centre sportif Léo Lagrange (Bois de Vincennes) — 15 ways in OSM cache,
            # all sport=tennis, polygon tagged leisure=sports_centre but publicly
            # bookable via tennis.paris.fr.
            99993696, 99993697, 99993699, 99993703, 99993710, 99993711,
            211358364, 211358365, 211358366, 211358367, 211358368, 211358369,
            211358371, 211358373, 211358374,
        ],
        "remove_ways": [],
        "note": "+16 Léo Lagrange municipal courts (publicly bookable, mis-filtered as 'club')",
    },
    "boston":         {"gt_count": 18, "gt_density": 3.59, "fair_land": 16.68, "fair_density": 1.08, "add_ways": [], "remove_ways": [], "note": "no corrections — Daly Field DCR verified public"},
    "new_york_city": {
        "gt_count": 31, "gt_density": 2.28, "fair_land": 13.61, "fair_density": 2.28,
        "add_ways": [],
        "remove_ways": [
            # Randalls Island Park Tennis Center — operated by Sportime as the
            # John McEnroe Tennis Academy / Cary Leeds Center. The complex sits
            # on NYC Parks land but is a private/commercial academy — not
            # bookable on the day by a member of the public as a park-tennis
            # court (you book Sportime, who charge commercial academy rates).
            1117878122, 1117878123, 1117878124, 1117878125, 1117878126,
            1117878128, 1117878129, 1117878130, 1117878131, 1117878132,
            1117878133, 1117878134, 1117878135, 1117878136, 1117878137,
        ],
        "note": "−15 Randalls Island (McEnroe Academy / Sportime, commercial academy on parks land). NYC water (Harlem River + East River + Hell Gate + Bronx Kill) had to be synthesised by buffering OSM waterway centerlines — OSM uses natural=coastline (lines) for NYC tidal waters, not natural=water polygons. Synthesised water ≈ 3.55 km².",
    },
    "chicago":        {"gt_count": 43, "gt_density": 3.28, "fair_land": 13.12, "fair_density": 3.28, "add_ways": [], "remove_ways": [], "note": "+8 Washington Park Refectory cluster trimmed by polygon edge; Lake Michigan polygon (relation 1205149) added to water-subtraction — 3.64 km² of disc is lake"},
    "auckland":       {"gt_count": 40, "gt_density": 2.33, "fair_land": 17.15, "fair_density": 2.33, "add_ways": [], "remove_ways": [], "note": "no corrections"},
    "los_angeles":    {"gt_count":  8, "gt_density": 0.47, "fair_land": 17.15, "fair_density": 0.47, "add_ways": [], "remove_ways": [], "note": "−27 SMMNRA federal protected-area overlay catches private CCs and luxury home courts"},
    "toronto":        {"gt_count": 19, "gt_density": 1.11, "fair_land": 17.10, "fair_density": 1.11, "add_ways": [], "remove_ways": [], "note": "−13 community tennis clubs on park land that require club membership"},
    "sydney":         {"gt_count": 27, "gt_density": 1.60, "fair_land": 16.88, "fair_density": 1.60, "add_ways": [], "remove_ways": [], "note": "no corrections — all council-tagged"},
    "melbourne":      {"gt_count": 50, "gt_density": 3.07, "fair_land": 16.31, "fair_density": 3.07, "add_ways": [], "remove_ways": [], "note": "+24 Melbourne Park NTC Pay-&-Play outdoor courts (sports_centre)"},
    "rome":           {"gt_count":  2, "gt_density": 0.12, "fair_land": 17.14, "fair_density": 0.12, "add_ways": [], "remove_ways": [], "note": "−24 private FIT circoli leasing land inside the Valle dei Casali nature reserve"},
    "buenos_aires":   {"gt_count":  6, "gt_density": 0.54, "fair_land": 17.15, "fair_density": 0.35, "add_ways": [], "remove_ways": [], "note": "−7 Club Comunicaciones members-only concession at Parque Sarmiento"},
    "san_francisco":  {"gt_count": 27, "gt_density": 1.58, "fair_land": 17.09, "fair_density": 1.58, "add_ways": [], "remove_ways": [], "note": "−2 St Francis Wood HOA, +9 SFRPD inside park-and-sports_centre overlap"},
    "tokyo_23_wards": {"gt_count": 70, "gt_density": 4.08, "fair_land": 17.14, "fair_density": 4.08, "add_ways": [], "remove_ways": [], "note": "+52 OSM park-polygon gaps (Tokyo-side ~25-30 only; bbox scope includes Saitama)", "step7_exclude": True},
    "brussels":       {"gt_count": 27, "gt_density": 1.76, "fair_land": 16.79, "fair_density": 1.61, "add_ways": [], "remove_ways": [], "note": "+11 ADEPS Forêt de Soignes, +3 Trois Tilleuls — both municipal sports_centres"},
    "greater_london": {"gt_count": 44, "gt_density": 2.89, "fair_land": 15.24, "fair_density": 2.89, "add_ways": [], "remove_ways": [], "note": "no corrections — all 8 venues are Will To Win / Lambeth Parks Tennis / Southwark public"},
}


def slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")


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


def fetch_basemap(center_lat, center_lon, radius_m, zoom=13):
    """Fetch a stitched basemap covering circle + ~25% padding."""
    pad = 1.25
    pad_lat = (radius_m * pad) / 111_320.0
    pad_lon = pad_lat / max(math.cos(math.radians(center_lat)), 0.1)
    minlat = center_lat - pad_lat
    maxlat = center_lat + pad_lat
    minlon = center_lon - pad_lon
    maxlon = center_lon + pad_lon

    x_min, y_max = deg2num_float(minlat, minlon, zoom)
    x_max, y_min = deg2num_float(maxlat, maxlon, zoom)
    x_lo, x_hi = int(math.floor(x_min)), int(math.ceil(x_max))
    y_lo, y_hi = int(math.floor(y_min)), int(math.ceil(y_max))
    cols = x_hi - x_lo; rows_ = y_hi - y_lo
    canvas = Image.new("RGB", (cols * 256, rows_ * 256), color=(245, 246, 248))
    for dx in range(cols):
        for dy in range(rows_):
            t = fetch_tile(x_lo + dx, y_lo + dy, zoom)
            if t is not None:
                canvas.paste(t, (dx * 256, dy * 256))
    canvas_minlat, canvas_minlon = num2deg(x_lo, y_hi, zoom)
    canvas_maxlat, canvas_maxlon = num2deg(x_hi, y_lo, zoom)
    return canvas, (minlon, maxlon, minlat, maxlat), (canvas_minlon, canvas_maxlon, canvas_minlat, canvas_maxlat)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_brighton_courts():
    """Brighton park_public courts in user circle, including Hove Beach Park
    (Kingsway) ground-truth correction."""
    rows = list(csv.DictReader(open(PROCESSED / "uk_tennis_facilities_parks_v2.csv")))
    bh = [r for r in rows if r["city_name"] == "Brighton and Hove" and r["kind"] == "court"
          and r["access"] != "private"]
    def is_kingsway(r):
        lat, lon = float(r["lat"]), float(r["lon"])
        return 50.825 < lat < 50.828 and -0.192 < lon < -0.187
    in_circle = []
    for r in bh:
        is_park = (r["park_public"] == "1") or is_kingsway(r)
        if not is_park:
            continue
        lat, lon = float(r["lat"]), float(r["lon"])
        if haversine_m(lat, lon, BH_CIRCLE["lat"], BH_CIRCLE["lon"]) <= BH_CIRCLE["radius_m"]:
            in_circle.append((lat, lon))
    return in_circle


def get_uk_courts(rank: int, center_lat, center_lon, radius_m):
    """Park-public courts for a UK city: in_park AND not in_club, within circle.
    UK pipeline stores files as {rank:03d}_*.json (courts) and
    parks_{rank:03d}_*.json / clubs_{rank:03d}_*.json.
    Returns (strict, gt_added) — same shape as get_global_courts."""
    uk_dir = RAW / "overpass" / "uk"
    courts_cands = list(uk_dir.glob(f"{rank:03d}_*.json"))
    parks_cands = list(uk_dir.glob(f"parks_{rank:03d}_*.json"))
    clubs_cands = list(uk_dir.glob(f"clubs_{rank:03d}_*.json"))
    if not courts_cands:
        return [], []
    return _filter_courts(
        json.loads(courts_cands[0].read_text()),
        json.loads(parks_cands[0].read_text()) if parks_cands else {"elements": []},
        json.loads(clubs_cands[0].read_text()) if clubs_cands else {"elements": []},
        center_lat, center_lon, radius_m,
    )


def _build_polys(data):
    polys = []
    for el in data.get("elements", []):
        if el["type"] == "way" and "geometry" in el:
            coords = [(n["lon"], n["lat"]) for n in el["geometry"]]
            if len(coords) >= 4:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                try:
                    p = Polygon(coords)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.is_valid and p.area > 0:
                        polys.append(p)
                except Exception:
                    pass
        elif el["type"] == "relation" and "members" in el:
            outers = []
            for m in el["members"]:
                if m.get("role") == "outer" and "geometry" in m:
                    coords = [(n["lon"], n["lat"]) for n in m["geometry"]]
                    if len(coords) >= 4:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        outers.append(coords)
            for outer in outers:
                try:
                    p = Polygon(outer)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.is_valid and p.area > 0:
                        polys.append(p)
                except Exception:
                    pass
    return polys


def _filter_courts(courts_data, parks_data, clubs_data,
                   center_lat, center_lon, radius_m,
                   add_ways=None, remove_ways=None):
    park_polys = _build_polys(parks_data)
    club_polys = _build_polys(clubs_data)
    add_set = set(add_ways or [])
    remove_set = set(remove_ways or [])
    out = []
    overrides = []  # ground-truth added courts (drawn distinct from strict)
    for el in courts_data.get("elements", []):
        t = el.get("tags", {})
        if t.get("leisure") != "pitch":
            continue
        if t.get("access") == "private":
            continue
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        if haversine_m(lat, lon, center_lat, center_lon) > radius_m:
            continue
        wid = el.get("id")
        if wid in remove_set:
            continue
        if wid in add_set:
            overrides.append((lat, lon))
            continue
        pt = Point(lon, lat)
        if not any(p.contains(pt) for p in park_polys):
            continue
        if any(p.contains(pt) for p in club_polys):
            continue
        out.append((lat, lon))
    return out, overrides


def get_global_courts(city_slug: str, center_lat, center_lon, radius_m):
    """Park-public courts for a global city: in_park AND not in_club, within circle.
    Returns (strict_courts, ground_truth_added_courts) — second list comes from
    GROUND_TRUTH[slug]['add_ways'] (currently populated for Paris only)."""
    glob_dir = RAW / "overpass" / "global"
    courts_path = glob_dir / f"courts_{city_slug}.json"
    parks_path = glob_dir / f"parks_{city_slug}.json"
    clubs_path = glob_dir / f"clubs_{city_slug}.json"
    if not courts_path.exists():
        return [], []
    gt = GROUND_TRUTH.get(city_slug, {})
    return _filter_courts(
        json.loads(courts_path.read_text()),
        json.loads(parks_path.read_text()) if parks_path.exists() else {"elements": []},
        json.loads(clubs_path.read_text()) if clubs_path.exists() else {"elements": []},
        center_lat, center_lon, radius_m,
        add_ways=gt.get("add_ways", []),
        remove_ways=gt.get("remove_ways", []),
    )


def render_panel(ax, label_main: str, label_sub: str, density_text: str,
                 center_lat: float, center_lon: float, radius_m: float,
                 court_coords: list, gt_added: list | None = None,
                 is_brighton: bool = False) -> None:
    canvas, extent, c_extent = fetch_basemap(center_lat, center_lon, radius_m, zoom=13)
    minlon, maxlon, minlat, maxlat = extent
    cminlon, cmaxlon, cminlat, cmaxlat = c_extent
    ax.imshow(canvas, extent=(cminlon, cmaxlon, cminlat, cmaxlat),
              aspect="auto", interpolation="bilinear")
    # circle outline
    r_lat = radius_m / 111_320.0
    r_lon = radius_m / (111_320.0 * math.cos(math.radians(center_lat)))
    angles = [math.radians(a) for a in range(0, 361, 2)]
    xs = [center_lon + r_lon * math.cos(a) for a in angles]
    ys = [center_lat + r_lat * math.sin(a) for a in angles]
    color = BRIGHTON_PINK if is_brighton else "#444"
    ax.plot(xs, ys, color=color, linewidth=1.8, alpha=0.9, zorder=4)
    ax.fill(xs, ys, color=color, alpha=0.08, zorder=3)

    # courts — strict (blue / pink-for-Brighton)
    if court_coords:
        ax.scatter([c[1] for c in court_coords], [c[0] for c in court_coords],
                   s=40, color=BRIGHTON_PINK if is_brighton else "#1b4f72",
                   edgecolor="white", linewidth=0.8, alpha=0.92, zorder=5,
                   label="OSM-strict courts" if (gt_added and not is_brighton) else None)
    # Ground-truth additions (different colour, slightly larger ring) so the eye
    # can pick out which courts the audit recovered.
    if gt_added:
        ax.scatter([c[1] for c in gt_added], [c[0] for c in gt_added],
                   s=70, marker="o", facecolor="#f5a623",
                   edgecolor="#7a4a00", linewidth=1.2, alpha=0.95, zorder=6,
                   label="Ground-truth added")

    ax.set_xlim(minlon, maxlon)
    ax.set_ylim(minlat, maxlat)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#cccccc" if not is_brighton else BRIGHTON_PINK)
        s.set_linewidth(2.5 if is_brighton else 1)
    # Title block
    ax.set_title(f"{label_main}\n{label_sub}", fontsize=14,
                 color=BRIGHTON_DEEP if is_brighton else "#1f2933",
                 loc="left", pad=8,
                 fontweight="bold" if is_brighton else "normal")
    # Density bottom-right
    ax.text(0.97, 0.04, density_text, transform=ax.transAxes,
            ha="right", va="bottom", fontsize=15, fontweight="bold",
            color=BRIGHTON_DEEP if is_brighton else "#1f2933",
            bbox=dict(facecolor="white", alpha=0.92, edgecolor="#cccccc", boxstyle="round,pad=0.4"))


def render(mode: str) -> None:
    """mode = 'step6' or 'step7'.
    step6 = admin-clip ground-truth densities (Paris/Tokyo above Brighton).
    step7 = fair-denominator densities (Brighton at #1; Tokyo excluded on
    bbox-scope grounds per the writeup)."""
    assert mode in ("step6", "step7")
    # Load global rankings
    glob = list(csv.DictReader(open(PROCESSED / "global_density_final.csv")))
    glob = [r for r in glob if r["densest_public_park"] and int(r["densest_public_park"]) > 0]
    glob.sort(key=lambda r: -float(r["density_public_park_per_km2_land"]))

    # Build panel list: every audited global city + Brighton + Greater London.
    # Each panel carries either Step-6 admin-clip density (mode='step6') or
    # Step-7 fair-denominator density (mode='step7'). In step7 mode, Tokyo
    # is excluded entirely (bbox-scope, can't be compared like-for-like).
    panels = []
    for r in glob:
        s = slug(r["city"])
        gt = GROUND_TRUTH.get(s)
        if gt and mode == "step7" and gt.get("step7_exclude"):
            continue  # Tokyo: dismissed on scope grounds
        if gt:
            count = gt["gt_count"]
            note = gt["note"]
            if mode == "step6":
                density = gt["gt_density"]
                land_for_label = float(r["land_km2"])
            else:
                density = gt["fair_density"]
                land_for_label = gt["fair_land"]
        else:
            count = int(r["densest_public_park"])
            density = float(r["density_public_park_per_km2_land"])
            note = ""
            land_for_label = float(r["land_km2"])
        panels.append({
            "label_main": f"{r['city']} ({r['country']})",
            "label_sub": f"{count} courts • land {land_for_label:.1f} km²",
            "density": density,
            "lat": float(r["densest_public_park_lat"] or 0) if "densest_public_park_lat" in r else None,
            "lon": float(r["densest_public_park_lon"] or 0) if "densest_public_park_lon" in r else None,
            "slug": s,
            "uk_rank": None,
            "note": note,
            "is_brighton": False,
        })

    # Splice in Greater London from uk_density_final.csv
    uk = list(csv.DictReader(open(PROCESSED / "uk_density_final.csv")))
    ldn_rows = [r for r in uk if r["city"] == "Greater London"]
    if ldn_rows:
        r = ldn_rows[0]
        gt = GROUND_TRUTH.get("greater_london")
        count = gt["gt_count"] if gt else int(r["densest_public_park"])
        if mode == "step7" and gt:
            density = gt["fair_density"]
            land_for_label = gt["fair_land"]
        elif gt:
            density = gt["gt_density"]
            land_for_label = float(r["land_km2"])
        else:
            density = float(r["density_public_park_per_km2_land"])
            land_for_label = float(r["land_km2"])
        panels.append({
            "label_main": "Greater London (UK) — Battersea / Kennington",
            "label_sub": f"{count} courts • land {land_for_label:.1f} km²",
            "density": density,
            "lat": float(r["densest_public_park_lat"]) if r.get("densest_public_park_lat") else None,
            "lon": float(r["densest_public_park_lon"]) if r.get("densest_public_park_lon") else None,
            "slug": None,
            "uk_rank": 1,
            "note": gt["note"] if gt else "",
            "is_brighton": False,
        })

    # Brighton's USER circle as a featured panel (with Hove Beach Park correction).
    # Brighton's fair-denominator density equals its admin-clip density because
    # Brighton's only clip is sea (rightful water exclusion), so step6 = step7.
    panels.append({
        "label_main": "Brighton & Hove (UK)",
        "label_sub": f"{BH_CIRCLE['park_courts']} courts • land {BH_CIRCLE['land_km2']:.1f} km² • 36% sea",
        "density": BH_CIRCLE["density"],
        "lat": BH_CIRCLE["lat"], "lon": BH_CIRCLE["lon"],
        "slug": None,
        "uk_rank": None,
        "note": "+6 Hove Beach Park (BHCC park, OSM-untagged)",
        "is_brighton": True,
    })

    # Sort panels by ground-truth density descending and keep top 10
    panels.sort(key=lambda p: -p["density"])
    panels = panels[:10]

    # Fallback centres (Step 3 sub-circle locations from 16_global_densest.py)
    # used only if a panel doesn't have a Step-4 lat/lon. global_density_final.csv
    # now carries densest_public_park_lat/lon, so this is rarely needed.
    fallback_centres = {}
    for r in csv.DictReader(open(PROCESSED / "global_densest_circle.csv")):
        c = r["city"]
        if r.get("densest_park_lat"):
            fallback_centres[c] = (float(r["densest_park_lat"]), float(r["densest_park_lon"]))

    # Render
    n = len(panels)
    cols = 5; rows = math.ceil(n / cols)
    fig = plt.figure(figsize=(cols * 5.4, rows * 6.4 + 1.0), facecolor="white")
    gs = GridSpec(rows, cols, figure=fig, hspace=0.28, wspace=0.06,
                  left=0.015, right=0.985, top=0.90, bottom=0.04)

    for i, p in enumerate(panels):
        ax = fig.add_subplot(gs[i // cols, i % cols])
        gt_added = []
        if p["is_brighton"]:
            lat, lon = BH_CIRCLE["lat"], BH_CIRCLE["lon"]
            courts = get_brighton_courts()
        elif p.get("uk_rank"):
            lat = p["lat"]; lon = p["lon"]
            courts, gt_added = get_uk_courts(p["uk_rank"], lat, lon, BH_CIRCLE["radius_m"])
        else:
            if p["lat"] and p["lon"]:
                lat, lon = p["lat"], p["lon"]
            else:
                fb = fallback_centres.get(p["label_main"].split(" (")[0])
                lat, lon = fb if fb else (p["lat"], p["lon"])
            courts, gt_added = get_global_courts(p["slug"], lat, lon, BH_CIRCLE["radius_m"])

        density_text = f"{p['density']:.2f}/km²"
        rank = i + 1
        title_main = f"#{rank}  {p['label_main']}"
        render_panel(ax, title_main, p["label_sub"], density_text,
                     lat, lon, BH_CIRCLE["radius_m"], courts,
                     gt_added=gt_added,
                     is_brighton=p["is_brighton"])

    if mode == "step6":
        title = ("Top 10 densest park-tennis circles in the world\n"
                 "Ground-truth counts, admin-clip denominator (see Step 6)")
        outname = "top10_circle_maps.png"
    else:
        title = ("Top 10 densest park-tennis circles in the world\n"
                 "Ground-truth counts, fair denominator (see Step 7) — Brighton & Hove #1")
        outname = "top10_circle_maps_step7.png"
    fig.suptitle(title, fontsize=22, color="#1f2933", fontweight="bold", y=0.985)
    fig.text(0.02, 0.012,
             "Carto basemap • OSM tennis features + park/club polygons + per-city ground-truth audit • "
             "blue dots = OSM-strict public park courts • orange rings = audit-recovered municipal courts "
             "(sports_centre polygons hiding on-the-day public venues) • pink = Brighton",
             color="#7a8086", fontsize=10)

    out = REPORTS / outname
    fig.savefig(out, dpi=130, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> int:
    render("step6")
    render("step7")
    return 0


if __name__ == "__main__":
    sys.exit(main())
