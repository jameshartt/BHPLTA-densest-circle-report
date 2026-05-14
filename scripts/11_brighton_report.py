"""Brighton & Hove tennis-accessibility presentation (UK-wide).

Produces:
  reports/brighton_tennis.md          headline report for the BHPLTA / club
  reports/brighton_hero.png           jazzed hero — text + chart, share-ready
  reports/brighton_500m_vs_1km.png    side-by-side bands vs peers
  reports/brighton_per_capita.png     honest counter-narrative
  reports/brighton_map.png            Brighton facilities on a real basemap

Headline: "Brighton has the most walkable tennis of any major UK city
outside London." Defensible against full UK 75-city dataset.
"""

from __future__ import annotations

import csv
import io
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import pandas as pd
import seaborn as sns
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
IMAGERY = ROOT / "data" / "imagery"

BRIGHTON_PINK = "#e3174a"
BRIGHTON_DEEP = "#9d0f33"
LONDON_GREY = "#9aa1a3"
PEER_GREY = "#c1c8cc"
INK = "#1f2933"
SOFT = "#f0f1f3"

REPORTS.mkdir(parents=True, exist_ok=True)

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def chart_hero(pop_access: pd.DataFrame, out: Path) -> None:
    """Share-ready hero: bold headline panel above a ranked bar chart."""
    big = pop_access.dropna(subset=["pct_pop_within_500m"]).copy()
    big = big[big["population"] >= 400_000].sort_values("pct_pop_within_500m", ascending=True)

    # Two stacked figures: top = headline area, bottom = chart. Use figure-level
    # coordinates so font sizes are absolute.
    fig = plt.figure(figsize=(13, 14), facecolor="white")

    # === TOP BANNER ===
    banner = fig.add_axes((0, 0.86, 1, 0.10), zorder=1)
    banner.axis("off")
    banner.set_xlim(0, 1); banner.set_ylim(0, 1)
    banner.add_patch(mpatches.Rectangle((0, 0), 1, 1, color=BRIGHTON_PINK))
    banner.text(0.04, 0.62, "BRIGHTON & HOVE", color="white",
                fontsize=30, fontweight="bold", va="center")
    banner.text(0.04, 0.25, "Tennis on your doorstep — a UK ranking",
                color="white", fontsize=16, style="italic", va="center")

    # === HEADLINE BLOCK ===
    head = fig.add_axes((0, 0.66, 1, 0.20), zorder=1)
    head.axis("off")
    head.set_xlim(0, 1); head.set_ylim(0, 1)
    head.text(0.04, 0.70, "1 in 3", fontsize=88, fontweight="bold",
              color=BRIGHTON_PINK, va="center")
    head.text(0.36, 0.82, "Brightonians lives within a 500-metre walk",
              fontsize=18, color=INK, va="center")
    head.text(0.36, 0.65, "of a tennis court — the highest share of any",
              fontsize=18, color=INK, va="center")
    head.text(0.36, 0.48, "major UK city outside London.",
              fontsize=18, color=INK, va="center", fontweight="bold")

    # Supporting stats strip
    head.add_patch(mpatches.Rectangle((0.04, 0.05), 0.92, 0.27,
                                       facecolor="#fdf0f3", edgecolor="none"))
    cols = [
        ("70%", "within 1 km walk", 0.07),
        ("91%", "within 2 km walk", 0.39),
        ("720 m", "median walk to nearest court", 0.71),
    ]
    for big_text, sub, x in cols:
        head.text(x, 0.22, big_text, fontsize=34, fontweight="bold",
                  color=BRIGHTON_PINK, va="center")
        head.text(x, 0.10, sub, fontsize=12, color=INK, va="center")

    # === BAR CHART ===
    ax = fig.add_axes((0.16, 0.07, 0.80, 0.55), zorder=1)
    colors = []
    for n in big["name"]:
        if n == "Brighton and Hove":
            colors.append(BRIGHTON_PINK)
        elif n == "Greater London":
            colors.append(LONDON_GREY)
        else:
            colors.append(PEER_GREY)
    bars = ax.barh(big["name"], big["pct_pop_within_500m"], color=colors,
                   edgecolor="white", linewidth=1.4, height=0.72)
    for bar, n, v in zip(bars, big["name"], big["pct_pop_within_500m"]):
        weight = "bold" if n == "Brighton and Hove" else "normal"
        col = BRIGHTON_DEEP if n == "Brighton and Hove" else "#374049"
        ax.text(v + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=12, color=col, fontweight=weight)
    # London annotation
    for bar, n in zip(bars, big["name"]):
        if n == "Greater London":
            if bar.get_width() > 8:
                ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                        "the capital", ha="center", va="center",
                        fontsize=10, color="white", style="italic")
    ax.set_xlabel("% of city residents within a 500-metre walk of a tennis court",
                  fontsize=12, color=INK, labelpad=10)
    ax.set_title("How Brighton compares — every UK city of 400,000+ residents",
                 fontsize=14, color=INK, loc="left", pad=14, fontweight="bold")
    ax.set_xlim(0, max(big["pct_pop_within_500m"]) * 1.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=10)
    ax.tick_params(axis="y", colors=INK, labelsize=11)
    ax.set_facecolor("white")

    fig.text(0.04, 0.018,
             "Source: OpenStreetMap (tennis courts) • ONS LSOA + NRS DZ + NISRA DZ population centroids • "
             "jim.tennis • May 2026",
             color="#7a8086", fontsize=9)
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)


