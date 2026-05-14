# Ground-truth audit: San Francisco

**Step-4 densest 2.34 km circle centre**: 37.73650, -122.46444 (south-west SF — Lakeshore / St. Francis Wood / Stern Grove area)
**OSM-strict count**: 20 public-park courts
**Ground-truth count**: 27 courts (low estimate 27; high estimate 33 including SFUSD school courts)
**Confidence**: medium-high
**Density implication**: 27 / 17.09 = 1.58 per km^2 LAND

## OSM-strict breakdown

The 20 courts that pass the OSM-strict filter (court centroid inside `leisure=park` AND outside any `leisure=sports_centre`/club polygon) cluster into 13 named public-park venues, plus one HOA park at the dead centre of the circle that was mis-classified as public.

| Venue | OSM courts | Operator | Bookable on day? |
|---|---|---|---|
| Terrace Green Park (St. Francis Wood) | 2 | St. Francis Wood Homes Association (private HOA) | **No — private** |
| West Portal Playground | 1 | SFRPD | Yes — free walk-up |
| Aptos Playground | 1 | SFRPD | Yes — free walk-up |
| Larsen Park (Carl Larsen) | 1 | SFRPD | Yes — free walk-up |
| Sigmund Stern Recreation Grove | 2 | SFRPD | Yes — free walk-up |
| Miraloma Playground | 1 | SFRPD | Yes — free walk-up |
| Junipero Serra Playground | 1 | SFRPD | Yes — free walk-up |
| Sunnyside Playground | 1 | SFRPD | Yes — free walk-up |
| Golden Gate Heights Park | 2 | SFRPD | Yes — free walk-up |
| J.P. Murphy Playground | 3 | SFRPD | Yes — free walk-up |
| Glen Canyon Park | 2 | SFRPD | Yes — free walk-up |
| Merced Heights Playground | 2 | SFRPD | Yes — free walk-up |
| George Christopher Playground | 1 | SFRPD | Yes — free walk-up |
| **OSM-strict total** | **20** | | |

## Corrections

### Remove (false positive — wrongly counted by OSM-strict)

- **Terrace Green Park** — 2 courts (ways 48435278, 48435280) at the dead centre of the circle (37.73650, -122.46444). The OSM polygon (way 48435281) is tagged `leisure=park` but also `access=private` with `website=stfranciswood.org`. This is the private St. Francis Wood Homes Association tennis court — not bookable by the public. **-2**

### Add (missed by OSM-strict — courts sit inside SFRPD parks but were wrapped by an unnamed `leisure=sports_centre` polygon, so the strict filter excluded them)

- **McCoppin Square** — 1 court (way 392027113) at 37.74323, -122.48048. Sits inside `leisure=park` McCoppin Square (way 16750270) but also inside an unnamed `leisure=sports_centre` shell (way 1164832022). SFRPD public, free walk-up. **+1**
- **Parkside Square (Parkside Playground)** — 4 courts (ways 1093131047, 1093131048, 1093131049, 28693835) at 37.73825, -122.48347. Inside `leisure=park` Parkside Square (way 103637793), wrapped by `leisure=sports_centre` way 1164828546 (courts=4). SFRPD public. **+4**
- **Balboa Park (Ocean Avenue)** — 4 courts (ways 1107950985, 1107950986, 1107950987, 1107950988) at 37.72547, -122.44332. Inside `leisure=park` Balboa Park (way 24562831), wrapped by `leisure=sports_centre` way 48442605. SFRPD public, free walk-up. **+4**

Net correction: **-2 + 9 = +7**, giving **27** ground-truth public-park courts.

### Hold (in-circle but excluded — correctly not public)

- **San Francisco State University courts** (~24 courts in two clusters):
  - 10 courts at 37.729, -122.484 (ways 1164832980-89, `leisure=sports_centre` way 86124627), about 350 m north of the SFSU Mashouf Wellness Center polygon (way 634526276).
  - 14 courts at 37.726, -122.483 (ways 1164837248-61, `leisure=sports_centre` way 28694495), adjacent to the same complex.
  - These are SFSU intramural / Cox Stadium / Mashouf tennis facilities. Access is limited to SFSU students, faculty, and Mashouf members; not in the SFRPD on-the-day drop-in system. Correctly excluded.
- **Mercy High School / Stonestown private courts** — 3 courts at 37.729, -122.473 (ways 1164843190, 1164843191, 1164843192). Private Catholic school courts, not bookable on the day. Correctly excluded.
- **Lincoln High School (SFUSD) tennis** — 6 courts at 37.747, -122.480 (ways 865527407-12). Public high school courts adjacent to the West Sunset Playground complex but inside the Abraham Lincoln HS footprint. SFUSD school courts are not on the SFRPD reservation system; public access is restricted during school hours and not bookable on the day. Conservatively excluded. (Would add **+6** under a generous "publicly accessible after school" reading → high estimate 33.)
- **CCSF / Phelan-Ocean school cluster** — 8 courts at 37.726, -122.447 (ways 1107950325-32, sports_centre 28953033). Most likely City College of San Francisco / Riordan / Balboa HS school courts. Not in the SFRPD drop-in system. Correctly excluded.

### Padel conversions
- None detected in the OSM data for the public-park venues in this circle. SF padel build-out is recent and concentrated in private clubs / Mission Bay / Presidio, none of which fall inside this south-west circle.

## Members-only exclusions verified

The well-known SF members-only tennis clubs all lie outside this circle:
- **The Olympic Club Lakeside** (15+ courts) — at 37.711, -122.495, more than 3.0 km from centre, outside the radius.
- **Lake Merced Country Club / Lakeside CC** — out of radius to the south.
- **Olympic Club Lakeside Tennis** — out of radius.
- **Goldman Tennis Center** (way 25309187 — Golden Gate Park) — SFRPD-operated but at 37.770, -122.459, ~3.75 km from centre, outside the radius.

No members-only club polygon is inside the 2.34 km radius.

## Sources

- OSM Overpass cached extracts: `data/raw/overpass/global/{courts,parks,clubs,boundary,water}_san_francisco.json` (queried 2026-05-11).
- Terrace Green private classification: OSM way 48435281 tags `access=private`, `website=https://www.stfranciswood.org/parks` (St. Francis Wood Homes Association).
- SFRPD operator confirmation on linked polygons: ways 48537425 (Junipero Serra), 86124618 (West Portal), 128241105 (Golden Gate Heights), 353551814 (J.P. Murphy), 402978882 (Larsen Park) all carry `operator=San Francisco Recreation & Park Department` and `sfrecpark.org` website tags.
- Wrapped sports_centre identification: OSM ways 1164832022 (McCoppin), 1164828546 (Parkside, `courts=4`), 48442605 (Balboa) — all bare `leisure=sports_centre sport=tennis` polygons fully contained inside a named SFRPD `leisure=park` polygon.
- SFSU exclusion anchor: way 634526276 `name=Mashouf Wellness Center` ~350 m from the two 10-court / 14-court clusters at (37.729, -122.484) and (37.726, -122.483).
- Goldman Tennis Center reference: OSM way 25309187 `name=Lisa and Douglas Goldman Tennis Center`, `website=sfrecpark.org/...Goldman-Tennis-Center-420` — confirmed SFRPD operator but outside the circle.
