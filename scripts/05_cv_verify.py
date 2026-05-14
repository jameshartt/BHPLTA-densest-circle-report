"""CV verification: sample OSM-tagged courts, fetch satellite tiles, score with
CLIP zero-shot to estimate the false-positive rate of OSM tagging.

Pipeline:
  1. Load data/processed/uk_clubs.csv to get club centroids.
  2. Load data/processed/uk_tennis_facilities.csv to get individual court
     points (kind=court only).
  3. Random sample N courts.
  4. For each sampled court, fetch a satellite tile centered on it (Esri World
     Imagery, zoom 19, 256x256). Cache locally.
  5. Run CLIP zero-shot with prompts:
       a) "an aerial photo of a tennis court"
       b) "an aerial photo of empty ground"
       c) "an aerial photo of buildings"
       d) "an aerial photo of a sports field"
     Classify as tennis if (a) is top.
  6. Output data/processed/uk_cv_sample.csv with score per court.
  7. Print precision summary.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import random
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
IMAGERY = ROOT / "data" / "imagery"

USER_AGENT = "tennis-courts-analysis/0.1 (research; jameshartt@gmail.com)"
ESRI_TILE_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/tile/{z}/{y}/{x}"
)

CLIP_PROMPTS = [
    # Tennis variants (positive class)
    "an aerial photo of a tennis court",
    "an aerial photo of a hard tennis court",
    "an aerial photo of a clay tennis court",
    "an aerial photo of a grass tennis court",
    "an aerial photo of multiple tennis courts side by side",
    # Negatives
    "an aerial photo of an empty grass field",
    "an aerial photo of buildings or rooftops",
    "an aerial photo of a football or soccer pitch",
    "an aerial photo of a basketball court",
    "an aerial photo of trees or forest",
    "an aerial photo of a road or car park",
    "an aerial photo of a residential garden",
]
TENNIS_PROMPT_INDICES = [0, 1, 2, 3, 4]  # first 5 are tennis


def deg2num_float(lat_deg: float, lon_deg: float, zoom: int) -> tuple[float, float]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def fetch_tile_xy(x: int, y: int, zoom: int) -> bytes | None:
    cache_path = IMAGERY / "esri" / f"z{zoom}_x{x}_y{y}.jpg"
    if cache_path.exists():
        return cache_path.read_bytes()
    url = ESRI_TILE_URL.format(z=zoom, x=x, y=y)
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  tile fetch failed: {e}")
        return None
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(r.content)
    return r.content


def stitched_tile(lat: float, lon: float, zoom: int) -> Image.Image | None:
    """Fetch a 2x2 stitch of tiles centered as best as possible on (lat, lon)
    and crop to a 384x384 view centered on the point."""
    fx, fy = deg2num_float(lat, lon, zoom)
    # base tile (top-left of 2x2): floor of (fx-0.5, fy-0.5)
    bx = int(math.floor(fx - 0.5))
    by = int(math.floor(fy - 0.5))
    canvas = Image.new("RGB", (512, 512))
    for dx in range(2):
        for dy in range(2):
            data = fetch_tile_xy(bx + dx, by + dy, zoom)
            if data is None:
                return None
            try:
                tile = Image.open(io.BytesIO(data)).convert("RGB")
            except Exception:
                return None
            canvas.paste(tile, (dx * 256, dy * 256))
    # The lat/lon falls at pixel (offset_x, offset_y) inside the canvas
    px = int((fx - bx) * 256)
    py = int((fy - by) * 256)
    half = 192  # 384x384 crop
    left = max(0, px - half)
    upper = max(0, py - half)
    right = min(512, left + half * 2)
    lower = min(512, upper + half * 2)
    if right - left < half * 2:
        left = right - half * 2
    if lower - upper < half * 2:
        upper = lower - half * 2
    return canvas.crop((left, upper, right, lower))


def load_clip():
    from transformers import CLIPModel, CLIPProcessor
    print("loading CLIP model (openai/clip-vit-base-patch32) ...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.eval()
    return model, processor


def clip_score(model, processor, image: Image.Image, prompts: list[str]):
    import torch
    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model(**inputs)
    probs = out.logits_per_image.softmax(dim=-1)[0].tolist()
    return probs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="uk")
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--zoom", type=int, default=18)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    facilities = PROCESSED / f"{args.region}_tennis_facilities.csv"
    if not facilities.exists():
        print(f"missing {facilities}", file=sys.stderr)
        return 1

    rows = [r for r in csv.DictReader(facilities.open()) if r["kind"] == "court"]
    print(f"total courts available: {len(rows)}")
    random.seed(args.seed)
    sample = random.sample(rows, min(args.sample, len(rows)))
    print(f"sampling {len(sample)} courts")

    model, processor = load_clip()

    out_rows: list[dict] = []
    for i, row in enumerate(sample):
        lat = float(row["lat"])
        lon = float(row["lon"])
        img = stitched_tile(lat, lon, args.zoom)
        if img is None:
            continue
        time.sleep(0.05)  # be polite
        probs = clip_score(model, processor, img, CLIP_PROMPTS)
        p_tennis_total = sum(probs[i] for i in TENNIS_PROMPT_INDICES)
        top_idx = probs.index(max(probs))
        # Tennis if aggregate tennis-prompt probability is the dominant class
        is_tennis = int(p_tennis_total > 0.50 or top_idx in TENNIS_PROMPT_INDICES)
        out_rows.append({
            "osm_type": row["osm_type"],
            "osm_id": row["osm_id"],
            "city_name": row["city_name"],
            "lat": lat,
            "lon": lon,
            "p_tennis": round(p_tennis_total, 4),
            "top_prompt_idx": top_idx,
            "is_tennis": is_tennis,
        })
        if (i + 1) % 25 == 0:
            print(f"  scored {i + 1}/{len(sample)}; running precision: "
                  f"{sum(r['is_tennis'] for r in out_rows)/len(out_rows):.1%}")

    out_csv = PROCESSED / f"{args.region}_cv_sample.csv"
    fieldnames = ["osm_type", "osm_id", "city_name", "lat", "lon", "p_tennis",
                  "top_prompt_idx", "is_tennis"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    precision = sum(r["is_tennis"] for r in out_rows) / len(out_rows) if out_rows else 0.0
    print(f"\nwrote {out_csv} with {len(out_rows)} scored courts")
    print(f"OSM-tagged precision (CLIP zero-shot): {precision:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
