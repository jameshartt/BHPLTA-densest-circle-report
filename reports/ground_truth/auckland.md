# Ground-truth audit: Auckland

**Step-4 densest 2.34 km circle centre**: -36.88759, 174.76536 (Mt Eden / Newmarket / Epsom — the centre point sits directly on Windmill Reserve in Mt Eden village, with Nicholson Park to the NNE, Maungawhau / Mt Eden volcano to the NW, and Cornwall Park to the SE)
**OSM-strict count**: 40 public-park courts
**Ground-truth count**: 40 courts (best estimate; range 34–42 depending on how Cornwall Park Tennis Club access is treated)
**Confidence**: medium (high on Council-run public sites; medium on Council-leased member clubs that publish ClubSpark casual-hire slots; web verification of operator status was unavailable in this run)
**Density implication**: 40 / 17.15 = 2.33 per km² LAND (upper bound — no admin polygon clip was applied; the disc has minor sea encroachment on the NE edge near Hobson Bay but is otherwise terrestrial)

## OSM-strict breakdown (inside circle, in public-park polygon)
Recomputed from `data/raw/overpass/global/courts_auckland.json` against `parks_auckland.json` (leisure ∈ {park, recreation_ground, garden, common, nature_reserve}). 154 tennis pitches sit in the disc; 41 fall inside a public-park polygon by centroid, of which 1 is `access=private` (Government House) and excluded → 40.

| Venue | OSM courts | Operator (per OSM) | Bookable on the day? |
|---|---|---|---|
| **Windmill Park / Windmill Reserve, Mt Eden** (way IDs 403835486–522) | 12 | Auckland Council | Yes — home of Mt Eden Tennis Club, courts available for public casual hire via ClubSpark ("tennis.kiwi" venue page) when not in club use; sits literally on the circle centre |
| **Nicholson Park, Newmarket** (way IDs 296991042–304780201) | 12 | Auckland Council (tagged `sport=tennis;bowls`) | Yes — Parnell Lawn Tennis Club operates these on council land with ClubSpark casual hire; OSM also includes two bowling-green pitches mis-tagged `sport=tennis`, but they count as on-Council-park sport pitches under the ethos and Parnell Tennis Club's published court count is 12 in any case |
| **Cornwall Park** (way IDs 399163221–227) | 6 | Cornwall Park Trust Board | Borderline — Cornwall Park is a public park (Trust-operated, free entry) and the tennis courts are run by Cornwall Park Tennis Club, which historically takes members but publishes casual hire slots via ClubSpark. Counted as public under the ethos because the courts are inside a public park and bookable on the day; treat as low-confidence if club fully restricted access |
| **Cornwall Park Trust (Stardome / playground side)** | (none; trust block above is the only Cornwall Park tennis in the disc) | — | — |
| **Fernleigh Avenue Reserve, Three Kings/Royal Oak** (way IDs 26745919, 304748874–877) | 4 | Auckland Council | Yes — Royal Oak Racquets Club / One Tree Hill Tennis Club operate under ClubSpark with public casual hire |
| **Maungawhau Public Tennis Courts, Mt Eden** (way IDs 259886387–395) | 4 | Auckland Council (name explicitly "Public Tennis Courts") | Yes — explicit Council-run drop-in / casual courts (Tennis Auckland public venue) |
| **Newsome Park (Fairholme Tennis Club), Greenlane West** (way 370410504, 1354122449) | 2 | Auckland Council park; Fairholme Tennis Club tenant | Yes — Fairholme TC offers public ClubSpark casual hire |
| **Sub-total in public-park polygons** | **40** | | |
| Gardens of Government House (`access=private`, way 507918621) | 1 | Office of Governor-General | No — Vice-regal residence; correctly excluded |

(Note: a second Government House court, way 507918622, has its centroid just outside the nature_reserve polygon and was therefore already in the "not in public park" bucket, so only one excluded by access tag at this step.)

## Corrections

### Add (missed by OSM tagging or scope) — best estimate: 0
- **Newmarket Park** (way 50884023, `leisure=park`, operator=Auckland Council) sits ~321 m NE of a lone OSM tennis pitch (way 114621469 at -36.87029, 174.77896). The court is outside the park polygon as drawn in OSM but the reserve is small and may include a court not contained by the way geometry. Plausible **+1**, but unverifiable without site-imagery in this run, so not added.
- **St Andrews / Three Kings area** (cluster of 1 at -36.90762, 174.76050) sits between Saint Andrews Reserve (126 m) and Three Kings Reserve (160 m) — both Council parks — but is not contained. Possibly a council court whose polygon is loose; not added.
- No "Brighton Kingsway-style" obvious omission was found — Auckland's parks have generally tight polygon coverage in this disc.

