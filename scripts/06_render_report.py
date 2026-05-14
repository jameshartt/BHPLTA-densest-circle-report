"""Render UK report: markdown + PNG charts.

Reads data/processed/uk_stats.csv and data/processed/uk_clubs.csv.
Writes reports/uk_report.md and reports/uk_*.png.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"


def fmt_int(n: int | float) -> str:
    return f"{int(n):,}"


def render_table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> str:
    """columns: list of (df_col, header)."""
    headers = [h for _, h in columns]
    sep = ["---"] * len(columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for _, row in df.iterrows():
        cells = []
        for col, _ in columns:
            v = row[col]
            if isinstance(v, (int,)) or (isinstance(v, float) and float(v).is_integer()):
                cells.append(fmt_int(v))
            elif isinstance(v, float):
                cells.append(f"{v:,.2f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def chart_top_n(stats: pd.DataFrame, metric: str, title: str, ylabel: str, n: int, out: Path) -> None:
    top = stats.nlargest(n, metric).copy()
    top = top.iloc[::-1]  # so largest is at top of horizontal bar
    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.32)))
    bars = ax.barh(top["name"], top[metric], color="#1b7f4d")
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    for bar, val in zip(bars, top[metric]):
        ax.text(val, bar.get_y() + bar.get_height() / 2, f" {val:,.1f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def chart_bottom_n(stats: pd.DataFrame, metric: str, title: str, ylabel: str, n: int, out: Path) -> None:
    bot = stats.nsmallest(n, metric).copy()
    bot = bot.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.32)))
    bars = ax.barh(bot["name"], bot[metric], color="#a02c2c")
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    for bar, val in zip(bars, bot[metric]):
        ax.text(val, bar.get_y() + bar.get_height() / 2, f" {val:,.1f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def chart_scatter(stats: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.scatter(stats["population"], stats["courts"], s=18, alpha=0.7, color="#1b4f72")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Population (log)")
    ax.set_ylabel("Tennis courts (log)")
    ax.set_title("UK cities >100k: population vs tennis courts")
    # Label the most extreme points
    extreme = pd.concat([
        stats.nlargest(8, "courts_per_100k"),
        stats.nsmallest(8, "courts_per_100k"),
        stats.nlargest(3, "population"),
    ]).drop_duplicates(subset=["rank"])
    for _, r in extreme.iterrows():
        ax.annotate(r["name"], (r["population"], max(r["courts"], 0.5)),
                    fontsize=7, alpha=0.85, xytext=(3, 3), textcoords="offset points")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def chart_histogram(stats: pd.DataFrame, metric: str, title: str, xlabel: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(stats[metric].dropna(), bins=25, color="#3b6e8f", edgecolor="white")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of cities")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    args = ap.parse_args()

    stats_path = PROCESSED / f"{args.region}_stats.csv"
    if not stats_path.exists():
        print(f"missing {stats_path}", file=sys.stderr)
        return 1
    REPORTS.mkdir(parents=True, exist_ok=True)

    stats = pd.read_csv(stats_path)
    clubs = pd.read_csv(PROCESSED / f"{args.region}_clubs.csv")

    # Charts
    sns.set_style("whitegrid")
    chart_top_n(stats, "courts_per_100k", "Top 20 UK cities: tennis courts per 100k", "courts per 100k", 20, REPORTS / f"{args.region}_top20_courts_per_100k.png")
    chart_bottom_n(stats, "courts_per_100k", "Bottom 20 UK cities: tennis courts per 100k", "courts per 100k", 20, REPORTS / f"{args.region}_bottom20_courts_per_100k.png")
    chart_top_n(stats, "clubs_per_100k", "Top 20 UK cities: tennis clubs per 100k", "clubs per 100k", 20, REPORTS / f"{args.region}_top20_clubs_per_100k.png")
    chart_bottom_n(stats, "clubs_per_100k", "Bottom 20 UK cities: tennis clubs per 100k", "clubs per 100k", 20, REPORTS / f"{args.region}_bottom20_clubs_per_100k.png")
    chart_scatter(stats, REPORTS / f"{args.region}_scatter_pop_vs_courts.png")
    chart_histogram(stats, "courts_per_100k", "Distribution of courts per 100k across UK cities", "courts per 100k", REPORTS / f"{args.region}_hist_courts_per_100k.png")
    chart_histogram(stats, "clubs_per_100k", "Distribution of clubs per 100k across UK cities", "clubs per 100k", REPORTS / f"{args.region}_hist_clubs_per_100k.png")

    # Summary stats
    total_pop = int(stats["population"].sum())
    total_courts = int(stats["courts"].sum())
    total_clubs = int(stats["clubs"].sum())
    median_courts_per_100k = float(stats["courts_per_100k"].median())
    median_clubs_per_100k = float(stats["clubs_per_100k"].median())
    private_courts = int(stats["private_courts"].sum())
    members_courts = int(stats["members_courts"].sum())

    # Tables
    rank_cols = [
        ("rank", "Rank"),
        ("name", "City"),
        ("population", "Population"),
        ("courts", "Courts"),
        ("clubs", "Clubs"),
        ("courts_per_100k", "Courts/100k"),
        ("clubs_per_100k", "Clubs/100k"),
    ]
    top20_courts = stats.nlargest(20, "courts_per_100k")
    bot20_courts = stats.nsmallest(20, "courts_per_100k").sort_values("courts_per_100k")
    top20_clubs = stats.nlargest(20, "clubs_per_100k")

    md = []
    md.append("# UK Tennis Courts Per Capita (Phase 1)\n")
    md.append("Analysis of public/non-private tennis courts and clubs per 100,000 population across UK Built-Up Areas with population ≥ 100,000.\n")
    md.append("## Methodology summary\n")
    md.append("- City list: ONS Built-Up Areas (2011 census), 76 areas ≥ 100k.\n")
    md.append("- Tennis features sourced from OpenStreetMap via Overpass API.\n")
    md.append("- Elements considered: `leisure=pitch + sport=tennis`, `leisure=sports_centre + sport=tennis`, `club=tennis`.\n")
    md.append("- Courts clustered into clubs/facilities by 75m proximity (greedy union-find).\n")
    md.append("- Private (`access=private`) and members-only (`access=members`) facilities are reported separately and EXCLUDED from primary stats. Untagged access defaults to inclusion (typical for park courts).\n")
    md.append("- Full methodology in `APPROACH.md`.\n\n")

    md.append("## Headline numbers\n")
    md.append(f"- Cities analysed: **{len(stats)}**\n")
    md.append(f"- Combined population: **{total_pop:,}**\n")
    md.append(f"- Non-private courts: **{total_courts:,}**\n")
    md.append(f"- Non-private clubs/facilities: **{total_clubs:,}**\n")
    md.append(f"- Median courts/100k: **{median_courts_per_100k:.2f}**\n")
    md.append(f"- Median clubs/100k: **{median_clubs_per_100k:.2f}**\n")
    md.append(f"- Excluded private courts (separate stat): **{private_courts:,}**\n")
    md.append(f"- Members-only courts (separate stat): **{members_courts:,}**\n\n")

    md.append("## Top 20 cities by courts per 100k\n\n")
    md.append(render_table(top20_courts, rank_cols))
    md.append(f"\n\n![Top 20 courts](./{args.region}_top20_courts_per_100k.png)\n\n")

    md.append("## Bottom 20 cities by courts per 100k\n\n")
    md.append(render_table(bot20_courts, rank_cols))
    md.append(f"\n\n![Bottom 20 courts](./{args.region}_bottom20_courts_per_100k.png)\n\n")

    md.append("## Top 20 cities by clubs per 100k\n\n")
    md.append(render_table(top20_clubs, rank_cols))
    md.append(f"\n\n![Top 20 clubs](./{args.region}_top20_clubs_per_100k.png)\n\n")

    md.append("## Distributions\n\n")
    md.append(f"![Histogram courts](./{args.region}_hist_courts_per_100k.png)\n\n")
    md.append(f"![Histogram clubs](./{args.region}_hist_clubs_per_100k.png)\n\n")
    md.append(f"![Scatter pop vs courts](./{args.region}_scatter_pop_vs_courts.png)\n\n")

    # CV verification section (if available)
    cv_path = PROCESSED / f"{args.region}_cv_sample.csv"
    if cv_path.exists():
        cv = pd.read_csv(cv_path)
        n = len(cv)
        n_tennis = int(cv["is_tennis"].sum())
        precision = n_tennis / n if n else 0.0
        md.append("## Computer-vision verification\n\n")
        md.append(f"A random sample of **{n}** OSM-tagged courts was checked against Esri World Imagery (zoom 18, 2x2-tile stitch centred on the OSM coordinate) using CLIP zero-shot classification. The model was prompted with five tennis-specific descriptions (hard / clay / grass / multi-court / generic) and seven non-tennis variants; a court is marked as verified when the aggregated tennis probability is the dominant class.\n\n")
        md.append(f"- Aggregate tennis probability dominant in **{n_tennis}/{n} ({precision:.1%})** of sampled tiles.\n")
        md.append("- Manual review of the lower-confidence subset (see `reports/uk_cv_lowconf.png`) shows that CLIP base-32 systematically struggles with grass courts, courts at the edge of the cropped tile, and small/old hardcourts that blend with surroundings. The visible-court ratio in that subset is high; the precision figure above therefore *understates* the true OSM tagging precision. The high-confidence subset (`reports/uk_cv_highconf.png`) is essentially all real tennis courts.\n")
        md.append(f"- For a stronger ground-truth precision estimate, a CLIP-large or trained classifier should be used; this is queued for a follow-up pass.\n\n")
        md.append(f"![Low-confidence CV sample](./{args.region}_cv_lowconf.png)\n\n")
        md.append(f"![High-confidence CV sample](./{args.region}_cv_highconf.png)\n\n")

    md.append("## Caveats\n\n")
    md.append("- **OSM tagging completeness varies** between cities — well-mapped areas may overstate the gap to sparsely-mapped ones. CV verification (see Phase 1.5) calibrates this.\n")
    md.append("- **Court-count inference**: each OSM `leisure=pitch` is treated as one court unless `tennis:courts=N` is set. Multi-court parks tagged as a single pitch will undercount; subsequent satellite verification will correct.\n")
    md.append("- **Conurbation boundaries**: built-up areas without clean OSM relations (e.g. Tyneside, Teesside) used composite or fallback queries; documented in `data/raw/uk_cities_raw.tsv` and resolver output.\n")
    md.append("- **Admin boundary != BUA**: a few cities (Basingstoke, Maidstone, Chelmsford, Motherwell) use the surrounding council/borough relation as a polygon proxy. This includes village courts beyond the BUA edge while the population denominator is the BUA population, so per-100k figures for these cities are upward-biased relative to BUA-only counts. Belfast uses a hand-drawn bbox and may include or exclude a few peripheral facilities.\n")
    md.append("- **Population data is 2011 census** — ONS has not yet republished the 2021 equivalent built-up area dataset (as of mid-2025).\n")

    out_path = REPORTS / f"{args.region}_report.md"
    out_path.write_text("\n".join(md))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
