# Ground-truth audit: Buenos Aires

**Step-4 densest 2.34 km circle centre**: -34.55947, -58.49689 (Saavedra / Núñez, NOT Palermo — the densest 2.34 km circle is centred on Parque Presidente Sarmiento, ~5 km north-west of Palermo proper)
**OSM-strict count**: 13 public-park courts
**Ground-truth count**: ~6 (range 5-8)
**Confidence**: low-medium
**Density implication**: 6/11.04 = 0.54 per km² LAND (vs OSM-strict 1.18 — likely ~halved)

## Verification of the 13

26 tennis pitches (`leisure=pitch + sport=tennis`) sit inside the 2.34 km circle. Point-in-polygon against the Parque Presidente Sarmiento polygon (OSM way 294261998, leisure=park, no `access` tag, no `operator`) puts exactly 13 inside the park, matching the strict count.

The 13 form two clusters inside Parque Sarmiento:
- **Cluster A** (6 courts, 0-64 m from centre, eastern edge of park): ways 248723987, 248723988, 816715062-65
- **Cluster B** (7 courts, 740-790 m from centre, NW of park): ways 816716435-41

Excluded from the 13 by the OSM pipeline (correctly): 6 courts of Urquiza Tenis Club (private members club, way 86967655, 2.2-2.3 km south) and 1 padel court mis-tagged as tennis (Padel Le Bretón, way 1510171659, 1.77 km south).

## The problem: Parque Sarmiento is mostly private concessions

Parque Sarmiento in Saavedra is a GCBA-owned park, but most of its sports infrastructure has been leased to **Club Social y Deportivo Comunicaciones** (Club Comunicaciones), which operates tennis, swimming, football and racquet facilities on members-only terms. Only the **Polideportivo Parque Sarmiento** wedge of the park is run directly by the GCBA Direccción General de Deportes and is genuinely public on the day (it appears on the GCBA Polideportivos list with public booking).

Without a site survey, the most defensible breakdown of the 13 OSM courts is:

- The **Cluster A** of 6 courts (Av. Ricardo Balbín side, eastern edge): these match the layout of the Polideportivo Parque Sarmiento public tennis courts (~6 hard courts, GCBA-managed, bookable by the public).
- The **Cluster B** of 7 courts (deeper inside the park, NW corner near Av. García del Río / Av. Crisólogo Larralde): these match the Club Comunicaciones clay-court layout (members only).

The 6 "orphan" courts at 170-286 m (lat -34.558, lon -58.494 to -58.495), sitting just east of the Parque Sarmiento polygon boundary on what is functionally still GCBA land, are most plausibly additional Club Comunicaciones courts on a leased parcel — also **members only**.

This is a classic Argentine pattern: GCBA land, private operation, the public can only enter as a paying socio. The OSM `leisure=park` polygon does not subdivide concessions, so the strict pipeline over-counts.

## OSM-strict breakdown
| Venue | OSM courts | Operator | Bookable on day? |
|---|---|---|---|
| Parque Sarmiento east strip (Cluster A, 6 courts) | 6 | likely GCBA Polideportivo Parque Sarmiento | YES (public) |
| Parque Sarmiento NW strip (Cluster B, 7 courts) | 7 | likely Club Comunicaciones concession | NO (members) |

## Corrections
### Add
- None with confidence. The 6 orphan courts immediately east of the Sarmiento polygon (ways 248723975-77, 248723983, 248724157, 248724159) are inside the larger GCBA-owned parcel but are very likely Club Comunicaciones members courts, so should NOT be added.

### Remove
- **Cluster B (7 courts)**: ways 816716435, 816716436, 816716437, 816716438, 816716439, 816716440, 816716441. These sit inside the Parque Sarmiento polygon but on the Club Comunicaciones concession (members only). Removing them drops the count from 13 to 6.

(Lower bound 5 if one of the Cluster A courts is actually Comunicaciones-controlled; upper bound 8 if there are 2 extra public courts in the polideportivo not yet split out in OSM. 6 is the central estimate.)

## Caveats
- I could not access buenosaires.gob.ar or OSM directly for verification (web tools blocked in this run). The corrections rely on prior knowledge that Club Comunicaciones operates the bulk of Parque Sarmiento's tennis facilities under a long-running GCBA concession, and that the Polideportivo Parque Sarmiento has roughly six public courts. A site survey or buenosaires.gob.ar polideportivos page check is needed to firm this up.
- Argentina has had huge padel migration since 2018; some Sarmiento courts may now be padel rather than tennis even if still tagged `sport=tennis`. Cross-checking aerial imagery would tighten the count further.
- The OSM polygon for Parque Sarmiento includes the entire GCBA parcel, not just the publicly-accessible polideportivo wedge — this is the root cause of the over-count.

## Sources
- OSM cached data: `data/raw/overpass/global/courts_buenos_aires.json`, `data/raw/overpass/global/parks_buenos_aires.json`, `data/raw/overpass/global/clubs_buenos_aires.json`
- Parque Sarmiento polygon: OSM way 294261998 (wikidata Q6062504)
- Prior knowledge: Club Comunicaciones (Av. Crisólogo Larralde 5050), Polideportivo Parque Sarmiento (Av. Balbín 4750), Urquiza Tenis Club (private).
- Recommended follow-ups: buenosaires.gob.ar/desarrollohumanoyhabitat/deportes/polideportivos for the official GCBA public-facility roster; clubcomunicaciones.com.ar for the private-concession court count; Wikimapia or Google Earth Pro for visual confirmation of which clusters belong to which operator.
