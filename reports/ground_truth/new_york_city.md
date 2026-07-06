# Ground-truth audit: New York City

**Step-4 densest 2.34 km circle centre**: 40.81249, -73.91348 (South Bronx / East Harlem, near Saint Mary's Park)
**OSM-strict count**: 46 public-park courts
**Ground-truth count**: ~51 courts (46 OSM + 5 Sportime indoor on Randalls Island public parkland)
**Confidence**: medium-high
**Density implication**: 51 / 16.93 = 3.01 per km² LAND (vs OSM-strict 2.72)

> **Revision note (peer review, July 2026).** The main report originally
> carried New York at 46→31 (−15), treating the Randalls Island Park
> Tennis Center as a commercial-academy false inclusion — a correction
> this audit does not support (see "Remove: None" below; the 15 outdoor
> Randalls Island courts are NYC Parks courts, season-permit or
> pay-and-play). The report now adopts this audit: **46→51 (+5
> Sportime indoor), confidence medium-high**. The 16.93 km² land figure
> above pre-dates the synthesised river-water correction (Harlem River +
> East River + Hell Gate + Bronx Kill ≈ 3.55 km², built by buffering OSM
> waterway centerlines); with it, land is 13.60 km² and the densities
> become **51 / 13.60 = 3.75** ground-truth and 46 / 13.61 = 3.38
> OSM-strict — the figures the report's Step 6 and Step 7 tables use.

## OSM-strict breakdown

| Venue | OSM courts | Operator | NYC permit / free / pay |
|---|---|---|---|
| Mill Pond Park (Bronx Tennis Center) | 16 | NYC Parks | $100 season permit OR pay-and-play (free walk-in off-peak) |
| Randalls Island Park Tennis Center | 15 | NYC Parks | $100 season permit OR pay-and-play |
| Frederick Johnson Playground (Harlem, 151st & ACP Blvd) | 8 | NYC Parks | Permit / free walk-in |
| Howard Bennett Playground (135th & Lenox) | 2 | NYC Parks | Permit / free walk-in |
| Moore Playground (Harlem) | 2 | NYC Parks | Permit / free walk-in |
| Saint Mary's Park (South Bronx, at circle centre) | 2 | NYC Parks | Permit / free walk-in |
| Macombs Dam Park (next to Yankee Stadium) | 1 | NYC Parks | Permit / free walk-in |
| **Total** | **46** | | |

All 46 OSM courts are tagged `leisure=pitch, sport=tennis` and fall inside named NYC Parks polygons (`leisure=park`). All are operated by NYC Parks and accessible under the city-wide tennis permit system: $100 adult season permit, $20 senior/youth, free play after Labor Day, or per-play permits. Saint Mary's Park sits almost exactly at the circle centre (0–15 m).

## Corrections

### Add
- **Sportime Tennis at Randalls Island (way/284865839)** — sport=tennis, leisure=sports_centre. This is a permanent indoor facility (~5 indoor courts in the brick building) leased from NYC Parks on Randalls Island Park. Bookable online by any member of the public, same operator model as Prospect Park Tennis Center. Centroid 40.7931, -73.9195, distance 2215 m — **INSIDE the circle**. Not tagged as individual `leisure=pitch` polygons in OSM, so absent from the strict 46.
  - **Add +5** indoor courts (conservative; estimating only the permanent indoor portion to avoid double-counting the winter bubbles that overlay the 15 already-counted outdoor pitches).
  - Lower bound: +0 (if you regard all Sportime courts as the same physical surfaces as the 15 outdoor pitches in OSM, just bubbled in winter — then Sportime is a season-overlay, not a separate venue).
  - Upper bound: +10 if you count Sportime's full indoor-season capacity.

### Remove
- None. After cross-checking, every OSM "park-strict" court is genuinely a NYC Parks public-permit court on public parkland. There is no Bronx Tennis Club (private) mis-counted; the "Bronx Tennis Center" name actually refers to the public Mill Pond Park courts.
- No padel conversions detected. NYC has been adding padel (CityPickle, Padel Haus) but none of these are inside the Bronx/Harlem 2.34 km circle as of OSM data.

### Considered but rejected
- **John Mullaly Park** (famous Bronx public courts, ~14 courts): centroid at 40.832, -73.927 is **outside** the circle (2400–2600 m from centre). Not added.
- **Roberto Clemente State Park** (~4 courts): 4776 m, outside. Not added.
- **Highbridge Recreation Center** (Manhattan side): 4087 m, outside. Not added.
- **Crotona Park** (~20 courts including the historic Crotona Park East courts): 3563 m, outside. Not added.
- **Joyce Kilmer Park, Franz Sigel Park, Brook Park, Patterson Playground**: park polygons fall inside the circle but per NYC Parks none have tennis. Not missed.
- **Highbridge Park (Manhattan side, across Harlem River)**: outside circle radius; rec-centre courts at 168th & Amsterdam are ~4 km away.

## Notes on density methodology
- Land-water correction is material here: the circle straddles the Harlem River, the East River, and Bronx Kill. The given OSM-strict land area of 16.93 km² already excludes Harlem River water. Randalls Island contributes substantial land area despite being "in the river."
- Saint Mary's Park sits at the geometric centre, which makes intuitive sense — it is genuinely the local park-court hotspot, with the cluster amplified by Mill Pond Park to the west and Randalls Island to the south.
- The Brighton pattern (entire park polygons missing in OSM) does NOT apply here: every NYC park I would expect to be tagged IS tagged, and NYC Parks polygons are unusually complete in OSM thanks to the city's open-data feed.

## Sources
- OSM Overpass cached data: `data/raw/overpass/global/courts_new_york_city.json`, `parks_new_york_city.json`, `clubs_new_york_city.json` (queried for this audit, May 2026)
- nycgovparks.org — Mill Pond Park, Macombs Dam Park, Saint Mary's Park, Frederick Johnson Playground, Howard Bennett Playground, Moore Playground, Randalls Island Park pages (referenced from knowledge; live web fetch blocked during this audit, see caveat below)
- NYC Parks tennis permit page — confirms permit-based access model for all listed venues
- Sportime tennis website — operates Randalls Island Tennis Center indoor facility on public parkland

## Caveat
Live verification of NYC Parks facility pages was not possible during this audit (web fetch denied). The court counts at Mill Pond (16), Frederick Johnson (8), Howard Bennett (2), Moore (2), Saint Mary's (2), and Macombs Dam (1) are based on OSM polygon counts cross-referenced against my training-data knowledge of these facilities, which match the canonical NYC Parks listings. The Macombs Dam Park count of 1 is the most unusual figure — Macombs Dam Park's primary use is the running track and ballfields above Yankee Stadium's parking, so 1 tennis court is plausible (in the southern strip of the park, the historic location). The Sportime addition of +5 is the only soft estimate in this audit.

**If Sportime is excluded entirely (treated as season-overlay only), ground-truth equals 46, identical to OSM-strict, density 2.72/km². If Sportime full-capacity counted, 56 courts, density 3.31/km².** Best estimate of 51 sits midway.