def chart_hero_vertical(pop_access: pd.DataFrame, out: Path) -> None:
    """9:16 phone-optimised hero — Instagram Story / WhatsApp Status / Reel cover.
    Output is 1080x1920 px."""
    big = pop_access.dropna(subset=["pct_pop_within_500m"]).copy()
    big = big[big["population"] >= 400_000].sort_values("pct_pop_within_500m", ascending=True)

    fig = plt.figure(figsize=(10.8, 19.2), facecolor="white")  # 1080 x 1920 @ 100dpi

    # === BANNER (top 11%) ===
    banner = fig.add_axes((0, 0.89, 1, 0.11), zorder=1)
    banner.axis("off"); banner.set_xlim(0, 1); banner.set_ylim(0, 1)
    banner.add_patch(mpatches.Rectangle((0, 0), 1, 1, color=BRIGHTON_PINK))
    banner.text(0.5, 0.65, "BRIGHTON & HOVE", color="white",
                fontsize=42, fontweight="bold", ha="center", va="center")
    banner.text(0.5, 0.30, "tennis on your doorstep — a UK ranking",
                color="white", fontsize=22, style="italic", ha="center", va="center")

    # === HERO BLOCK (32%) ===
    head = fig.add_axes((0, 0.57, 1, 0.32), zorder=1)
    head.axis("off"); head.set_xlim(0, 1); head.set_ylim(0, 1)

    head.text(0.5, 0.78, "1 in 3", fontsize=150, fontweight="bold",
              color=BRIGHTON_PINK, ha="center", va="center")
    head.text(0.5, 0.51, "Brightonians lives within a", ha="center", va="center",
              fontsize=26, color=INK)
    head.text(0.5, 0.44, "500-metre walk of a tennis court", ha="center", va="center",
              fontsize=26, color=INK, fontweight="bold")
    head.text(0.5, 0.32, "— the highest share of any major", ha="center", va="center",
              fontsize=22, color=INK)
    head.text(0.5, 0.26, "UK city outside London.", ha="center", va="center",
              fontsize=22, color=INK, fontweight="bold")

    # Supporting stats strip
    head.add_patch(mpatches.Rectangle((0.04, 0.02), 0.92, 0.18,
                                       facecolor="#fdf0f3", edgecolor="none"))
    cols = [
        ("70%", "within 1 km walk", 0.18),
        ("91%", "within 2 km walk", 0.50),
        ("720 m", "median walk", 0.82),
    ]
    for big_text, sub, x in cols:
        head.text(x, 0.13, big_text, fontsize=44, fontweight="bold",
                  color=BRIGHTON_PINK, ha="center", va="center")
        head.text(x, 0.05, sub, fontsize=16, color=INK, ha="center", va="center")

    # === CHART (54%) ===
    chart_title = fig.add_axes((0, 0.51, 1, 0.05), zorder=1)
    chart_title.axis("off")
    chart_title.text(0.5, 0.5, "How Brighton compares — UK cities of 400,000+",
                     ha="center", va="center", fontsize=22, fontweight="bold", color=INK)

    # Use top 10 cities (truncate to fit phone)
    top10 = big.tail(10).copy()  # already ascending; tail = highest

    ax = fig.add_axes((0.30, 0.06, 0.66, 0.44), zorder=1)
    colors = []
    for n in top10["name"]:
        if n == "Brighton and Hove":
            colors.append(BRIGHTON_PINK)
        elif n == "Greater London":
            colors.append(LONDON_GREY)
        else:
            colors.append(PEER_GREY)
    bars = ax.barh(top10["name"], top10["pct_pop_within_500m"], color=colors,
                   edgecolor="white", linewidth=2.5, height=0.78)
    for bar, n, v in zip(bars, top10["name"], top10["pct_pop_within_500m"]):
        weight = "bold" if n == "Brighton and Hove" else "normal"
        col = BRIGHTON_DEEP if n == "Brighton and Hove" else "#374049"
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=22, color=col, fontweight=weight)
    for bar, n in zip(bars, top10["name"]):
        if n == "Greater London":
            ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                    "the capital", ha="center", va="center",
                    fontsize=14, color="white", style="italic")
    ax.set_xlim(0, max(top10["pct_pop_within_500m"]) * 1.20)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=16)
    ax.tick_params(axis="y", colors=INK, labelsize=20)
    ax.set_xlabel("% of city residents within a 500 m walk of a court",
                  fontsize=16, color=INK, labelpad=8)
    ax.set_facecolor("white")

    fig.text(0.5, 0.012,
             "Source: OpenStreetMap • ONS / NRS / NISRA population centroids • jim.tennis",
             color="#7a8086", fontsize=14, ha="center")
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)


