# Ground-truth audit: Boston

**Step-4 densest 2.34 km circle centre**: 42.36992, -71.12946 (Charles River Reservation, Allston, sitting on the Boston/Cambridge boundary)
**OSM-strict count**: 18 public-park courts
**Ground-truth count (Boston-only scope)**: 18 courts
**Ground-truth count (including Cambridge side)**: 18 courts — see methodological note. No additional public-park tennis on the Cambridge bank within the disc was identified; the visible neighbouring courts on the Cambridge / HBS side belong to Harvard.
**Confidence**: medium (high on the 18 Daly Field courts via OSM operator tags from MassGIS; medium on the absence of further public-park courts because WebSearch/WebFetch were unavailable in this run)
**Density implication**: 18 / 5.01 = 3.59 per km² of in-Boston land. If the in-circle Cambridge land were included as well (≈70% of the disc, ~12 km², per the problem statement), the effective density drops to roughly 1.05 / km² of total disc land. The Boston-only land basis is the comparable figure since Cambridge OSM was not fetched.

## OSM-strict breakdown (inside circle, public_park=1)
| Venue | OSM courts | Operator | Notes |
|---|---|---|---|
| Daly Field tennis complex, Charles River Reservation (Allston) | 18 | Massachusetts DCR (Department of Conservation & Recreation) | All 18 are inside relation/17152813 `leisure=park name="Charles River Reservation" access=yes operator="Massachusetts Department of Conservation and Recreation" ownership=state source=MassGIS OpenSpace`. Way IDs 722644397–722644414, all `sport=tennis surface=asphalt`; 8 of 18 are lit. The 18 sit in two contiguous batteries on Soldiers Field Road just east of North Beacon St, ~0–150 m from the circle centre. Free drop-in use is standard for DCR public-park tennis. No padel conversion is recorded in OSM. |

## Corrections

### Add (missed by OSM tagging or scope)
- None identified with confidence in this audit.
  - The Boston-scoped Overpass extract shows zero additional tennis pitches inside the disc whose containing polygon is missing a `leisure=park` tag (i.e. no obvious Brighton-style omission).
  - On the Cambridge side of the river, the cached parks/courts dataset is Boston-only, so any DCR or City-of-Cambridge public courts on the Cambridge bank are invisible to this audit. The Cambridge bank within 2.34 km of (42.36992, -71.12946) is overwhelmingly Harvard land (Soldiers Field complex, Business School, Beren Tennis Center, Murr Center, Palmer Dixon, Henderson Boathouse) plus the Memorial Drive / Charles River Reservation strip, where the only mapped tennis on that bank in the cache lies inside Harvard institutional polygons (see "Remove" notes). No municipal Cambridge park-tennis venues are known within this radius — Riverside Press Park, Cambridge Common, and Danehy Park all sit well outside the 2.34 km disc.

### Remove (in OSM-strict but not actually on-the-day public)
- None. All 18 OSM-strict pitches are at a DCR-operated public reservation (Daly Field) and are public drop-in. No removals.

### Excluded by design (in-circle but NOT public-park, correctly excluded)
For transparency, 9 additional tennis pitches sit inside the 2.34 km disc but outside any `leisure=park` polygon. All were correctly excluded by the strict filter; all are also excluded under the project ethos because none are on-the-day bookable by the general public:
- **Harvard Business School outdoor courts (4 courts)** — ways 1358169548–1358169551 at ~(42.366, -71.124), 55 m from Shad Hall (Harvard HBS fitness centre) and 182 m from the Murr Center (Harvard varsity tennis/squash). Harvard institutional, not public-on-demand.
- **Harvard Soldiers Field tennis (3 artificial-turf courts)** — ways 619598470–619598472 at ~(42.354, -71.120), adjacent to "Boston University Track & Tennis Center" (OSM-named) but physically on Harvard Soldiers Field. Athletics-only.
- **Boston-side private/institutional clay (2 courts)** — ways 101674275, 101674277 at ~(42.351, -71.139) in Brighton, adjacent to a polygon tagged `leisure=park access=private`. Private.

## Sources consulted
- `data/raw/overpass/global/courts_boston.json` (27 in-circle tennis pitches)
- `data/raw/overpass/global/parks_boston.json` — relation/17152813 carries `name="Charles River Reservation" operator="Massachusetts Department of Conservation and Recreation" ownership=state access=yes website=https://www.mass.gov/locations/charles-river-reservation wikidata=Q1065919`, sourced from MassGIS OpenSpace — this is itself an authoritative ingest.
- `data/raw/overpass/global/clubs_boston.json` (Murr Center, Palmer Dixon Indoor, Shad Hall, BU Track & Tennis Center, etc.)
- WebSearch and WebFetch were unavailable in this run; the DCR operator attribution above rests on the MassGIS-sourced OSM tags rather than a fresh fetch of mass.gov/locations/daly-field-state-recreation-area.

## Methodological note
The 2.34 km circle straddles the Boston/Cambridge municipal boundary at the Charles River Reservation, with the problem statement noting that ~70% of the disc lies in Cambridge. The Overpass extracts for this audit were scoped to the Boston admin relation (id 2315704), so any Cambridge-side public-park courts are invisible to this audit. Two mitigating facts: (1) the Charles River Reservation itself is a single contiguous DCR-operated public park that spans both banks, and the 18 Daly Field courts sit on the Boston (Allston) bank; (2) the Cambridge bank within 2.34 km of the centre is dominated by Harvard's Soldiers Field complex (institutional, not public), with Cambridge municipal parks (Riverside Press Park, Cambridge Common, Danehy Park) all sitting outside the disc. Were the dataset re-scoped to also cover Cambridge OSM, the most likely additions would be tennis-tagged pitches that are nevertheless Harvard-owned and therefore still ineligible under the ethos. For inter-city comparability, the Boston-only land area (5.01 km² of the 17.16 km² disc) and the Boston-only court count (18) should be used together; switching either side of that ratio without switching the other distorts the density.
