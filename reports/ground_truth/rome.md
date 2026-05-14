# Ground-truth audit: Rome

**Step-4 densest 2.34 km circle centre**: 41.87483, 12.43615 (Monteverde Vecchio / Gianicolense, just south of Villa Doria Pamphilj)
**OSM-strict count**: 26 public-park courts (claimed)
**OSM raw within circle**: 69 tennis pitches across 20 distinct facilities
**Ground-truth count**: 0–4 truly public on-the-day-bookable park courts
**Confidence**: medium-high (no live municipal-booking-site fetch possible from sandbox; conclusion rests on OSM tags, Rome's well-documented circolo concession model, and venue identification)
**Density implication**: ~0–4 / 17.14 km² = **0.00–0.23 per km² LAND** (vs the OSM-strict 1.52)

## Why the OSM-strict 26 is wildly inflated

Re-running the polygon-in-park test on the cached Overpass dump gives:
- `leisure=park` only → **3 courts** (Villa Doria Pamphilj, cluster C15)
- `leisure in {park, garden, nature_reserve}` → **30 courts** (adds 27 inside *Riserva Naturale Valle dei Casali*, OSM relation 2985749, operator=RomaNatura)

The "26" reported by the pipeline is between these two — almost certainly the nature-reserve polygon is being treated as a "park". In Rome that is the wrong assumption: RomaNatura nature reserves are public land, but tennis-court footprints inside them are *concessions* to FIT-affiliated private circoli that charge full membership fees. The reserve boundary swallows half a dozen separate clubs (Villa York, Casali, Bravetta, etc.) and mis-labels every one of their courts as a "public-park court".

## Venues inside the circle (20 clusters, 69 raw courts)

| # | Cluster centre | Courts | Likely venue | Operator | Bookable on day? |
|---|---|---|---|---|---|
| C1 | 41.8746, 12.4374 (centre) | 10 (7 active + 3 OSM-tagged `disused=yes`) | Tennis Club Villa Pamphili / Monteverde (Via di Donna Olimpia) | FIT private circolo | **No** — members + season subscribers |
| C2 | 41.8789, 12.4367 | 1 | Embassy/residential court (off Piazza San Pancrazio) | Private | **No** |
| C3 | 41.8789, 12.4339 | 3 | Adjacent to swim-only sports_centre way/553812231 (Piscina Garbatella-Monteverde area) | Private/club | **No** |
| C4 | 41.8763, 12.4304 | 4 | Inside sports_centre way/36851612 next to Piscina Comunale Juventus Nuoto | FIT private circolo | **No** (pool itself is municipal) |
| C5 | 41.8810, 12.4311 | 6 | Circolo on Mura Gianicolensi (Largo Berchet area) | FIT private circolo | **No** |
| C6 | 41.8781, 12.4457 | 1 | Single court on Gianicolo flank | Likely embassy/private | **No** |
| C7 | 41.8794, 12.4260 | 2 | SSD Vita-adjacent satellite or Piscina-Juventus annex | Private | **No** |
| C8 | 41.8637, 12.4313 | 13 | **Villa York** (OSM relation/12571878, multi-sport, FIT-affiliated) | Private circolo, RomaNatura concession | **No** — members only |
| C9 | 41.8609, 12.4415 | 1 | Casali residential/condominio court | Private | **No** |
| C10 | 41.8877, 12.4253 | 4 | Aurelio cluster near Vita Club annex | Private | **No** |
| C11 | 41.8867, 12.4233 | 1 | Vita Club annex / Aurelio | Private | **No** |
| C12 | 41.8720, 12.4144 | 9 (all clay) | Bravetta clay circolo (inside sports_centre way/36875269, adj. Giardino A. Mazzoni) | FIT private circolo | **No** |
| C13 | 41.8895, 12.4452 | 1 | Inside/edge of Villa Doria Pamphilj (Giardino dei Cedrati) | RomaNatura/Comune concession | **Unclear — likely private use** |
| C14 | 41.8604, 12.4478 | 1 | Bruzzi-Tantucci / Villa Flora condominio | Private | **No** |
| C15 | 41.8853, 12.4552 | 3 | **Villa Doria Pamphilj — Teatro / Roseto area** | Comune di Roma (Pamphilj is municipal park) | **Possibly** (Pamphilj courts have historically been concession-run; current status uncertain) |
| C16 | 41.8854, 12.4169 | 5 | **SSD Vita Club** (vitaclub.it — confirmed in OSM tags) | Private gym/tennis | **No** for full members-only courts; some clubs offer pay-per-hour but Vita Club is membership-driven |
| C17 | 41.8927, 12.4399 | 1 | Parco Enrico Modigliani area, condominio | Private | **No** |
| C18 | 41.8822, 12.4136 | 1 | Aurelio condominio | Private | **No** |
| C19 | 41.8720, 12.4101 | 1 | Bravetta condominio/scuola | Private/school | **No** |
| C20 | 41.8568, 12.4243 | 1 | Casaletto, near Domar Sporting Club | Private | **No** |

## Corrections vs OSM-strict 26

### Remove from count
- **All 27 courts inside Riserva Naturale Valle dei Casali**: these are not park courts — they're FIT-circolo concessions on RomaNatura land (Villa York 13, Bravetta clay 9, plus smaller clusters around C5/C8/C9). The "nature reserve" polygon is being mis-treated as a public park.
- **3 disused courts at C1** (OSM `disused=yes` on ways 477887797/799/801): should be excluded under any "bookable" definition.
- **Any court inside a `leisure=sports_centre` polygon with no `access=yes`**: under the brief's ethos these are private circoli, even if topologically inside a park.

### Add (potential public-bookable inside circle)
- **0–3 Villa Doria Pamphilj courts (C15)**: the only courts in the circle definitively inside a `leisure=park` polygon under the municipal park (Pamphilj is owned by Comune di Roma). Historically the Pamphilj tennis "Roseto/Cedrati" courts have been managed by a concessionaire with mixed public/member access. Confidence on these being on-day-bookable is **low to medium**.
- **C13 (1 court, edge of Pamphilj)** could plausibly be added on the same logic.

### Not in OSM at all worth flagging
- The big-name Rome public-facing tennis assets — **Foro Italico** (Pietrangeli/Centrale; ~3 km NNE), **Tennis Club Parioli**, **Circolo Aniene**, **Circolo Italiano del Tennis** (all famous members-only), and **TC EUR** — are all **outside** this circle and irrelevant.
- No `comune.roma.it`-branded municipal tennis facility appears inside this circle in the OSM dump; Rome's municipal tennis pipeline is weak — most "park courts" are actually concession-circoli (the pattern Brighton/Manchester would never tolerate).

## Final number

A defensible **ground-truth public-park court count for this 2.34 km Monteverde/Gianicolense circle is 0–4**, with **2** as a midpoint estimate (the Pamphilj Teatro/Roseto cluster, assumed currently bookable to the public). This is dramatically lower than the OSM-strict 26.

| | OSM-strict | Ground-truth |
|---|---|---|
| Count | 26 | 2 (range 0–4) |
| Density / km² land | 1.52 | 0.12 (range 0.00–0.23) |

Rome's central-west tennis density is **>10× over-counted** by the OSM-strict heuristic because Italian circoli sit physically inside park/reserve polygons but operate as gated private clubs. This is the canonical Mediterranean failure mode of the OSM-strict global ranking and Rome should carry a large downward correction in the comparative table.

## Sources

- OSM Overpass cached dumps in `data/raw/overpass/global/{courts,parks,clubs,boundary,water}_rome.json` (timestamps 2026-05-11 to 2026-05-13).
- Confirmed OSM tags:
  - relation/12571878 "Villa York" `sport=soccer;tennis;swimming;waterpolo`, `leisure=sports_centre`
  - way/463262838 "Società Sportiva Dilettantistica Vita" `website=https://www.vitaclub.it/`, `leisure=sports_centre`, `description=tennis,_piscina,_palestra,_fitness`
  - relation/2985749 "Riserva Naturale Valle dei Casali" `leisure=nature_reserve`, `operator=RomaNatura`
  - relation/2985897 "Villa Doria Pamphilj" `leisure=park`
  - ways 477887797/799/801 `disused=yes` (3 disused courts at C1)
- Rome circolo / RomaNatura concession model: well-documented (FIT affiliate club directory; RomaNatura concession registry). Web verification of comune.roma.it / vitaclub.it / villayork.it could not be performed in this sandbox; flagged as residual uncertainty.
- Brighton precedent comparison: 36 → 43 (additive). Rome moves the opposite direction (26 → ~2), consistent with Mediterranean private-circolo pattern.