def chart_hero_square(pop_access: pd.DataFrame, out: Path) -> None:
    """1:1 square hero for Instagram feed posts. 1080x1080 px."""
    big = pop_access.dropna(subset=["pct_pop_within_500m"]).copy()
    big = big[big["population"] >= 400_000].sort_values("pct_pop_within_500m", ascending=True)

    fig = plt.figure(figsize=(10.8, 10.8), facecolor="white")

    # Banner top
    banner = fig.add_axes((0, 0.86, 1, 0.14), zorder=1)
    banner.axis("off"); banner.set_xlim(0, 1); banner.set_ylim(0, 1)
    banner.add_patch(mpatches.Rectangle((0, 0), 1, 1, color=BRIGHTON_PINK))
    banner.text(0.5, 0.62, "BRIGHTON & HOVE", color="white",
                fontsize=38, fontweight="bold", ha="center", va="center")
    banner.text(0.5, 0.28, "the most walkable major UK city for tennis (outside London)",
                color="white", fontsize=16, style="italic", ha="center", va="center")

    # Hero stat
    head = fig.add_axes((0, 0.54, 1, 0.32), zorder=1)
    head.axis("off"); head.set_xlim(0, 1); head.set_ylim(0, 1)
    head.text(0.5, 0.72, "1 in 3", fontsize=120, fontweight="bold",
              color=BRIGHTON_PINK, ha="center", va="center")
    head.text(0.5, 0.42, "Brightonians lives within a 500-metre walk",
              ha="center", va="center", fontsize=21, color=INK)
    head.text(0.5, 0.32, "of a tennis court", ha="center", va="center",
              fontsize=21, color=INK, fontweight="bold")
    # Supporting stats
    head.add_patch(mpatches.Rectangle((0.04, 0.02), 0.92, 0.20,
                                       facecolor="#fdf0f3", edgecolor="none"))
    cols = [("70%", "within 1 km", 0.18),
            ("91%", "within 2 km", 0.50),
            ("720 m", "median walk", 0.82)]
    for big_text, sub, x in cols:
        head.text(x, 0.14, big_text, fontsize=34, fontweight="bold",
                  color=BRIGHTON_PINK, ha="center", va="center")
        head.text(x, 0.05, sub, fontsize=13, color=INK, ha="center", va="center")

    # Chart — top 8
    top8 = big.tail(8).copy()
    ax = fig.add_axes((0.30, 0.10, 0.66, 0.40), zorder=1)
    colors = []
    for n in top8["name"]:
        if n == "Brighton and Hove":
            colors.append(BRIGHTON_PINK)
        elif n == "Greater London":
            colors.append(LONDON_GREY)
        else:
            colors.append(PEER_GREY)
    bars = ax.barh(top8["name"], top8["pct_pop_within_500m"], color=colors,
                   edgecolor="white", linewidth=2, height=0.78)
    for bar, n, v in zip(bars, top8["name"], top8["pct_pop_within_500m"]):
        weight = "bold" if n == "Brighton and Hove" else "normal"
        col = BRIGHTON_DEEP if n == "Brighton and Hove" else "#374049"
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=16, color=col, fontweight=weight)
    for bar, n in zip(bars, top8["name"]):
        if n == "Greater London":
            ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                    "the capital", ha="center", va="center",
                    fontsize=11, color="white", style="italic")
    ax.set_xlim(0, max(top8["pct_pop_within_500m"]) * 1.20)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=11)
    ax.tick_params(axis="y", colors=INK, labelsize=14)
    ax.set_xlabel("% of residents within a 500 m walk of a court",
                  fontsize=11, color=INK, labelpad=6)
    ax.set_facecolor("white")
    ax.set_title("UK cities of 400,000+ residents — top 8",
                 fontsize=14, color=INK, loc="left", pad=10, fontweight="bold")

    fig.text(0.5, 0.025,
             "Source: OpenStreetMap • ONS/NRS/NISRA centroids • jim.tennis",
             color="#7a8086", fontsize=10, ha="center")
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)


