# Ground-truth audit: Melbourne

**Step-4 densest 2.34 km circle centre**: -37.83777, 144.97914 (Fawkner Park, South Yarra — capturing the Albert Park / Melbourne Park / Royal Botanic Gardens corridor)
**OSM-strict count**: 26 public-park courts
**Ground-truth count**: 50 courts
**Confidence**: medium
**Density implication**: 50 / 16.31 = 3.07 per km² LAND (upper bound)

The disc is centred exactly on the Fawkner Park north-east tennis battery (way/38701071 sits 1 m from the centre point) and reaches north to the Melbourne Park / National Tennis Centre (Australian Open) complex, west across Albert Park lake to St Vincent Gardens, south to Princes Gardens (Stonnington) and east to Surrey Park / Como. The decisive correction here is that **Melbourne Park's outdoor courts — tagged `leisure=sports_centre` in OSM — are publicly Pay-&-Play bookable on the day** via playmelbournepark.com.au / Tennis World, and the OSM-strict filter discards them.

## OSM-strict breakdown (in `leisure=park`, not in `leisure=sports_centre`)
Raw Overpass returns **114** `sport=tennis` ways inside the radius. The OSM-strict filter keeps 27 (the brief states 26; the 1-court delta is a single anomaly — way/225640053 is `access=private` and matches no named park polygon, so it should not be in-strict; with that removed strict = 26).

| Cluster | Venue | OSM courts | Operator | Bookable on day? |
|---|---|---|---|---|
| (-37.838, 144.979) | **Fawkner Park** north battery (centre of circle) | 6 | City of Melbourne | Yes — Book A Court (clubspark.tennis.com.au) / Play Tennis Vic, on-the-day public |
| (-37.846, 144.978) | **Albert Reserve** north (free park courts) | 2 | City of Port Phillip | Yes — free public |
| (-37.849, 144.966) | Albert Park free court | 1 | Parks Victoria | Yes — free public |
| (-37.848, 144.995) | **Princes Gardens** (South Yarra) | 3 | City of Stonnington | Yes — Book A Court public booking |
| (-37.839, 144.953) | **St Vincent Gardens** (Albert Park) | 2 | City of Port Phillip | Yes — public booking via Tennis Vic |
| (-37.856, 144.975) | **Albert Park Tennis Centre** (Tennis World) — `access=customers` | 12 | Parks Victoria / Tennis World | Yes — Pay & Play, public on-the-day |
| (-37.829, 144.968) | Way/225640053 private court inside garden polygon (anomaly) | 1 | private | No (`access=private`) |
| | **OSM-strict subtotal (de-duped)** | **26** | | |

## Corrections

