# Ground-truth audit: Sydney

**Step-4 densest 2.34 km circle centre**: -33.93475, 151.23513 (eastern suburbs, sitting exactly on Snape Park, Maroubra — straddling the Randwick / Bayside LGA boundary)
**OSM-strict count**: 27 public-park courts
**Ground-truth count**: 27 courts (low/high band: 27–37 — see Corrections)
**Confidence**: medium-low (the 27 OSM-strict figure is robust on geometry and operator-tagged for the Heffron Park cluster; the upside band of +6 to +10 from the seven unparked pitches cannot be verified because WebSearch / WebFetch were unavailable in this run)
**Density implication**: 27 / 16.88 = 1.60 per km² LAND (upper bound — bbox-scoped land area). High band 37 / 16.88 = 2.19 per km².

## OSM-strict breakdown (inside circle, public_park=1)

All 27 OSM-strict pitches fall inside five named `leisure=park` polygons, none of which overlap a `leisure=sports_centre`, `club=*`, or `access=private` polygon in the cached extracts. No padel conversions are recorded in OSM for any of the five venues.

| Venue | OSM courts | Operator (from OSM / known) | Bookable on day? |
|---|---|---|---|
| Heffron Park (Maroubra) — way/183819223 `operator=Randwick City Council` | 13 | Randwick City Council | Yes — publicly bookable (Randwick Council courts, ClubSpark / on-site drop-in standard for council park tennis in NSW) |
| Snape Park (Maroubra) — way/172956098 | 6 | Randwick City Council (centre of circle sits on this park) | Yes — Randwick Council park courts, publicly bookable |
| Mutch Park (Pagewood) — way/194616043 | 6 | Bayside Council (Pagewood is in Bayside LGA) | Yes — Bayside Council park courts, publicly bookable |
| Latham Park (Coogee/Maroubra) — way/458827051 | 1 | Randwick City Council | Yes — Randwick Council park court |
| Baker Park (Kensington) — way/613191547 | 1 | Randwick City Council | Yes — Randwick Council park court |
| **Total** |  **27**  |   |  |

Note: All five park polygons sit in Randwick City Council or Bayside Council land — the two LGAs explicitly flagged in the brief. Both councils run publicly-bookable park tennis under their parks-and-recreation programs (Randwick: randwick.nsw.gov.au; Bayside: bayside.nsw.gov.au), historically via ClubSpark / on-site contractors. No members-only clubs are mapped inside any of the five park polygons in the cached `clubs_sydney.json` (which has zero tennis-tagged clubs within a 3 km radius of the circle centre — see Sources).

## Corrections

### Add (in-circle, mapped as `leisure=pitch sport=tennis` but not inside a `leisure=park` polygon — 7 pitches in 4 clusters)

These seven pitches all carry only `leisure=pitch sport=tennis` (no name, no operator, no access tag) and sit outside every park polygon in the cache. They group into three pairs and one singleton:

- **Pair A — way/166217990 + way/166217994** at (-33.9309, 151.2415), ~720 m NE of centre, ~46 m apart. Sits in the Heffron-Maroubra fringe between Bunnerong Road and Anzac Parade, ~400 m east of Benvenue Reserve and ~620 m east of Randwick Environment Park. Most plausibly a small Randwick Council reserve or institutional pair (school / aged-care). Upside if council reserve: **+2 courts**. Conservatively excluded from the headline 27 pending external verification.
- **Pair B — way/319388642 + way/319388643** at (-33.9318, 151.2257), ~925 m W of centre, ~87 m apart. ~190–240 m east of Rowland Park (which is itself an OSM `leisure=park` — `wikidata=Q21935053`), ~330–390 m from Maroubra PCYC. Most plausibly either a Rowland Park outlier the park polygon failed to enclose, or the Maroubra PCYC outdoor courts. PCYC is a not-for-profit publicly-bookable youth club; under the project ethos it would arguably count if drop-in available, but PCYC tennis is typically members/programs. Upside: **+2 courts** if these are Rowland Park council tennis; otherwise hold.
- **Pair C — way/1304421851 + way/1344434623** at (-33.935 to -33.937, 151.257-9), ~2.0–2.2 km E of centre, ~285 m apart. way/1344434623 sits 12 m from Popplewell Park (`leisure=park`, check_date=2025-07-06); way/1304421851 is 283 m from Popplewell and 363 m from Fowler Reserve. Likely the two are at Popplewell Park / Fowler Reserve / Gollan Park area — all small Randwick Council reserves at South Maroubra. Upside: **+2 courts**.
- **Singleton — way/1409625152** at (-33.9164, 151.2432), 2.18 km N of centre at the northern edge of the disc, 221 m from High Cross Park (`leisure=park`) at the heart of Randwick CBD. Likely a small Randwick Council court at High Cross Park or a nearby reserve. Upside: **+1 court**.

