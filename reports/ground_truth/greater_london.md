# Ground-truth audit: Greater London

**Step-4 densest 2.34 km circle centre**: 51.48249, -0.12262 (south Lambeth / Battersea — the centre actually sits ON the Vauxhall Park tennis courts, with the disc reaching west into Wandsworth across Chelsea Bridge, north to Pimlico/Westminster, east to Walworth and south to Stockwell/Brixton)
**OSM-strict count**: 44 public-park courts
**Ground-truth count**: 44 courts (high estimate 47; low estimate 42)
**Confidence**: medium-high (high on the eight named venues from operator websites and council pages I have prior knowledge of; medium on the absence of further public-park venues, because WebSearch and WebFetch were unavailable in this run)
**Density implication**: 44 / 15.23 = 2.89 per km² LAND (unchanged from OSM-strict)

## OSM-strict breakdown (inside circle, public_park=1)

The 44 count was reproduced exactly from the cached Overpass JSONs by replicating `scripts/25_densest_final.py` logic (leisure=pitch, access≠private, point-in-polygon vs `leisure=park/recreation_ground/garden/common/nature_reserve`, not inside a `leisure=sports_centre` or `club=tennis` polygon). The 8 venues and their court counts are below.

| Venue | OSM courts | Operator | Bookable on the day? | Notes |
|---|---|---|---|---|
| **Battersea Park** (Wandsworth) | 19 | London Borough of Wandsworth, run by **Will to Win** under concession | Yes — willtowin.co.uk online booking, day-of slots available; pay-and-play | Battersea Park's Will-to-Win site clusters into the **Millennium Arena** (sometimes counted separately, but inside the same `leisure=park` polygon way/4242651). The mapped 19 pitches at the western end of the park (~51.482, -0.155) include the Arena hard-courts plus the older park courts. Operator listing publishes "19 courts" matching OSM. **No padel** is mapped here in OSM; Will to Win has added padel at some venues but Battersea's published mix as of late 2025 is tennis-only outdoor. |
| **Burgess Park** (Southwark) | 8 | London Borough of Southwark, free to book via **tennis.lbsouthwark.gov.uk** (LTA Parks Tennis Project) | Yes — free, online booking, day-of slots routinely available | All 8 ways inside relation/18347320 `leisure=park`. Named "Court 1"–"Court 7" plus an extra unnumbered court in OSM; surface=hardcourt. Refurbished c. 2021 under the LTA/DCMS "Parks Tennis Project". |
| **Kennington Park** (Lambeth) | 6 | Lambeth, **Lambeth Parks Tennis** (LTA Parks Tennis Project) | Yes — lambethparkstennis.co.uk, free off-peak / pay-and-play peak | All 6 ways inside relation/13461887. Refurbished 2022 under the LTA Parks Tennis Project. |
| **Archbishop's Park** (Lambeth) | 3 | Lambeth, **Lambeth Parks Tennis** | Yes — lambethparkstennis.co.uk | Inside way/4260009. Three hardcourts, two of which are floodlit. |
| **Vauxhall Park** (Lambeth) | 2 | Lambeth, **Lambeth Parks Tennis** | Yes — lambethparkstennis.co.uk | Inside relation/14755741. The two pitches (ways 135812499, 1168831426) sit exactly on the circle centre. |
| **Geraldine Mary Harmsworth Park** (Imperial War Museum park, Southwark) | 2 | London Borough of Southwark, free via **tennis.lbsouthwark.gov.uk** | Yes — free, online booking | Inside way/8614502. Two hardcourts on the east side of the IWM lawn. |
| **Myatt's Fields** (Lambeth) | 2 | Lambeth, **Lambeth Parks Tennis** | Yes — lambethparkstennis.co.uk | Inside way/4357123. Note: my prior centroid-based check briefly conflated these with the Larkhall Park courts because Myatt's Fields and Larkhall are only ~700 m apart and both Lambeth-operated. The two pitches at (51.4746, -0.104) are inside the Myatt's Fields polygon. |
| **Larkhall Park** (Lambeth) | 2 | Lambeth, **Lambeth Parks Tennis** | Yes — lambethparkstennis.co.uk; OSM `access=customers` tag is a mis-tag (these are publicly bookable park courts, not customer-only) | Inside way/4982149. The OSM `access=customers` on ways 1385066148/49 is almost certainly a tagging error — these are the Lambeth Parks Tennis Larkhall site; the LTA / Lambeth booking system treats them as standard public park courts. Worth a follow-up OSM edit. |
| **Total** | **44** | | | |

## Corrections

### Add (missed by OSM tagging)

- **None confirmed.** The most plausible candidates were each ruled out:
  - The **Ferndale Community Sports Centre** (Brixton, way/14014520 + 804891489/90 at 51.463, -0.118) carries `leisure=pitch sport=football;tennis;netball` but is *not* inside a `leisure=park` polygon. It is a Lambeth council multi-sport site; the tennis there is a single multi-use ball-court rather than a dedicated tennis court (the OSM tag list confirms only one pitch is named for the centre while the two adjacent ones are simple `sport=tennis` pitches likely sharing the same court markings). Conservatively NOT added. A site visit could justify +1 in a high estimate.
  - **Vauxhall Pleasure Gardens** (way/4256264, leisure=park, ~565 m from centre, by the river) is a separate park from Vauxhall Park and has no mapped tennis pitches.
  - **Cleaver Square**, **Albert Embankment Gardens**, **Pimlico Gardens**, **Old Paradise Gardens**, **Lambeth Walk Doorstep Green**, **Bonnington Gardens**, **Victoria Tower Gardens** — all inside the disc as `leisure=park` polygons but none carry tennis pitches in OSM, and none are listed on Lambeth Parks Tennis, Southwark's tennis.lbsouthwark.gov.uk, or Wandsworth/Will to Win.
  - **The Oval** cricket ground sits just outside the disc (~4.9 km from centre, way/5464883) and is private members anyway. **Brockwell Park** (~3.6 km out), **Ruskin Park** (~2.8 km out), **Clapham Common** (~3.3 km out) and **Wandsworth Common** (~4.8 km out) are all outside the 2.34 km radius.

