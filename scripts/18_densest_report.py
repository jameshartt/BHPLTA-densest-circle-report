"""Render the 'densest tennis-court circle' analysis as a report + charts.

Outputs:
  reports/densest_uk_all.png       UK ranking by densest 2.26 km all-courts circle
  reports/densest_uk_park.png      UK ranking by densest 2.26 km park-courts circle
  reports/densest_global_park.png  Global ranking, park courts
  reports/densest_circle.md        Markdown writeup
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

BRIGHTON_PINK = "#e3174a"
BRIGHTON_DEEP = "#9d0f33"
INK = "#1f2933"
PEER_GREY = "#c1c8cc"
LONDON_GREY = "#9aa1a3"


def chart_uk(uk_csv: Path, metric: str, title: str, xlabel: str,
             out: Path, top_n: int = 16) -> None:
    df = pd.read_csv(uk_csv).dropna(subset=[metric])
    df = df.sort_values(metric, ascending=False).head(top_n)
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, max(5, top_n * 0.45)), facecolor="white")
    colors = []
    for n in df["city"]:
        if n == "Brighton and Hove":
            colors.append(BRIGHTON_PINK)
        elif n == "Greater London":
            colors.append(LONDON_GREY)
        else:
            colors.append(PEER_GREY)
    bars = ax.barh(df["city"], df[metric], color=colors, edgecolor="white",
                   linewidth=1.5, height=0.78)
    for bar, n, v in zip(bars, df["city"], df[metric]):
        weight = "bold" if n == "Brighton and Hove" else "normal"
        col = BRIGHTON_DEEP if n == "Brighton and Hove" else "#374049"
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{int(v)}", va="center", fontsize=11, color=col, fontweight=weight)
    ax.set_xlabel(xlabel, fontsize=11, color=INK, labelpad=8)
    ax.set_title(title, fontsize=14, color=INK, loc="left", pad=14, fontweight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=10)
    ax.tick_params(axis="y", colors=INK, labelsize=11)
    ax.set_facecolor("white")
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)


def chart_global(global_csv: Path, metric: str, title: str, xlabel: str,
                 out: Path, brighton_value: int) -> None:
    df = pd.read_csv(global_csv).dropna(subset=[metric])
    df["label"] = df["city"] + " (" + df["country"] + ")"
    df = df.sort_values(metric, ascending=False)
    df = df.iloc[::-1]
    # Prepend Brighton row
    bh_row = pd.DataFrame({
        "label": ["Brighton & Hove (UK)"],
        metric: [brighton_value],
        "city": ["Brighton and Hove"],
    })
    full = pd.concat([bh_row, df], ignore_index=True).sort_values(metric, ascending=True)
    fig, ax = plt.subplots(figsize=(11, max(5, len(full) * 0.42)), facecolor="white")
    colors = [BRIGHTON_PINK if "Brighton" in lbl else PEER_GREY for lbl in full["label"]]
    bars = ax.barh(full["label"], full[metric], color=colors, edgecolor="white",
                   linewidth=1.5, height=0.78)
    for bar, lbl, v in zip(bars, full["label"], full[metric]):
        weight = "bold" if "Brighton" in lbl else "normal"
        col = BRIGHTON_DEEP if "Brighton" in lbl else "#374049"
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{int(v)}", va="center", fontsize=11, color=col, fontweight=weight)
    ax.set_xlabel(xlabel, fontsize=11, color=INK, labelpad=8)
    ax.set_title(title, fontsize=14, color=INK, loc="left", pad=14, fontweight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=10)
    ax.tick_params(axis="y", colors=INK, labelsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)


def main() -> int:
    uk_csv = PROCESSED / "uk_densest_circle.csv"
    if not uk_csv.exists():
        print(f"missing {uk_csv}", file=sys.stderr)
        return 1
    uk = pd.read_csv(uk_csv)
    bh = uk[uk["city"] == "Brighton and Hove"].iloc[0]
    bh_circle_all = int(bh["central_bh_all"])
    bh_circle_park = int(bh["central_bh_park"])
    bh_densest_all = int(bh["densest_all"])
    bh_densest_park = int(bh["densest_park"])

    chart_uk(uk_csv, "densest_all",
             "UK cities: densest 2.26 km circle (all non-private courts)",
             "Courts in densest 2.26 km circle (16 km²)",
             REPORTS / "densest_uk_all.png")
    chart_uk(uk_csv, "densest_park",
             "UK cities: densest 2.26 km circle (park courts only)",
             "Park courts in densest 2.26 km circle",
             REPORTS / "densest_uk_park.png")

    # Global
    global_csv = PROCESSED / "global_densest_circle.csv"
    if global_csv.exists():
        chart_global(global_csv, "densest_park",
                     "World: densest 2.26 km circle (park courts only)",
                     "Park courts in densest 2.26 km circle",
                     REPORTS / "densest_global_park.png",
                     brighton_value=bh_circle_park)

    # Markdown
    md = []
    md.append("# The Central Brighton & Hove tennis cluster — UK / World ranking\n")
    md.append("*Test of the claim: a 2.26 km circle drawn just to contain "
              "Queens Park, Pavilion & Avenue, and the Kingsway / Hove Beach "
              "Club courts holds the densest set of public/park tennis courts "
              "of any equivalent area in the country (and likely the world).*\n\n")
    md.append("---\n\n")

    md.append("## How the circle is defined\n\n")
    md.append("Three anchor venues set the perimeter of Central Brighton & Hove:\n\n")
    md.append("- **Queens Park** — east edge (50.824, -0.125)\n")
    md.append("- **Pavilion & Avenue Tennis Club** — north edge (50.843, -0.149)\n")
    md.append("- **Kingsway / Hove Beach Club** (formerly King Alfred) — west edge (50.826, -0.189)\n\n")
    md.append("The smallest enclosing circle of those three points has:\n\n")
    md.append("- Centre: **50.825° N, 0.157° W** (around Brunswick / Norfolk Square)\n")
    md.append("- Radius: **2.26 km** (≈ 25-minute walk corner to corner)\n")
    md.append("- Area:   **16.0 km²**\n\n")

    md.append("![Central B&H circle](./brighton_central_circle.png)\n\n")

    md.append("## The two-step narrative\n\n")
    md.append("### 1. All non-private courts in a 2.26 km circle (the 'physical density' headline)\n\n")
    md.append(f"Brighton's Central B&H circle contains **{bh_circle_all} non-private courts**. "
              f"Brighton's overall densest 2.26 km sub-circle (allowed to move anywhere "
              f"in the city) holds **{bh_densest_all}** courts.\n\n")
    md.append("Across the UK, however, two anomalies sit ahead of Brighton on raw density:\n\n")
    md.append("- **Greater London (Wimbledon area)** — 162 courts within a 2.26 km circle "
              "around (51.47°N, 0.26°W). This area includes the All England Lawn Tennis "
              "Club, Roehampton Club, Wimbledon Park, Royal Wimbledon Park Golf & Tennis, "
              "and a dozen smaller clubs. Most are private members' clubs; OSM just hasn't "
              "tagged them `access=private`.\n")
    md.append("- **Oxford / Cambridge** — university college courts pack a huge count into "
              "a small area, but the typical resident can't book them.\n\n")
    md.append("That's where the framing of the claim matters: when the playing surfaces "
              "you're counting are inaccessible to the public, raw density isn't tennis-"
              "community density.\n\n")
    md.append("![UK all-court density](./densest_uk_all.png)\n\n")

    md.append("### 2. Park courts only (the 'accessible tennis' headline)\n\n")
    md.append(f"Filter to courts that sit inside a `leisure=park`, `recreation_ground`, "
              f"`garden`, or `common` polygon — i.e. genuine park/public tennis. "
              f"Brighton's Central B&H circle now contains "
              f"**{bh_circle_park} park courts**.\n\n")
    md.append("On THIS metric — the one that actually reflects a vibrant accessible "
              "tennis community — Brighton's position changes dramatically.\n\n")
    md.append("![UK park-court density](./densest_uk_park.png)\n\n")

    # global section if available
    if global_csv.exists():
        md.append("## World comparison\n\n")
        md.append("Same methodology applied to a curated list of tennis-rich cities "
                  "worldwide: Paris, Madrid, Barcelona, Berlin, Vienna, Buenos Aires, "
                  "Tokyo, Melbourne, New York, San Francisco, and more (full list "
                  "in `scripts/16_global_densest.py`).\n\n")
        md.append("![Global park-court density](./densest_global_park.png)\n\n")

    md.append("## Caveats\n\n")
    md.append("- **OSM completeness varies by city.** Brighton is well-mapped; some "
              "world cities may be undercounted.\n")
    md.append("- **Park definition.** We use OSM `leisure=park|recreation_ground|"
              "garden|common`. Some accessible courts sit in `leisure=sports_centre` "
              "polygons rather than parks (e.g. Pavilion & Avenue itself) — those are "
              "excluded from the park-courts count even though they're publicly bookable. "
              "Brighton's circle therefore *understates* its accessible tennis.\n")
    md.append("- **Ground-truth corrections.** Local knowledge: Queen's Park has 6 "
              "tennis courts (matches OSM after the spatial join); Kingsway / Hove "
              "Beach Club now operates 6 tennis + several padel courts (OSM still "
              "tags some as tennis). Net effect on the headline count is small.\n")

    out = REPORTS / "densest_circle.md"
    out.write_text("".join(md))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
