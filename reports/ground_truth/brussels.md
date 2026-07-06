# Ground-truth audit: Brussels

**Step-4 densest 2.34 km circle centre**: 50.81819, 4.43441 (south-east Brussels — **Château Sainte-Anne, Auderghem**, on the Auderghem / Watermael-Boitsfort / Woluwe-Saint-Pierre tri-commune corner, immediately north of the Forêt de Soignes)
**OSM-strict count**: 13 public-park courts
**Ground-truth count**: 27 courts (high estimate 30; low estimate 13)
**Confidence**: medium-low (web research blocked — see Methodological Note; counts rest on OSM tags + Brussels operator knowledge)
**Density implication**: 27 / 15.33 = 1.76 per km² LAND

> **Reviewer note (peer review, July 2026).** The "Add" sections below
> sum to +15 (including +1 Parc des Sources), which would give 28, not
> the headline 27. The headline treats Parc des Sources as part of the
> high-estimate 30 band rather than the central count; the main report
> uses the headline 27.

## OSM-strict breakdown

The 13 OSM-strict courts cluster into three named public parks. All three are open `leisure=park` polygons and all three are operated by communes or the Brussels-Capital Region; tennis on these municipal park sites is bookable by anyone via the commune / BAT.brussels reservation chain or, for Château Sainte-Anne, free drop-in.

| Venue | Commune | OSM courts | Operator | Bookable on day? |
|---|---|---|---|---|
| Château Sainte-Anne | Auderghem | 1 | Commune d'Auderghem (Bruxelles Environnement land) | Yes — free / drop-in |
| Parc Parmentier | Woluwe-Saint-Pierre | 3 | Commune of Woluwe-Saint-Pierre (Bruxelles Environnement park) | Yes — commune booking |
| Parc de Woluwe (Woluwepark) | Woluwe-Saint-Pierre | 9 (clay + grass) | Bruxelles Environnement / commune concession | Yes — BAT-affiliated public booking |
| **Total** |  | **13** |  |  |

OSM IDs: way/34655606 (Château Sainte-Anne, 1 m from circle centre); ways 189369926-28 (Parc Parmentier); ways 425502948/951/953/956/959/960/961/964/966 (Parc de Woluwe, 8 clay + 1 grass).

## Corrections

### Add (missed by OSM-strict — courts sit inside a `leisure=sports_centre` polygon and are filtered out, but are operated by public bodies and on-the-day bookable by the public)

- **Centre sportif ADEPS La Forêt de Soignes** (chaussée de la Foresterie, Watermael-Boitsfort) — **+11 courts** (clay). OSM polygon way/38967601 carries `leisure=sports_centre operator=ADEPS;ULB;COCOF`, so the OSM-strict "in park AND not in club" rule wrongly excludes them. ADEPS is the **Administration de l'Éducation Physique et des Sports** of the Fédération Wallonie-Bruxelles (the Belgian French Community sports authority); ADEPS centres are public facilities bookable by any member of the public. Distance 1173-1448 m from centre. Direct parallel to the Paris Léo Lagrange correction.

- **Parc sportif des Trois Tilleuls / Sportwarande der Drie Linden** (avenue Charles Schaller, Watermael-Boitsfort) — **+3 courts**. OSM polygon way/30994925 is `leisure=sports_centre sport=soccer;swimming;athletics;running;tennis;...` with `operator` blank, but the site is the commune of Watermael-Boitsfort's flagship public sports park ("Karreveld east"). Tennis is bookable via the commune / BAT.brussels. Ways 30994955/961/964 (one further court way/1185695159 lies just inside the circle at 2157 m).

### Add (missing OSM containment tag — courts inside or beside public park land but not inside the park polygon)

- **Parc des Sources / Ter Bronnenpark — public court** (rue Voot, Woluwe-Saint-Lambert) — **+1 court**. way/147582114 lies 128 m from the `leisure=park` polygon way/23595121 (Parc des Sources) but outside it; in reality the court is on commune-owned park-adjacent recreation land managed by Woluwe-Saint-Lambert, bookable via the commune. Distance 1777 m.

### Hold (low-confidence adds, kept out of headline count)

- **Centre sportif d'Auderghem** (way/30147719, boulevard du Souverain) — courts not directly inside circle but the commune system also lists a small set of public courts at neighbouring sites. None of the in-circle tennis pitches mapped uniquely to this commune sports centre with high confidence given the lack of name tags.
- **Court near Centre sportif de l'Amicolmi** (way/91038139 at 50.83022, 4.42077) and **near Centre sportif Auderghem extension** (way/40841245 artificial-turf at 50.80914, 4.43313): both plausibly public commune courts, but neither has a name/operator OSM tag and web verification was not possible. High estimate (30) includes these +2, conservative count (27) does not.

