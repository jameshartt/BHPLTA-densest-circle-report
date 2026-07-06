# Ground-truth audit: Paris

**Step-4 densest 2.34 km circle centre**: 48.83319, 2.44005 (south-east 12e arrondissement / Bois de Vincennes border)
**OSM-strict count**: 27 public-park courts
**Ground-truth count**: 43 courts (high estimate 47; low estimate 27)
**Confidence**: medium
**Density implication**: 43 / 9.60 = 4.48 per km^2 LAND

> **Reviewer note (peer review, July 2026).** The itemised additions
> below sum to +19 (+16 Léo Lagrange, +1 Alain Mimoun, +2 rue du Sahel),
> which would give 46, not the headline 43. The main report carries the
> conservative headline figure (43 = 27 + 16 Léo Lagrange, the
> high-confidence add) and treats the +3 balance as part of the
> high-estimate 47 band. The ~6-10 known Vincennes / Saint-Mandé courts
> outside the 75-scope are carried in the report's Step 7 table as a
> sensitivity (Paris ~2.9-3.2 with them counted).

## OSM-strict breakdown

The 27 OSM-strict courts cluster into two named public Tennis Paris facilities, both sitting inside the `leisure=park` polygon for **Bois de Vincennes** (12e arr., Ville de Paris). Both are bookable on the day by the public via tennis.paris.fr / Paris municipal booking.

| Venue | Arrondissement | OSM courts | Operator | On-the-day public? |
|---|---|---|---|---|
| Tennis La Faluère (Bois de Vincennes) | 75012 | 23 | Ville de Paris (Tennis Paris) | Yes — tennis.paris.fr |
| Tennis du Polygone de Vincennes (south of Lac Daumesnil) | 75012 | 4 (clay) | Ville de Paris (Tennis Paris) | Yes — tennis.paris.fr |
| **Total** |  | **27** |  |  |

(The 23-court cluster is anchored by an OSM node tagged `name=Tennis La Faluère` with `website=https://www.paris.fr/lieux/tennis-la-faluere-2964`. The 4 clay courts at 48.821, 2.460 are immediately south of Lac Daumesnil — coordinates and surface match the Tennis du Polygone municipal site.)

## Corrections

### Add (missed by OSM-strict — courts sit inside a `leisure=sports_centre` polygon and were filtered out, but are municipal Tennis Paris facilities open to the public on the day)

- **Centre sportif Léo Lagrange — Tennis Léo Lagrange** (Bois de Vincennes, 12e), ~324 m from circle centre — **+16 courts**. OSM tags the surrounding polygon `leisure=sports_centre` (way 880497044), so the OSM-strict "in-park-AND-not-in-club" rule wrongly excludes them. This centre is operated by the Ville de Paris; courts are bookable to any Paris resident or visitor via tennis.paris.fr on the day. (Sixteen tennis pitches mapped: ids 99993696/97/99/703/710/711 and 211358364-374.)
- **Centre sportif Alain Mimoun** (15 rue de la Nouvelle-Calédonie, 75012) — **+1 court** (way 144789274), ~2164 m from centre. Ville de Paris municipal centre; tennis bookable via tennis.paris.fr ("Tennis Alain Mimoun").
- 2 unattributed tennis pitches at ~48.8427, 2.4124 (ways 144790271, 144790274), 2284-2306 m from centre. They lie just inside the radius and appear to belong to a Ville de Paris municipal stadium complex on rue du Sahel / Centre sportif Léo Lagrange satellite courts. Conservatively counted but with low confidence.

### Hold (in-circle but excluded — correctly not public)

- **INSEP** (Institut National du Sport, de l'Expertise et de la Performance) — 4 courts (ways 174816558/62/64/65 and 667331272 = 5 total). Elite national training facility, gated, not bookable by the public. Correctly excluded.
- **Stade Jean-Pierre Garchery** — 5 courts (ways 91275132, 238414502-05) at the southern edge of the circle (2110-2193 m). Garchery is a Ville de Paris stadium but its tennis pitches are primarily allocated to school groups, clubs and FFT-affiliated associations. Not reliably bookable on the day by the general public on the Tennis Paris drop-in system. Conservatively excluded; would add +5 under a more generous definition (giving the high estimate of 47).

### Remove (already absent from OSM-strict)

- No false positives detected in the 27 OSM-strict courts. Neither cluster falls inside a members-only club polygon. (The major members-only Paris exclusions — Stade Roland Garros, Tennis Club de Paris, Racing Club de France — all sit in the Bois de Boulogne on the west side of the city, far outside this south-east circle.)

### Padel conversions

- No padel-only conversions detected in the OSM data for the two public sites. Tennis La Faluère's published Paris.fr listing is for tennis pitches. (Paris has many recent padel conversions, especially at private clubs in the Bois de Boulogne, but none affect this circle.)

## Cross-boundary note

The 2.34 km circle straddles the Paris admin boundary. A substantial portion of the eastern half (Bois de Vincennes east of the Avenue de la Pyramide, plus the town of **Vincennes** itself and parts of **Saint-Mandé** and **Charenton-le-Pont**) sits in the Val-de-Marne (94) département, NOT in the 75 admin scope of our cached Overpass extract. This means:

- The **Centre Sportif Hector Berlioz** / municipal courts of Vincennes (Avenue de Paris) and the **Tennis Municipaux de Saint-Mandé** are geographically inside the circle but invisible to our Paris-75 query.
- A rough manual scan of OSM via name search suggests ~6-10 additional public-park / municipal courts in Vincennes and Saint-Mandé within the radius. These are not counted in either the OSM-strict 27 or the ground-truth 43, because the comparative ranking uses Paris (75) only as the admin scope.

If the comparative ranking were re-scoped to administrative Île-de-France or to a pure geographic 2.34 km disc, the ground-truth count would likely rise to **~50-53 courts**. Flagging for the cross-city methodology section.

## Sources

- OSM Overpass cached extracts: `data/raw/overpass/global/{courts,parks,clubs}_paris.json` (queried 2026-05-11).
- Tennis La Faluère: OSM node 1774584911 tags `name=Tennis La Faluère`, `website=https://www.paris.fr/lieux/tennis-la-faluere-2964`.
- Tennis Paris municipal booking system: tennis.paris.fr (operator: Ville de Paris, Direction de la Jeunesse et des Sports) — covers La Faluère, Polygone, Léo Lagrange, Alain Mimoun and ~40 other sites city-wide.
- INSEP: way 174816555, `website=https://www.insep.fr/` — national elite centre, not public.
- Stade Pershing, Stade Garchery: OSM `leisure=sports_centre` polygons in Bois de Vincennes; not within the Tennis Paris on-the-day drop-in system at audit time.
- Cross-boundary: Paris admin boundary `boundary_paris.json` does not cover Vincennes (94300) or Saint-Mandé (94160); flagged as scope limitation.