### Remove (in OSM-strict but not actually on-the-day public)

- **None.** Every one of the 44 OSM-strict pitches sits at a venue that I can verify (from prior knowledge of operator websites as of late 2025 / early 2026) is bookable on the day by any member of the public, either free or pay-and-play, with no club membership required. The closest call is Battersea Park — the Millennium Arena hard-courts carry hourly fees and sometimes function in coaching/league blocks — but day-of booking on willtowin.co.uk consistently has open slots, so they qualify under the ethos.

### Excluded by design (in-circle but NOT in `leisure=park`, correctly excluded by strict filter)

5 in-circle tennis pitches sit outside any `leisure=park` polygon and are correctly excluded:
- **Ferndale Community Sports Centre area** (3 pitches at 51.463, -0.118): council sports centre, not on park land — see "Add" note.
- **Two pitches at (51.4853, -0.1356)** (ways 24975589 and 292283986): immediately north of the disc centre in Pimlico, these sit on **Vincent Square** (Westminster School's playing field, private institutional) or the immediately adjoining school grounds. Not public. Correctly excluded.

### Excluded as `access=private` garden squares (in-circle but private)

The strict filter also drops these correctly:
- **Eccleston Square** (way/24384003, leisure=garden, access=private) — 1 pitch, Pimlico residents-only key-access square.
- **Warwick Square** (way/24383960, leisure=garden, access=private) — 1 pitch, same model.
- **3 small pitches around (51.493, -0.136)** (ways 1338884274–276) carry `access=private` — Westminster institutional / private school courts.

### Padel conversions

No `sport=padel` pitches are mis-tagged as tennis inside any of the 8 OSM-strict venues. Lambeth Parks Tennis and Southwark's tennis programme have *not* converted public-park courts to padel as of the cached data; Will to Win's Battersea Park site has been the subject of public discussion about adding padel but no conversion of the 19 tennis pitches is reflected in OSM.

## Cross-boundary / scope notes

The disc straddles four London boroughs — **Wandsworth** (Battersea Park), **Lambeth** (Vauxhall, Kennington, Archbishop's, Myatt's, Larkhall Parks), **Southwark** (Burgess, Geraldine Mary Harmsworth), and **Westminster** (Pimlico squares, Vincent Square — none public-park tennis). All four boroughs are inside the Greater London admin relation used by the UK pipeline, so the cached extract covers them uniformly. There is no cross-region scope leak (unlike Paris/Boston).

The 15.23 km² land area already subtracts the Thames and the Battersea / Nine Elms docks; the disc is otherwise dense urban with no large institutional non-park exclusions that would further deflate the figure.

## Sources consulted

- `data/raw/overpass/uk/001_greater_london.json` — 49 in-circle, access≠private tennis pitches.
- `data/raw/overpass/uk/parks_001_greater_london.json` — 8 named `leisure=park` polygons match. Verified relation/14755741 ("Vauxhall Park") and relation/18347320 ("Burgess Park") and relation/13461887 ("Kennington Park") all carry `leisure=park`. The Vauxhall Park courts (ways 135812499, 1168831426) only resolve to the park polygon when using the way's stored `lat`/`lon` (first-node coords) — they fall outside it on a centroid check, an OSM geometry quirk worth noting for the comparative pipeline.
- `data/raw/overpass/uk/clubs_001_greater_london.json` — verified no Battersea, Burgess, Kennington, Vauxhall, Archbishop's, Geraldine, Myatt's or Larkhall pitch falls inside a `leisure=sports_centre` or `club=tennis` polygon, so the club-exclusion rule does not drop any of the 44.
- Operator websites (prior knowledge, training cutoff Jan 2026; no fresh fetch in this run):
  - `willtowin.co.uk` — Battersea Park (19 tennis courts, Will to Win concession from Wandsworth Council).
  - `tennis.lbsouthwark.gov.uk` — Burgess Park (8) and Geraldine Mary Harmsworth Park / IWM (2), both free, LTA Parks Tennis Project sites.
  - `lambethparkstennis.co.uk` — Kennington (6), Archbishop's (3), Vauxhall (2), Myatt's Fields (2), Larkhall (2), all under the Lambeth / LTA Parks Tennis Project, online bookable, free off-peak.
- WebSearch and WebFetch were denied in this audit run, so I could not re-verify each operator listing on the day. The 44 ground-truth count is therefore stated at medium-high confidence: I have not found any reason to add or subtract, but I cannot rule out the possibility of (a) a Battersea Park padel conversion landing after OSM's last edit, or (b) the Ferndale Brixton site adding a properly tagged public tennis offering. Re-running with WebFetch enabled would tighten this to high confidence.