def chart_distance_breakdown(pop_access: pd.DataFrame, peers: list[str], out: Path) -> None:
    df = pop_access[pop_access["name"].isin(peers + ["Brighton and Hove"])].copy()
    df = df.dropna(subset=["pct_pop_within_500m"])
    df = df.sort_values("pct_pop_within_500m", ascending=False)
    x = list(df["name"])
    y500 = list(df["pct_pop_within_500m"])
    y1k = list(df["pct_pop_within_1km"])
    y2k = list(df["pct_pop_within_2km"])
    n = len(x)
    idx = list(range(n))
    width = 0.27
    fig, ax = plt.subplots(figsize=(12, 6))
    cols500 = [BRIGHTON_PINK if name == "Brighton and Hove" else "#5b8aa6" for name in x]
    cols1k = [BRIGHTON_PINK if name == "Brighton and Hove" else "#85a8c1" for name in x]
    cols2k = [BRIGHTON_PINK if name == "Brighton and Hove" else "#b3cad9" for name in x]
    b1 = ax.bar([i - width for i in idx], y500, width, label="within 500 m walk",
                color=cols500, edgecolor="white", linewidth=1.2)
    b2 = ax.bar(idx, y1k, width, label="within 1 km walk",
                color=cols1k, edgecolor="white", linewidth=1.2)
    b3 = ax.bar([i + width for i in idx], y2k, width, label="within 2 km walk",
                color=cols2k, edgecolor="white", linewidth=1.2)
    ax.set_xticks(idx)
    ax.set_xticklabels(x, rotation=20, ha="right")
    ax.set_ylabel("% of city residents", fontsize=11)
    ax.set_ylim(0, 105)
    ax.set_title(
        "Brighton & Hove vs peer UK cities: walking distance to a tennis court",
        fontsize=13, loc="left", pad=10)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    for bars, vals in ((b1, y500), (b2, y1k), (b3, y2k)):
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
                    f"{v:.0f}", ha="center", fontsize=8, color="#333")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)


def chart_per_capita(stats: pd.DataFrame, out: Path) -> None:
    big = stats[stats["population"] >= 400_000].copy()
    big = big.sort_values("courts_per_100k", ascending=True)
    colors = [BRIGHTON_PINK if n == "Brighton and Hove" else PEER_GREY for n in big["name"]]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(big["name"], big["courts_per_100k"], color=colors,
                   edgecolor="white", linewidth=1.2)
    for bar, n, v in zip(bars, big["name"], big["courts_per_100k"]):
        weight = "bold" if n == "Brighton and Hove" else "normal"
        ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}", va="center", fontsize=10,
                color=BRIGHTON_DEEP if n == "Brighton and Hove" else "#444",
                fontweight=weight)
    ax.set_xlabel("Non-private tennis courts per 100,000 residents", fontsize=11)
    ax.set_title("Per-capita courts — UK cities ≥ 400k\n"
                 "Brighton's accessibility lead is NOT explained by raw count",
                 fontsize=12, loc="left", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Brighton map with real OSM tile basemap
# ---------------------------------------------------------------------------

def deg2num_float(lat_deg: float, lon_deg: float, zoom: int) -> tuple[float, float]:
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat_deg))) / math.pi) / 2.0 * n
    return x, y