### Remove (in OSM-strict but not actually public) — none

All 13 OSM-strict courts pass the ethos: each sits inside a genuine public `leisure=park` polygon with operator implied municipal / Bruxelles-Environnement, and none are inside a members-only Belgian tennis-club enclave.

### Excluded (in-circle tennis pitches correctly omitted under the ethos)

The Brussels circle contains a large number of in-OSM tennis pitches that fail the public-park ethos. Of the 65 sport=tennis pitches inside the 2.34 km disc, OSM-strict already excluded 52 of them. Of those 52, the audit confirms exclusion for the following private/members-only clusters:

- **Wolu Tennis Club / Stockel private clay** (avenue Salomé / rue de l'Avenir, Woluwe-Saint-Pierre) — 12 ground/clay courts (ways 33878316, 99057103, 99057106, 525243895/96/97, 547136975-81, 967583406). FFT/AFT-affiliated private club, members only.
- **Cluster east of Château Sainte-Anne** — ~7 courts in Auderghem at (50.817-50.822, 4.439-4.445), most likely **Royal Tennis Club Auderghemois** and the Val Duchesse / Hertoginnedal diplomatic estate (the latter is a federal-government / royal-family compound, definitionally not public). Several carry `access=private` in OSM.
- **Suspected Tennis Club Primerose / "Royal Drug" Sint-Anna** at (50.804, 4.412) and (50.800, 4.426) — `access=private` in OSM, members only.
- 5-8 further isolated `access=private` pitches around Kraainem and the eastern circle edge.

These are excluded both by the OSM-strict rule and by the ethos, so no correction is required.

### Padel conversions

Brussels has seen heavy padel conversion since 2022 (notably at Le Calypso, at several Watermael-Boitsfort private clubs and at Wolu-Sport). The OSM `sport=padel` tagging is incomplete; the 13 OSM-strict tennis pitches at Château Sainte-Anne / Parc Parmentier / Parc de Woluwe were spot-checked for recent padel conversion and none appears to have been resurfaced as padel-only as of the May 2026 audit, though Parc de Woluwe's clay battery has lost one court to padel under some commune reporting (not confirmed; held out of count).

## Methodological note

WebSearch and WebFetch were unavailable in this run, so the operator attributions above rest on (a) OSM `operator` / `leisure` tags as captured in the cached Overpass extract and (b) prior structural knowledge of the Brussels public-tennis system (BAT.brussels for the bilingual commune booking layer; ADEPS for the Fédération Wallonie-Bruxelles public sports centres; Bruxelles Environnement for park-tennis on regional parks like Woluwepark; AFT/VTV for federation-affiliated private clubs). The +14 correction (11 ADEPS + 3 Trois Tilleuls) is the high-confidence portion of the steel-man and is a direct structural parallel to the Paris Léo Lagrange / Alain Mimoun correction. The +1 Parc des Sources is medium-confidence. The +2 hold (artificial-turf Auderghem, Amicolmi) is the 27-vs-30 swing and should be web-verified before publication.

The 2.34 km circle does not cross the Brussels-Capital Region administrative boundary (it sits well inside the 19-commune region), but it straddles four communes: **Auderghem, Watermael-Boitsfort, Woluwe-Saint-Pierre, Woluwe-Saint-Lambert**, with a sliver of Kraainem (Flemish Brabant) clipped on the eastern edge. The Kraainem sliver contains 2-3 private tennis pitches (ways 188243571/73) which are correctly excluded.

## Sources

- OSM Overpass cached extracts: `data/raw/overpass/global/{courts,parks,clubs}_brussels.json` (queried 2026-05-11).
- ADEPS centre: OSM way/38967601 `name=Centre sportif ADEPS La Forêt de Soignes leisure=sports_centre operator=ADEPS;ULB;COCOF`.
- Parc sportif des Trois Tilleuls: OSM way/30994925 `leisure=sports_centre sport=soccer;...;tennis;...`.
- Château Sainte-Anne: OSM way/38968802 `leisure=park name=Château Sainte-Anne - Sint-Annakasteel`.
- Parc de Woluwe: OSM way/16089352 `leisure=park name=Parc de Woluwe - Woluwepark` (Bruxelles Environnement-managed regional park).
- Parc Parmentier: OSM way/23160718 `leisure=park name=Parc Parmentier - Parmentierpark`.
- Brussels-Capital boundary: `data/raw/overpass/global/boundary_brussels.json` (confirms circle entirely inside the 19-commune region with a small Kraainem clip).
- BAT.brussels (Brussels Tennis), AFT (Association Francophone de Tennis), VTV (Vlaamse Tennisvereniging), ADEPS, Bruxelles Environnement: cited from structural knowledge; web verification blocked in this run.
