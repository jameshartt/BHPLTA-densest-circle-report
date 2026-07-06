# Ground-truth audit: Toronto

**Step-4 densest 2.34 km circle centre**: 43.76376, -79.32090 (North York — Don Mills / Parkwoods / Henry Farm)
**OSM-strict count**: 32 public-park courts
**Ground-truth count**: 19 (likely 19-22 depending on interpretation of community-club courts)
**Confidence**: medium
**Density implication**: 19/17.10 = 1.11 per km² LAND (range 1.11-1.29)

> **Revision note (peer review, July 2026).** The header originally said
> 18 / 1.05, but this file's own "Ground-truth net" section computes
> 32 − 13 = **19** (Roywood 4 + Fenside 4 + Brookbanks 4 + Clydesdale 4 +
> Three-Valleys-area 3). The header now matches the body arithmetic,
> which is what the main report's tables use (19, 1.11).

## OSM-strict breakdown

All 32 OSM-strict courts sit inside a `leisure=park` polygon. Verifying each against Toronto's
public-tennis model (City Parks free drop-in vs. community-club leases that gate access by membership):

| Venue (OSM park id) | OSM courts | Operator | Bookable on day? |
|---|---|---|---|
| Roywood Park (w121986112) | 4 | City of Toronto Parks (free, drop-in) | Yes — unlocked, first-come |
| Fenside Park (w122081776) | 4 | City of Toronto Parks (free, drop-in) | Yes — unlocked, first-come |
| Wishing Well Park (w23224039) | 3 | Wishing Well Tennis Club (community lease) | Member-priority; limited public hours |
| Brookbanks Park (w225584515) | 4 | City of Toronto Parks (free, drop-in) | Yes — unlocked, first-come |
| Unnamed park w36007475 (Three Valleys area) | 3 | City of Toronto Parks (free, drop-in) | Yes |
| Graydon Hall Park (w59142587) | 3 | Graydon Hall Tennis Club (community lease) | Member-only in practice |
| Broadlands Park (w225584245) | 4 | Broadlands Community Tennis Club | Member-priority; club season May-Sep |
| Bridlewood Park (w225582211) | 3 | Bridlewood Tennis Club | Member-only in practice |
| Clydesdale Park (w25056343) | 4 | City of Toronto Parks (free, drop-in) | Yes — unlocked, first-come |

Total OSM-strict in park polygons: **32**.

## Corrections

### Remove (10 courts — community-club leases that are effectively members-only)

The Toronto model: parks-department land, but leased to a community tennis club that locks courts
during member-only hours and runs a season-long membership (~CAD $150-250). Per the audit ethos,
these should be excluded unless they offer on-the-day public booking. None of these four operate a
public day-rate booking system that I can confirm:

- **Wishing Well Park** -3 (Wishing Well TC — fenced/locked, member key)
- **Graydon Hall Park** -3 (Graydon Hall TC)
- **Broadlands Park** -4 (Broadlands Community TC — well-known member club)
- **Bridlewood Park** -3 (Bridlewood TC)

Counter-argument (steel-man): all four operate on City of Toronto Parks land and most community TCs
in Toronto are *required* to offer a public component (open public hours one weekday morning,
day passes, junior drop-in). If we adopt Brighton's relatively generous standard ("Kingsway counted"),
**some or all could be re-included**, yielding 22-25.

### Remove (already excluded by OSM-strict but flagged for completeness)

The 16 tennis pitches inside the circle but **outside** any park polygon are correctly excluded.
Spot-checks of their locations and tag patterns:

- **w299308461** (1 court, `access=private`) at 43.7773, -79.3106 — likely a residential/condo court.
- **w32605244** at 43.7730, -79.3383 — 7 courts, `surface=grass`. Grass tennis at this density in
  north-central Toronto = **Donalda Club** vicinity / private members' country club. Correctly excluded.
- **w1505094717/8** (2 courts) at 43.7685, -79.3451 — apartment-complex private courts.
- **w1504726421-26** (6 courts) at 43.7536-43, -79.3429 — clustered on Bushbury Dr; **Donalda Club**
  members-only tennis facility. Correctly excluded.
- **w1433494265/6** (2 courts) at 43.7505, -79.3389 — TDSB school grounds (Georges Vanier SS area) or
  Donalda overflow. Not publicly bookable.
- **w47940333/7** and **w1505095934/5** (4 courts total) near Parkway Forest — private apartment/condo
  amenity courts. Correctly excluded.

Also note an indoor **4-court covered tennis sports centre** (w38974844, `building=roof`, `sport=tennis`)
at 43.7731, -79.3299 (Sheppard / Don Mills). This is a private/pay-per-hour indoor facility (commercial),
not a public-park court. Correctly excluded under the "public park, free or on-the-day bookable" ethos.

### Add (0)

Sweeping OSM tennis pitches inside the circle (48 features) confirms no public-park courts were missed
by the OSM-strict filter. Toronto-side ground-truth searches for Henry Farm Tennis Club, Pleasant View
courts, L'Amoreaux Park etc.: Henry Farm TC's actual location (Henry Farm Park, ~43.776, -79.345) is
just outside the 2336.78 m circle. L'Amoreaux Park (huge tennis complex, 18+ courts) sits ~3.5 km
NE — outside. Pleasant View Park courts coincide with Wishing Well Park's three (already counted).

## Ground-truth net

- OSM-strict: 32
- Remove member-club courts (4 venues × ~13 courts): **−13**
- Add: 0
- **Strict ground truth**: 19 publicly accessible / drop-in courts (Roywood 4 + Fenside 4 + Brookbanks 4 + Clydesdale 4 + Three-Valleys-area 3)

If we adopt Brighton's more generous "operates on public land, season membership but partial public
access" standard, the count rises by some or all of the 13 community-club courts, yielding **22-32**.
The strict-reading point estimate is **19** (per the arithmetic above; an earlier draft said 18); **25** would be a defensible middle.

## Sources

- OSM data: `data/raw/overpass/global/courts_toronto.json`, `parks_toronto.json`, `clubs_toronto.json`
- City of Toronto Parks — Tennis program & permits policy (toronto.ca/parks): all "drop-in tennis"
  parks are unlocked, free, first-come; community clubs are listed separately under
  "Community Tennis Clubs"
- Local context: Don Mills / Henry Farm / Parkwoods is the home of several long-established
  community tennis clubs (Bridlewood, Broadlands, Graydon Hall, Wishing Well), each operating on
  City of Toronto Parks land but in practice running a season-membership model
- Spot-check via OSM coordinates against known facilities (Donalda Club at ~43.7536, -79.343; indoor
  dome at Sheppard/Don Mills)
