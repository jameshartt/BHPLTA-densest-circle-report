# Methodology

## Definitions

- **Court**: a single physical tennis court (singles or doubles). Multi-court facilities count each surface separately.
- **Club / facility**: a contiguous site hosting one or more courts. A park with 6 courts = 1 facility, 6 courts.
- **Non-private**: court is accessible to the public, members of the general public, or paying customers — NOT restricted to a closed membership of a private club. We err on the side of inclusion when access tagging is missing.

## City selection (Phase 1: UK)

- Source: ONS Built-Up Area population estimates (mid-year, latest available).
- Threshold: BUA population >= 100,000.
- Fallback for boundary geometry: query Nominatim/Overpass for the BUA polygon, or use ONS Open Geography Portal shapefiles.

## Court extraction (OSM)

Overpass QL query per city polygon:

```
(
  node["leisure"="pitch"]["sport"~"tennis"](area);
  way["leisure"="pitch"]["sport"~"tennis"](area);
  relation["leisure"="pitch"]["sport"~"tennis"](area);

  node["leisure"="sports_centre"]["sport"~"tennis"](area);
  way["leisure"="sports_centre"]["sport"~"tennis"](area);

  node["club"="tennis"](area);
  way["club"="tennis"](area);
  relation["club"="tennis"](area);
);
out center tags;
```

**Filtering**:

- Drop `access=private` outright.
- Tag `access=members` items as "members club" — reported separately, NOT in primary count.
- Keep `access` in {public, customers, yes, permissive, unknown/missing} as the primary count.

**Count inference** — a `leisure=pitch` is typically ONE court. But:
- If tagged with `tennis:courts=N`, use N.
- If the way's bounding box clearly contains multiple court footprints (>~30m x >~25m), CV verification may revise upward.

## Club inference

Two complementary signals:

1. **Explicit**: any `leisure=sports_centre` with tennis, or `club=tennis` — counts as 1 club.
2. **Implicit (clustering)**: DBSCAN on court centroids with eps ~75m. Each resulting cluster = 1 facility. A "club" must contain at least 1 court.

Final club count per city = `count(distinct facilities from either signal)` after deduping overlaps.

## CV verification

**Goal**: estimate the false-positive rate of OSM tagging (courts that aren't really tennis courts anymore, or never were) and spot-check undercounting.

**Approach**:

- Fetch a 256x256 satellite tile centered on each sampled court at zoom 19 (~0.3m/px → covers ~75x75m).
- Imagery source priority:
  1. Esri World Imagery REST tiles (free, attribution required, non-commercial OK for research)
  2. Mapbox Static API (free tier 50k/month)
  3. Bing Maps Aerial (free with key)
- Classification: start with **CLIP zero-shot** ("a tennis court seen from above" vs "not a tennis court"). If too noisy, train a small classifier on a hand-labeled set.
- Sample size: 300 random courts for UK Phase 1. Report precision of OSM tagging.

**Stretch** (Phase 1+): grid-scan a few cities to find courts OSM missed. Run detection across the full city bbox at zoom 18, dedupe hits within 30m, compare against OSM set. Only feasible for ~5 sampled cities due to tile volume.

## Per-capita stats

For each city:
- `courts_per_100k = total_courts / population * 100000`
- `clubs_per_100k = total_clubs / population * 100000`
- Reported with confidence interval derived from CV-verification precision.

## Output

Report (`reports/uk_report.md`) includes:

- Methodology notes
- Ranked tables: top 20 and bottom 20 cities by each metric
- Histograms + scatter of population vs courts
- CV verification summary (precision, sample size)
- Notes on data-quality caveats per region

## Known limitations

- **OSM coverage variance**: UK is well-mapped; some smaller cities may still undercount. CV verification mitigates this on a sample basis only.
- **Access tagging incomplete**: many UK clubs lack explicit `access` tags. Default-inclusive policy may overstate "non-private" counts; documented in the report.
- **Court vs facility ambiguity**: some OSM ways tag an entire block of courts as one pitch. Multi-court inference via bbox size is heuristic.
- **CV cost**: per-court tile fetching is bounded by free-tier limits; falls back to sampling.