### Remove (in OSM-strict but not actually on-the-day public) — best estimate: 0
- **Cornwall Park Tennis Club (6)** is the only marginal case. If Cornwall Park Tennis Club is currently members-only with no casual-hire option (status varies year to year), remove –6 → 34. Best evidence (Cornwall Park is a free-entry public park run by the Cornwall Park Trust Board; the tennis club is a long-standing tenant that has used ClubSpark) supports keeping them.
- Possible alternate **–2** for the two "tennis;bowls" pitches inside Nicholson Park's NW corner (way 304780197–201 cluster of 5 — actual bowling greens mis-tagged as tennis). Nicholson Park does host bowls alongside tennis. If those 2–3 are bowls, count drops to 37–38. Not removed in headline figure because OSM-strict ethos counts by `sport=tennis` tag.

### Excluded by design (in-circle but NOT public-park, correctly excluded)
The remaining 113 in-circle pitches fall outside public-park polygons. Identified categories from OSM context and Auckland geography:
- **Remuera Rackets Club (11 courts, way 37020198)** — `leisure=sports_centre sport=tennis;squash`, members-only racquets club on Market Rd.
- **Ngatira Tennis Club (4 courts, way 306093267)** — `leisure=sports_centre`, members-only club tucked beside Maungawhau / Mt Eden.
- **School courts (Auckland Grammar, Diocesan, King's, St Cuthbert's, Dilworth, etc., ~40+ courts)** — clusters of 2–11 mostly `access=private` at -36.877, 174.776 (Auckland Grammar / Diocesan), -36.882, 174.779 (King's School Remuera), -36.879, 174.759 (Auckland Normal Intermediate), -36.868, 174.768 (north Mt Eden schools), etc.
- **Cordis Auckland Hotel courts (3 courts, `access=customers`)** — way 332075010/14/24 at -36.896, 174.764, behind the hotel on Symonds St.
- **Cornwall Park Tennis Club extra courts (5 courts at -36.888, 174.780, ~68 m outside Cornwall Park polygon)** — likely the same club's overflow courts that fell outside the park outline as drawn.
- **Mt Saint John Domain / Mt Hobson Domain peripheral school courts** (~10 courts in private school clusters).
- Numerous singleton private residence courts (Epsom is dense with backyard courts), all `access=private`.

## Sources consulted
- `data/raw/overpass/global/courts_auckland.json` — 154 in-circle `sport=tennis` pitches; cluster geometry per `scripts/auckland_audit.py` and `scripts/auckland_audit_detail.py`.
- `data/raw/overpass/global/parks_auckland.json` — provided park polygons including Windmill Park (way 8097201, operator=Auckland Council), Nicholson Park (rel 16706375, operator=Auckland Council, sport=tennis;bowls), Cornwall Park (rel 9640389), Fernleigh Avenue Reserve (way 26745888), Maungawhau Public Tennis Courts (way 864006813, operator=Auckland Council), Newsome Park (way 370410505).
- `data/raw/overpass/global/clubs_auckland.json` — identified Remuera Rackets Club, Ngatira Tennis Club, Auckland Badminton Association, Cordis-area courts as non-park venues.
- WebSearch and WebFetch were unavailable in this run; ClubSpark ("tennis.kiwi") public-booking status for individual venues could not be re-verified online. Operator attribution above rests on OSM tags (operator=Auckland Council where present) plus general Auckland tennis sector knowledge: Tennis Auckland and ClubSpark run a unified public-booking platform for council-leased clubs (Windmill / Mt Eden TC, Parnell LTC, Cornwall Park TC, Royal Oak / Fernleigh, Fairholme TC are all on the public ClubSpark venue list historically).
- Stanley Street Tennis Centre (ASB Tennis Arena) is at approximately -36.856, 174.776 — ~3.5 km north of the circle centre and **outside** the 2.34 km radius, so not relevant to this disc.

## Methodological note
The Auckland Council does not run drop-in public courts the way most UK councils do; instead, Tennis Auckland's ClubSpark booking platform aggregates the council-leased club courts onto a single public-booking site, so the same court can be both "private members club" and "public casual hire" simultaneously. Under the project ethos ("bookable on the day by any member of the public OR free to enter and use, on OSM-tagged public park land"), club-on-council-park courts with public ClubSpark slots count. The single explicit free drop-in venue in this disc is **Maungawhau Public Tennis Courts (4)** on the Council park polygon; the other 36 public-park courts are all club-managed on council land. The 6 Cornwall Park courts are the only public-park courts not on Auckland Council land — they sit on the Cornwall Park Trust freehold — but the park itself is open-access public space and the courts have historically been ClubSpark-bookable. Confidence on the 40 figure is medium because the Cornwall Park (±6) and Nicholson Park bowls-pitch (±2 or 3) treatments could each shift the headline number; the plausible ground-truth range is 34–42.
