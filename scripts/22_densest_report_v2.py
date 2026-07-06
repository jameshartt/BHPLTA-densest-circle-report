"""Final densest-circle report with sea correction.

Reads:
  data/processed/uk_density_sea_corrected.csv
  data/processed/global_density_sea_corrected.csv
  data/processed/brighton_circle_land.json

Outputs:
  reports/densest_uk_park_corrected.png
  reports/densest_global_park_corrected.png
  reports/densest_circle.md
"""

from __future__ import annotations

import csv
import json
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


def chart_bar(df: pd.DataFrame, metric: str, label_col: str,
              title: str, xlabel: str, out: Path,
              brighton_label: str = "Brighton and Hove",
              top_n: int = 15) -> None:
    df = df.sort_values(metric, ascending=False).head(top_n)
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, max(5, top_n * 0.40)), facecolor="white")
    colors = [BRIGHTON_PINK if l == brighton_label else PEER_GREY for l in df[label_col]]
    bars = ax.barh(df[label_col], df[metric], color=colors, edgecolor="white",
                   linewidth=1.5, height=0.78)
    for bar, l, v in zip(bars, df[label_col], df[metric]):
        weight = "bold" if l == brighton_label else "normal"
        col = BRIGHTON_DEEP if l == brighton_label else "#374049"
        ax.text(v + 0.02 * max(df[metric]),
                bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}", va="center", fontsize=10, color=col, fontweight=weight)
    ax.set_xlabel(xlabel, fontsize=11, color=INK, labelpad=8)
    ax.set_title(title, fontsize=13, color=INK, loc="left", pad=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", colors="#5a5a5a", labelsize=10)
    ax.tick_params(axis="y", colors=INK, labelsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)


def main() -> int:
    uk_csv = PROCESSED / "uk_density_final.csv"
    global_csv = PROCESSED / "global_density_final.csv"

    if not uk_csv.exists():
        print(f"missing {uk_csv}", file=sys.stderr)
        return 1
    uk = pd.read_csv(uk_csv)
    bh = uk[uk["city"] == "Brighton and Hove"].iloc[0]
    bh_uc_park = int(bh["central_bh_public_park"])
    bh_uc_land = float(bh["central_bh_land_km2"])
    bh_uc_density = float(bh["central_bh_density_per_km2_land"])

    chart_bar(uk, "density_public_park_per_km2_land", "city",
              "UK cities: PUBLIC park courts per km² of LAND in densest 2.34 km circle",
              "Public park courts per km² land",
              REPORTS / "densest_uk_park_corrected.png")

    if global_csv.exists():
        glob = pd.read_csv(global_csv)
        glob["city_country"] = glob["city"] + " (" + glob["country"] + ")"

        # Ground-truth corrections consolidated in data/processed/ground_truth.csv
        # (sourced from the per-city audits in reports/ground_truth/*.md).
        # Override OSM-strict densities with audit-corrected values where the
        # audit found systematic bias. The chart shows the Step 6 admin-clip
        # ground-truth densities.
        gt_rows = pd.read_csv(PROCESSED / "ground_truth.csv").set_index("city")
        for i, row in glob.iterrows():
            if row["city"] in gt_rows.index:
                gt = gt_rows.loc[row["city"]]
                glob.at[i, "densest_public_park"] = int(gt["gt_count"])
                glob.at[i, "density_public_park_per_km2_land"] = float(gt["adminclip_density"])

        # Use Brighton's BHPLTA ground-truth (43 / 10.9 = 3.94) for the
        # global comparison — the specific claim under test.
        bh_gt = gt_rows.loc["Brighton and Hove"]
        bh_glob = pd.DataFrame({
            "city": ["Brighton and Hove"],
            "city_country": ["Brighton & Hove (UK) — user circle"],
            "country": ["UK"],
            "densest_public_park": [int(bh_gt["gt_count"])],
            "land_km2": [float(bh_gt["adminclip_land_km2"])],
            "density_public_park_per_km2_land": [float(bh_gt["adminclip_density"])],
        })
        # Greater London ground-truth (no audit corrections)
        ldn = uk[uk["city"] == "Greater London"]
        if not ldn.empty:
            row = ldn.iloc[0]
            ldn_gt = gt_rows.loc["Greater London"]
            ldn_glob = pd.DataFrame({
                "city": ["Greater London"],
                "city_country": ["Greater London (UK) — Battersea / Kennington"],
                "country": ["UK"],
                "densest_public_park": [int(ldn_gt["gt_count"])],
                "land_km2": [float(row["land_km2"])],
                "density_public_park_per_km2_land": [float(ldn_gt["adminclip_density"])],
            })
            glob = pd.concat([bh_glob, ldn_glob, glob], ignore_index=True)
        else:
            glob = pd.concat([bh_glob, glob], ignore_index=True)
        chart_bar(glob, "density_public_park_per_km2_land", "city_country",
                  "World: PUBLIC park courts per km² of LAND (densest 2.34 km circle, ground-truth-corrected)",
                  "Public park courts per km² land (ground-truth)",
                  REPORTS / "densest_global_park_corrected.png",
                  brighton_label="Brighton & Hove (UK) — user circle")

    # Markdown
    md = []
    md.append("# Brighton & Hove: densest tennis cluster in the world?\n")
    md.append("*Park-courts density per square kilometre of LAND in a "
              "2.34 km circle just enclosing Queens Park, Pavilion & Avenue, "
              "Blakers Park and Kingsway / Hove Beach Club.*\n\n")
    md.append("---\n\n")

    md.append("## Brighton's 'Central B&H' circle\n\n")
    bh_circle = json.loads((PROCESSED / "brighton_circle_land.json").read_text())
    md.append(f"- Centre: {bh_circle['center_lat']:.4f}°N, "
              f"{abs(bh_circle['center_lon']):.4f}°W\n")
    md.append(f"- Radius: {bh_circle['radius_m']:.0f} m\n")
    md.append(f"- Disc area: {bh_circle['disc_area_km2']:.2f} km²\n")
    md.append(f"- **Land area: {bh_circle['land_area_km2']:.2f} km² "
              f"({bh_circle['pct_sea']:.1f}% of the disc is sea)**\n")
    md.append(f"- Park courts within the circle: **{bh_circle['park_courts_in_circle']}**\n")
    md.append(f"- Park-court density: "
              f"**{bh_circle['park_courts_in_circle']/bh_circle['land_area_km2']:.2f} "
              f"park courts per km² of land**\n\n")
    md.append("![Central B&H circle](./brighton_central_circle.png)\n\n")

    md.append("## UK ranking (sea-corrected)\n\n")
    md.append("Park courts per km² of LAND in each city's densest 2.34 km circle:\n\n")
    md.append("![UK ranking](./densest_uk_park_corrected.png)\n\n")

    if global_csv.exists():
        md.append("## World ranking (sea-corrected)\n\n")
        md.append("Same metric across major global cities. Brighton & Hove "
                  "highlighted. Cities flagged 'bbox' lack a clean OSM admin "
                  "polygon so their numbers are NOT sea-corrected and are "
                  "therefore upper bounds.\n\n")
        md.append("![Global ranking](./densest_global_park_corrected.png)\n\n")

    md.append("## Caveats\n\n")
    md.append("- **Park-courts only.** Courts that sit inside a "
              "`leisure=park`, `recreation_ground`, `garden` or `common` "
              "polygon. Excludes private clubs, college courts, and clubs "
              "that aren't in a park.\n")
    md.append("- **Sea correction.** Land area computed by intersecting the "
              "densest 2.34 km circle with the city's OSM admin-boundary "
              "polygon. For cities defined by bbox (Tokyo 23 wards, "
              "Melbourne, Sydney, Auckland) no boundary polygon exists, so "
              "those numbers are not corrected and overstate density.\n")
    md.append("- **'Park courts' can still include private clubs that sit "
              "physically inside a public park polygon.** Notably Paris's "
              "headline cluster is in the Bois de Boulogne, which contains "
              "Roland Garros and the major French members' clubs. A future "
              "iteration excludes courts inside `leisure=sports_centre` / "
              "`club=tennis` polygons.\n")

    out = REPORTS / "densest_circle.md"
    out.write_text("".join(md))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
