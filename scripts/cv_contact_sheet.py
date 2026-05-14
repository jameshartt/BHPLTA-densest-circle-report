"""Render a contact sheet of CV-sampled court tiles for human inspection.

Reads data/processed/uk_cv_sample.csv and produces:
  reports/uk_cv_lowconf.png  -- 25 lowest p_tennis (likely false positives)
  reports/uk_cv_highconf.png -- 25 highest p_tennis (sanity check on CLIP)
  reports/uk_cv_random.png   -- 25 randomly sampled

Each cell is annotated with city + p_tennis.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
IMAGERY = ROOT / "data" / "imagery"
REPORTS = ROOT / "reports"


def deg2num_float(lat_deg: float, lon_deg: float, zoom: int) -> tuple[float, float]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def stitched_tile(lat: float, lon: float, zoom: int) -> Image.Image | None:
    fx, fy = deg2num_float(lat, lon, zoom)
    bx = int(math.floor(fx - 0.5))
    by = int(math.floor(fy - 0.5))
    canvas = Image.new("RGB", (512, 512))
    for dx in range(2):
        for dy in range(2):
            cache_path = IMAGERY / "esri" / f"z{zoom}_x{bx + dx}_y{by + dy}.jpg"
            if not cache_path.exists():
                return None
            try:
                tile = Image.open(cache_path).convert("RGB")
            except Exception:
                return None
            canvas.paste(tile, (dx * 256, dy * 256))
    px = int((fx - bx) * 256)
    py = int((fy - by) * 256)
    half = 192
    left = max(0, px - half)
    upper = max(0, py - half)
    right = min(512, left + half * 2)
    lower = min(512, upper + half * 2)
    if right - left < half * 2:
        left = right - half * 2
    if lower - upper < half * 2:
        upper = lower - half * 2
    return canvas.crop((left, upper, right, lower))


def render_grid(rows: list[dict], out: Path, zoom: int, title: str, n: int = 25) -> None:
    rows = rows[:n]
    cols = 5
    rs = (len(rows) + cols - 1) // cols
    fig, axes = plt.subplots(rs, cols, figsize=(cols * 3, rs * 3))
    fig.suptitle(title, fontsize=14)
    if rs == 1:
        axes = [axes]
    for i, row in enumerate(rows):
        ax = axes[i // cols][i % cols]
        lat = float(row["lat"])
        lon = float(row["lon"])
        img = stitched_tile(lat, lon, zoom)
        if img is None:
            ax.text(0.5, 0.5, "no tile", ha="center", va="center")
        else:
            ax.imshow(img)
        ax.set_title(
            f"{row['city_name'][:20]}\np_tennis={float(row['p_tennis']):.2f}",
            fontsize=8,
        )
        ax.axis("off")
    # Hide unused axes
    for j in range(len(rows), rs * cols):
        axes[j // cols][j % cols].axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    ap.add_argument("--zoom", type=int, default=18)
    args = ap.parse_args()

    sample_csv = PROCESSED / f"{args.region}_cv_sample.csv"
    if not sample_csv.exists():
        print(f"missing {sample_csv}; run scripts/05_cv_verify.py first", file=sys.stderr)
        return 1

    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(sample_csv.open()))
    rows.sort(key=lambda r: float(r["p_tennis"]))

    render_grid(rows, REPORTS / f"{args.region}_cv_lowconf.png", args.zoom,
                "CV-sample: 25 lowest-confidence courts (p_tennis ascending)", 25)
    render_grid(list(reversed(rows)), REPORTS / f"{args.region}_cv_highconf.png", args.zoom,
                "CV-sample: 25 highest-confidence courts (p_tennis descending)", 25)
    print("wrote contact sheets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