def num2deg(xtile: float, ytile: float, zoom: int) -> tuple[float, float]:
    n = 2.0 ** zoom
    lon = xtile / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ytile / n))))
    return lat, lon


def fetch_tile(x: int, y: int, z: int) -> Image.Image | None:
    cache = IMAGERY / "carto" / f"z{z}_x{x}_y{y}.png"
    if cache.exists():
        try:
            return Image.open(cache).convert("RGB")
        except Exception:
            cache.unlink(missing_ok=True)
    # Use Carto Positron (light tiles) — public, attribution required
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


def chart_brighton_map(clubs_df: pd.DataFrame, facilities_df: pd.DataFrame, out: Path) -> None:
    bh = clubs_df[(clubs_df["city_name"] == "Brighton and Hove") &
                  (clubs_df["primary_access"] != "private")].copy()
    bh_courts = facilities_df[(facilities_df["city_name"] == "Brighton and Hove") &
                              (facilities_df["kind"] == "court") &
                              (facilities_df["access"] != "private")].copy()
    if bh.empty:
        print("warn: no Brighton clubs found")
        return
    pad = 0.012
    minlat = bh["lat"].min() - pad
    maxlat = bh["lat"].max() + pad
    minlon = bh["lon"].min() - pad * 1.6
    maxlon = bh["lon"].max() + pad * 1.6

    zoom = 13
    x_min, y_max = deg2num_float(minlat, minlon, zoom)
    x_max, y_min = deg2num_float(maxlat, maxlon, zoom)
    x_lo, x_hi = int(math.floor(x_min)), int(math.ceil(x_max))
    y_lo, y_hi = int(math.floor(y_min)), int(math.ceil(y_max))
    cols = x_hi - x_lo
    rows = y_hi - y_lo
    if cols == 0 or rows == 0:
        return

    canvas = Image.new("RGB", (cols * 256, rows * 256), color=(245, 246, 248))
    for dx in range(cols):
        for dy in range(rows):
            tile = fetch_tile(x_lo + dx, y_lo + dy, zoom)
            if tile is not None:
                canvas.paste(tile, (dx * 256, dy * 256))

    # Compute extent in lat/lon for the canvas
    canvas_minlat, canvas_minlon = num2deg(x_lo, y_hi, zoom)
    canvas_maxlat, canvas_maxlon = num2deg(x_hi, y_lo, zoom)

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.imshow(canvas, extent=(canvas_minlon, canvas_maxlon, canvas_minlat, canvas_maxlat),
              aspect="auto", interpolation="bilinear", zorder=0)
    # Cluster bubbles
    sizes = (bh["court_count"].astype(float) ** 1.25) * 22 + 35
    ax.scatter(bh["lon"], bh["lat"], s=sizes, color=BRIGHTON_PINK,
               edgecolor="white", linewidth=1.5, alpha=0.92, zorder=2)
    # Court counts on largest 5
    top5 = bh.sort_values("court_count", ascending=False).head(5)
    for _, r in top5.iterrows():
        ax.text(r["lon"], r["lat"], str(int(r["court_count"])),
                ha="center", va="center", color="white",
                fontsize=10, fontweight="bold", zorder=3)
    ax.set_xlim(minlon, maxlon)
    ax.set_ylim(minlat, maxlat)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        f"{len(bh)} non-private tennis facilities across Brighton & Hove "
        f"({int(bh['court_count'].sum())} courts) — bubbles sized by court count",
        fontsize=12, loc="left", color=INK, pad=10)
    fig.text(0.99, 0.005, "© OpenStreetMap contributors • Carto basemap",
             ha="right", color="#7a8086", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def main() -> int:
    pop_access = pd.read_csv(PROCESSED / "uk_pop_access.csv")
    stats = pd.read_csv(PROCESSED / "uk_stats.csv")
    clubs = pd.read_csv(PROCESSED / "uk_clubs.csv")
    facilities = pd.read_csv(PROCESSED / "uk_tennis_facilities.csv")

    chart_hero(pop_access, REPORTS / "brighton_hero.png")
    chart_hero_vertical(pop_access, REPORTS / "brighton_hero_9x16.png")
    chart_hero_square(pop_access, REPORTS / "brighton_hero_1x1.png")
    chart_distance_breakdown(
        pop_access,
        ["Greater London", "Edinburgh", "Bournemouth/Poole", "Bristol",
         "Sheffield", "Cardiff", "Liverpool"],
        REPORTS / "brighton_500m_vs_1km.png",
    )
    chart_per_capita(stats, REPORTS / "brighton_per_capita.png")
    chart_brighton_map(clubs, facilities, REPORTS / "brighton_map.png")

    bh_pa = pop_access[pop_access["name"] == "Brighton and Hove"].iloc[0]
    bh_stats = stats[stats["name"] == "Brighton and Hove"].iloc[0]

    pop_access_ranked = pop_access.dropna(subset=["pct_pop_within_500m"])
    big = pop_access_ranked[pop_access_ranked["population"] >= 400_000].copy()
    big = big.sort_values("pct_pop_within_500m", ascending=False).reset_index(drop=True)

    md = []
    md.append("# Brighton & Hove: the most walkable major UK city for tennis (outside London)\n")
    md.append("*Prepared for the Brighton & Hove Parks Lawn Tennis Association — May 2026*\n")
    md.append("\n---\n")

    md.append("## The headline\n")
    md.append(
        f"**Roughly one in three Brightonians lives within a 500-metre walk of a "
        f"tennis court — {bh_pa['pct_pop_within_500m']:.1f}% of residents — "
        f"the highest share of any major UK city outside Greater London.**\n\n"
        f"Among UK cities of 400,000 residents or more, only the capital is more "
        f"walkable than Brighton — and even then by just a couple of percentage "
        f"points. Edinburgh, our nearest major-city peer (482k residents), reaches "
        f"24.1%; Bournemouth/Poole, our nearest peer in shape, sits at 23.0%.\n"
    )
    md.append(
        f"\nNine in ten residents — {bh_pa['pct_pop_within_2km']:.1f}% — live within "
        f"a 2 km walk (about 25 minutes on foot). The typical Brighton resident "
        f"is just {int(bh_pa['median_distance_m'])} metres from their nearest court — "
        f"under 10 minutes' walk for most of us.\n"
    )

    md.append("\n![Hero](./brighton_hero.png)\n\n")

    md.append("## How we measured it\n")
    md.append(
        "For every UK city we used the **population-weighted centroids** of every "
        "small statistical area (LSOA in England & Wales, Data Zone in Scotland and "
        "Northern Ireland — averaging ~1,500 residents each, the smallest unit each "
        "country's statistics office publishes). For each centroid we measured the "
        "distance to its nearest **non-private** tennis court (OpenStreetMap data: "
        "`leisure=pitch + sport=tennis` and `leisure=sports_centre + sport=tennis`, "
        "excluding `access=private`). The resulting % is the share of **residents**, "
        "not area, within walking distance — so a few isolated park courts in "
        "low-density suburbs don't inflate the score.\n"
    )

    md.append("\n## Brighton vs the major UK cities\n\n")
    md.append("All UK cities with built-up-area population of 400,000 or more, ranked:\n\n")
    md.append("| # | City | BUA pop. | Residents in polygon | Within 500 m | Within 1 km | Within 2 km | Median walk |\n")
    md.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
    for i, r in enumerate(big.itertuples(index=False), 1):
        bold = "**" if r.name == "Brighton and Hove" else ""
        in_poly = int(r.pop_in_bbox) if pd.notna(r.pop_in_bbox) else 0
        md.append(
            f"| {bold}{i}{bold} | {bold}{r.name}{bold} "
            f"| {bold}{int(r.population):,}{bold} "
            f"| {bold}{in_poly:,}{bold} "
            f"| {bold}{r.pct_pop_within_500m:.1f}%{bold} "
            f"| {bold}{r.pct_pop_within_1km:.1f}%{bold} "
            f"| {bold}{r.pct_pop_within_2km:.1f}%{bold} "
            f"| {bold}{int(r.median_distance_m)} m{bold} |\n"
        )

    md.append(
        "\nLondon edges Brighton on the headline metric (35.1% vs 32.9%) — the "
        "capital has both the densest population and the most mapped tennis "
        "infrastructure of anywhere in the UK. **Outside London, no city comes "
        "close.** Edinburgh trails by 8.8 percentage points; Liverpool, Cardiff "
        "and Sheffield manage roughly half of Brighton's score.\n"
    )

    md.append("\n## A side-by-side with peer cities\n\n")
    md.append("![Walking-distance access by city](./brighton_500m_vs_1km.png)\n\n")

    bh_clubs_count = int(bh_stats["clubs"])
    bh_courts_count = int(bh_stats["courts"])
    bh_priv = int(bh_stats["private_courts"])
    md.append("## What's actually here\n")
    md.append(
        f"OpenStreetMap currently has **{bh_courts_count} non-private courts** "
        f"across **{bh_clubs_count} distinct facilities** within Brighton & Hove "
        f"(plus {bh_priv} private courts excluded from these figures). A typical "
        f"facility carries about four courts — Brighton's pattern is "
        f"well-resourced multi-court parks rather than scattered single courts.\n"
    )
    md.append("\n![Brighton & Hove tennis map](./brighton_map.png)\n\n")

    md.append("## Why Brighton wins (outside the capital)\n")
    md.append(
        "Three things compound:\n\n"
        "1. **Compact urban form.** The city's populated area is tightly bounded "
        "by the sea to the south and the South Downs to the north — so there is "
        "very little low-density sprawl for residents to be stranded in.\n"
        "2. **Multi-court parks distributed across that compact form.** "
        "Pavilion & Avenue, Withdean, Saltdean, Hove Recreation Ground, "
        "Queen's Park, Preston Park and St Ann's Well together place a "
        "non-trivial cluster within most residents' postcodes.\n"
        f"3. **A public-tennis culture, not a private one.** Of {bh_courts_count + bh_priv} "
        f"total tennis surfaces in the city, only {bh_priv} are tagged "
        "`access=private`. The rest are park courts, council-managed sites, or "
        "pay-and-play clubs — the BHPLTA model in action.\n"
    )

    md.append("\n## Per-capita context (the honest sub-headline)\n")
    md.append(
        f"On absolute courts-per-100,000-residents, Brighton sits mid-table at "
        f"{bh_stats['courts_per_100k']:.1f} — behind university towns like Oxford "
        "and Cambridge that pack large numbers of college courts into small "
        "populations, and behind Leicester / Edinburgh among major cities. "
        "**Accessibility, not raw count, is where Brighton excels** — and in a "
        "city this size, accessibility is what determines whether the average "
        "resident can actually play.\n"
    )
    md.append("\n![Courts per 100k, 400k+ cities](./brighton_per_capita.png)\n\n")

    md.append("## Caveats (so we can defend the claim)\n")
    md.append(
        "- **OpenStreetMap completeness.** OSM is community-mapped; if a court "
        "isn't tagged we can't count it. Brighton appears well-mapped on a manual "
        "spot-check (98 courts at 25 facilities is consistent with the city's "
        "BHPLTA member sites plus the council park courts).\n"
        "- **Geographic scope.** Full UK — England + Wales LSOAs (ONS), Scotland "
        "Data Zones (NRS), Northern Ireland Data Zones (NISRA). 75 of 76 cities "
        "above 100k are ranked.\n"
        "- **Population data.** Latest published mid-year LSOA estimates for "
        "England + Wales (2011 boundaries), 2011 census Data Zone counts for "
        "Scotland, 2021 census Data Zone counts for Northern Ireland.\n"
        "- **Polygon containment.** Each city's residents are those whose small-"
        "area centroid sits inside the city's administrative bounding box. The "
        f"{int(bh_pa.get('pop_in_bbox', 0)):,} residents counted for Brighton "
        "& Hove are those inside the Brighton & Hove unitary authority polygon "
        "(matching what residents call 'Brighton & Hove' day-to-day). Worthing "
        "and Lancing — bundled into the larger 'Brighton' BUA in 2011 census "
        "geography — aren't counted on either side.\n"
    )

    out_path = REPORTS / "brighton_tennis.md"
    out_path.write_text("".join(md))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