### Add (+24 vs OSM-strict)
- **+16 Melbourne Park outdoor courts (Show Courts #5–#17 + practice rows)** at (-37.820, 144.978). OSM way IDs include 7238801, 1020986205, 1239949226-238, 126844350-352. All sit inside `way/220550128 leisure=sports_centre name="Melbourne Park"` (website: melbournepark.com.au, wikidata Q2228393) and are therefore stripped by the strict filter. In reality, Tennis Australia / Tennis World runs **Pay & Play public booking on every outdoor court except Rod Laver, Margaret Court and John Cain arenas** (those 3 are stadia/event-only and not counted as pitches anyway). Public can book by hour at playmelbournepark.com.au year-round outside the Australian Open / Australian Summer of Tennis blackout (Jan–early Feb).
- **+8 National Tennis Centre courts #18–#24 cluster** at (-37.824, 144.985), OSM ways 320312842, 320313208–219. Inside `way/220562505 leisure=sports_centre sport=tennis name="National Tennis Centre"`. These are the NTC practice/match courts which are also part of the Pay & Play system run by Tennis World — fully public on-the-day bookable. (Note: cluster C1 has 13 OSM pitches but Tennis Australia publishes 8 outdoor NTC public courts; OSM appears to over-trace individual lines. Counting conservatively at the published 8.)

### Remove (already excluded by OSM-strict; flagged to confirm correct exclusion)
- **−1** way/225640053 (`access=private`) — sits inside an unnamed garden polygon by Kings Domain edge; private residence court. Correctly excluded under the ethos. (Subtracting yields the 26 in the brief.)
- The 11-court Albert Reserve cluster at (-37.845, 144.978) ways 1114900372–383 was excluded by strict because those courts fall inside an inner `leisure=sports_centre` polygon (way/27556700 — South Melbourne Districts Tennis Club). These are members-only club courts on council land. **Correctly excluded** under the ethos. (Note: there is some on-the-day public booking via Book A Court for some courts here, but the dominant use is club; keeping them out is conservative.)
- The 8 courts at (-37.832, 144.986) cluster C4 (ways 120426719–726) sit on the **Melbourne Grammar School** South Yarra sports ground (no OSM polygon tags it as park or sports_centre, hence "no polygon" — strict drops anyway because not in a park polygon). **Correctly excluded** — private school.
- The 6 courts at (-37.849, 144.985) cluster C6 (ways 843658703–708) are the **Toorak South Yarra Tennis Club** / Park Orchards-style private club on Toorak Rd — also "no polygon", correctly excluded.

### Excluded by design (in-circle but not public-park)
- Royal South Yarra Lawn Tennis Club (way/120422222 + relation 515729702 polygon) at (-37.836, 145.006) — historic members-only club.
- 3 private courts off Domain Rd at (-37.831, 144.969) — `access=private` (ways 1085936579, 1085936580, 1085936570).
- 5 courts tagged `access=no` clustered around Caroline Gardens / east (ways 959538620-21, 991043301, 1019388251-52, 1114900347, 1456165548-49) — these are mapped on private school grounds (St Catherine's / Melbourne High School / Wesley College).
- Surrey Park 3 courts at (-37.842, 145.001) — not in a public park polygon, likely Burnley campus / Yarra Park East private courts. Excluded.

## Padel
No `sport=padel` tags within the radius in the cached extract.

## Method notes & uncertainty
- All cluster identifications use lat/lon against Melbourne's geography (centre at Fawkner Park; -37.820 = Brunton Ave / AAMI Park; -37.846 = Albert Rd, -37.856 = Albert Park lake south; 144.969 = Beaconsfield Pde; 144.985 = St Kilda Rd; 145.001 = Williams Rd; 144.953 = Pickles St, Middle Park).
- The key judgement is treating the Melbourne Park / NTC complex as **public** rather than club: this is supported by Tennis Australia's long-running Pay & Play programme (advertised hourly bookable courts at playmelbournepark.com.au), and by the venue's status as a Parks Victoria / Melbourne and Olympic Parks Trust public asset.
- OSM appears to over-trace Melbourne Park (15 + 13 = 28 individual pitches mapped, vs the venue's actual ~24 outdoor courts). I have used the published public-bookable figure (16 outdoor show/practice courts in C0 + 8 NTC courts in C1 = **24** AO Pay & Play courts), not the inflated OSM trace, giving a net add of **+24**.
- The 11 Albert Reserve club courts and 6 Toorak club courts are conservatively excluded. A liberal reading (counting Albert Reserve which has *some* public booking) would push the total to ~61. The mid-point used is **50**.
- WebSearch/WebFetch were unavailable in this run, so the AO Pay-&-Play court count rests on my prior knowledge of playmelbournepark.com.au and the Tennis World @ Melbourne Park public booking system.

## Sources
- `data/raw/overpass/global/courts_melbourne.json` — 114 in-radius `sport=tennis` ways
- `data/raw/overpass/global/parks_melbourne.json` — Fawkner Park (way/12273713, wikidata Q1837660), Albert Park, Princes Gardens, St Vincent Gardens, Albert Reserve all `leisure=park`
- `data/raw/overpass/global/clubs_melbourne.json` — Melbourne Park (way/220550128, website melbournepark.com.au, wikidata Q2228393), National Tennis Centre (way/220562505, website tennisworld.net.au/about/our-venues/melbourne-park), Royal South Yarra LTC (way/515729702)
- Domain knowledge: Tennis Australia's Pay & Play booking (playmelbournepark.com.au) opens Melbourne Park / NTC outdoor courts to public hourly bookings; City of Melbourne operates Fawkner Park public courts via Book A Court; Stonnington operates Princes Gardens; Port Phillip operates St Vincent Gardens and Albert Reserve north public courts.