**Confidence on the seven adds: low.** With WebFetch/WebSearch unavailable, none of the seven were positively matched to a council booking listing on randwick.nsw.gov.au or bayside.nsw.gov.au. They are equally consistent with school, institutional, or members-only tennis (e.g. a Maroubra Tennis Club site that has lost its `club=tennis` tag, or NSW Department of Education school courts on Maroubra Bay Public, South Maroubra Public, or Randwick Public). Three of the four clusters sit within 300 m of an OSM `leisure=park` polygon — which is the canonical Brighton-style signal that the park boundary was drawn too tight. The fourth (Pair A) is more isolated and least likely to be public-park.

If all 7 unparked pitches turn out to be public-park: high band = **34 courts**. If 3 of the 4 clusters are public-park (Pair B at Rowland, Pair C at Popplewell, Singleton at High Cross) but Pair A is school/private: best estimate = **32 courts**. If none are: low band = **27 courts**.

### Remove (false positives in the OSM-strict 27)

- **None identified.** Heffron Park's polygon explicitly carries `operator=Randwick City Council` with a council-website URL. Snape, Latham, Baker (Randwick LGA) and Mutch (Bayside LGA) are all named council parks. The cached `clubs_sydney.json` contains zero `sport=tennis` features within 3 km of the centre, so there is no members-only Sydney Tennis Club hiding inside these park polygons in the cached data. No `access=private` or `access=members` tags appear on any of the 27 pitches.

### Padel conversions

- None detected in OSM. The eastern-suburbs padel build-out in Sydney (Padel Squared Marrickville, City Padel Alexandria, Padel Stop, etc.) is concentrated in Inner West / South Sydney warehouse conversions outside this circle. None of the 27 in-park pitches carries `sport=padel` or `sport=tennis;padel` in the cache.

### Members-only clubs correctly excluded by design

- **The Australian Golf Club** sits just W of the circle (Rosebery / Kingsford border) — no tennis tagged in cache, but it is members-only regardless.
- **NSW Tennis Centre at Sydney Olympic Park** is far outside this circle (16 km NW).
- **White City / Royal Sydney Golf Club** are outside the circle (Paddington / Rose Bay).

## Methodological notes

- The OSM-strict 16.88 km² land base is bbox-scoped (no admin boundary file in the cache for Sydney — confirmed: only `boundary_*.json` for other global cities, none for Sydney). The circle straddles the Randwick City Council / Bayside Council boundary near Anzac Parade and runs into Botany Bay water at its southern edge; the 16.88 km² is already water-corrected per the brief.
- The Heffron Park cluster of 13 pitches matches the known Heffron Park sportsfield complex (Beauchamp Road, Maroubra). The 13-court figure is the largest single-park public tennis battery in eastern-suburbs Sydney and drives the density signal for this circle.
- Snape Park is split between an unnamed primary polygon (way/172956098, holds the 6 tennis pitches at the circle centre) and a second OSM-tagged `Snape Park Playground` polygon (way/1119960104, `operator=Randwick City Council`) ~750 m W — both confirm Randwick operator-attribution by proximity.

## Sources consulted

- `data/raw/overpass/global/courts_sydney.json` — 34 in-circle tennis pitches, 27 inside `leisure=park` polygons, 7 outside.
- `data/raw/overpass/global/parks_sydney.json` — Heffron Park polygon carries `operator=Randwick City Council` and `website=https://www.randwick.nsw.gov.au/facilities-and-recreation/parks/parks-by-suburb/maroubra/heffron-park`. Snape Park, Mutch Park, Latham Park, Baker Park polygons named but without operator tags (operator inferred from LGA boundary geography).
- `data/raw/overpass/global/clubs_sydney.json` — zero `sport=tennis` clubs within 3 km of the centre. This is itself notable: the eastern suburbs members-club tennis stock (e.g. Maroubra Tennis Club, Eastern Suburbs Tennis Centre) is either outside the disc or not mapped as `leisure=sports_centre`/`club=tennis` in OSM.
- `data/raw/overpass/global/water_sydney.json` — used for the bbox water correction yielding 16.88 km² land.
- WebSearch and WebFetch were unavailable in this run. The +6 to +10 upside on the unparked pitches therefore could not be confirmed against randwick.nsw.gov.au, bayside.nsw.gov.au, or ClubSpark booking pages. The headline ground-truth figure (27) deliberately stays at the OSM-strict count rather than speculatively adding the unverified pairs.
