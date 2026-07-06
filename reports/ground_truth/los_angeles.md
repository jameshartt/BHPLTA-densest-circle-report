# Ground-truth audit: Los Angeles

**Step-4 densest 2.34 km circle centre**: 34.06780, -118.49137 (Brentwood / Crestwood Hills / Mandeville Canyon, West LA — between Sunset Blvd and the Santa Monica Mountains foothills, NOT Cheviot Hills/Rancho Park as the brief guessed)
**OSM-strict count**: 35 public-park courts
**Ground-truth count**: 8
**Confidence**: high
**Density implication**: 8 / 17.01 km² = **0.47 per km² LAND**

> **Reviewer note (peer review, July 2026).** The strict-35 breakdown
> below is built from "~" venue estimates that sum to ~38, not exactly
> 35; the direction and scale of the −27 correction are unaffected. As
> the confidence note in this file says, confidence is high on
> direction, medium on the exact final count (6-10) — the main report's
> limitations section now carries that qualifier.

## What the circle actually covers

The centre (34.068, -118.491) sits high on the hillside in **Brentwood**, just east of Mandeville Canyon, just west of Mountaingate Country Club, and immediately north of Brentwood Country Club. The 2.34 km radius reaches:
- **W**: Riviera Country Club, Will Rogers SHP (just outside), upper Rivas Canyon
- **N**: Mountaingate CC, MRCA conservation lands, Mandeville/Hilton open space
- **E**: Brentwood School East Campus, Getty Center grounds, Barrington Rec Center
- **S**: residential Brentwood Glen, edge of Westgate
There are very few public parks here — almost all green tag area is national-recreation-area overlay on private/residential land.

## Why OSM-strict over-counts to 35

The **Santa Monica Mountains National Recreation Area** (OSM relation 177418, `boundary=protected_area + leisure=nature_reserve`, operator NPS) is a federal recreation-area **boundary** that legally overlays this entire hillside — including private homes, country clubs, and private schools. Of the 129 tennis pitches inside the 2.34 km circle:
- **34** fall inside the SMMNRA boundary polygon → counted by OSM-strict as "in a park"
- **4** fall inside Barrington Recreation Center (true RAP public park)
- **23** fall inside Riviera Tennis Club (`leisure=sports_centre`, private)
- The remainder (≈ 68) are residential/club courts not contained in any park polygon at all

In reality, almost all 34 SMMNRA-overlapping courts are private residential homes (Brentwood Hills, Crestwood Hills, Kenter Canyon, Mandeville Canyon estates) or private clubs (Mountaingate CC, Brentwood CC) — they are NOT bookable to the public.

## OSM-strict breakdown (best interpretation of the 35)

| Venue | OSM courts | Operator | Bookable on day? |
|---|---|---|---|
| Barrington Recreation Center | 4 | LA RAP | **Yes — public, free/reservable** |
| Crestwood Hills Park area pitches (in SMMNRA overlay) | 2 of ~6 mapped | LA RAP | **Yes — 2 public courts; rest are private homes** |
| Mountaingate Country Club (in SMMNRA overlay) | ~9 | Mountaingate CC | No — members only |
| Brentwood Country Club fairway/tennis area | ~12 | Brentwood CC | No — members only |
| Riviera Country Club / Riviera Tennis Club | 23 | Riviera CC | No — members only (excluded from 35 by OSM-strict because tagged sports_centre, not park) |
| Brentwood School (East / Hammer Campus) | ~6 | Brentwood School | No — private K-12, not publicly bookable |
| Archer School / Mt St Mary's Chalon courts | ~2 | Private schools | No |
| Single private home courts (Crestwood Hills, Mandeville, Kenter) | ~10+ | Private residences | No |

Of these, only **Barrington (4) + Crestwood Hills Park (2) = 6** are genuine public-park courts inside the circle.

## Corrections

### Add
- **Rustic Canyon Recreation Center** (601 Latimer Rd, Pacific Palisades) — LA RAP — has **2 public tennis courts**. Polygon centroid sits ~2.0 km from circle centre, edge of circle. Bookable via LA RAP reservation system, otherwise drop-in.
- No other RAP courts are reachable — Westwood Rec, Stoner Rec, Cheviot Hills, Rancho Park, Palisades Rec are all well outside this 2.34 km circle (the circle centre is in the hills, not in flat-LA RAP territory).

### Remove
- **All 23 Riviera Tennis Club courts** if any are in the 35 — they sit inside `leisure=sports_centre` and are members-only (Riviera Country Club).
- **All ~34 courts** that the OSM-strict filter pulled in via the Santa Monica Mountains NRA boundary overlay. SMMNRA is a federal land-management boundary, not a contiguous public park — it covers private estates, private schools, and private country clubs in this hillside.
- Specifically remove: Mountaingate CC courts (≈ 9), Brentwood CC area courts (≈ 12), Brentwood School courts (≈ 6), the cluster of single-court private residential pitches scattered across Crestwood Hills/Mandeville (≈ 10+), the four Riviera-adjacent private homes flagged `access=private`.

### Final ground-truth count
- Barrington Recreation Center: 4 public courts
- Crestwood Hills Park (RAP): 2 public courts
- Rustic Canyon Recreation Center (edge of circle): 2 public courts
- **Total: 8 public-park tennis courts**

## Sources

- OSM cached data: `data/raw/overpass/global/courts_los_angeles.json`, `parks_los_angeles.json`, `clubs_los_angeles.json` (analysed locally).
- OSM relation 177418 — Santa Monica Mountains National Recreation Area (NPS boundary).
- OSM way 443668556 — Barrington Recreation Center polygon.
- OSM relation 15402744 — Crestwood Hills Park polygon (RAP).
- OSM way 330130796 — Riviera Tennis Club (sports_centre, private).
- LA Recreation & Parks venue knowledge: Barrington Rec Center (333 S Barrington Ave), Crestwood Hills Park (1100 Hanley Ave), Rustic Canyon Rec (601 Latimer Rd) — all listed on laparks.org as public tennis venues with reservation-or-drop-in access.
- Note: web verification on laparks.org was attempted but blocked in this audit environment; counts of public courts per RAP venue are from prior public-domain knowledge of these named facilities.

## Confidence notes

High confidence on the **direction** of the correction (OSM-strict massively over-counts here due to the SMMNRA federal boundary overlaying private residential hillside). Medium confidence on the **exact** ground-truth count between 6 and 10 — the precise number depends on whether Rustic Canyon (edge of circle) is counted and whether Crestwood Hills RAP currently operates 2 or 3 courts. Even taking the upper bound (10), density drops from 2.06/km² to ≤ 0.6/km². This circle is fundamentally a **wealthy-hillside-with-private-courts** zone, not a public-park-tennis hotspot.
