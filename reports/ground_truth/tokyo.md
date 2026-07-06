# Ground-truth audit: Tokyo (23 wards)

**Step-4 densest 2.34 km circle centre**: 35.77557, 139.60057 (Nerima ward, NW edge — on the 大泉さくら運動公園 tennis courts, ~150 m south of the Tokyo/Saitama prefecture boundary)
**OSM-strict count**: 18 public-park courts
**Ground-truth count**: ~70 courts (high 79, conservative 52)
**Confidence**: medium
**Density implication**: 70 / 17.14 = 4.08 per km² LAND (upper bound; see scope caveat)

> **Reviewer note (peer review, July 2026).** The high-confidence adds
> below sum to +54 (→ 72), the headline says "~70", and the high
> estimate of 79 does not decompose exactly from the itemised bands —
> treat all three as the ~±10% estimates they are. This audit gives
> court *counts* only; the two Tokyo-recount densities quoted in the
> main report divide the same ~25-30 Tokyo-side courts by different
> denominators (Tokyo-side land ≈ 3.0-3.6; full fair disc ≈ 1.5-1.8),
> and both are now labelled as such there.

## OSM-strict breakdown

All 18 sit inside a `leisure=park` polygon and outside any club polygon.

| Venue (JP + EN) | OSM courts | Operator | Bookable? |
|---|---|---|---|
| 青葉台公園 (Aobadai Park, Asaka-shi) | 6 (way/682424119) | 朝霞市 | Yes — Asaka 公共施設予約 |
| 和光市運動場 (Wako Athletic Ground) | 4 (way/1315511352) | 和光市 | Yes — Wako 公共施設予約 |
| 大泉学園町希望が丘公園 (Kibōgaoka Park, Nerima) | 3 (way/734173723, `operator=練馬区`) | 練馬区 | Yes — Nerima 区民施設予約 |
| 大泉さくら運動公園 (Oizumi Sakura Sports Park, Nerima) | 3 (way/234875355) | 練馬区 | Yes |
| びくに公園 (Bikuni Park, Nerima) | 2 (way/306994974) | 練馬区 | Yes |

## Corrections

Cluster geometry reconstructed by union-find on inter-court distance ≤ 200 m. 19 clusters total. Reverse-resolved against nearest tagged park.

### Add (missed by OSM-strict — courts adjacent to named public parks but outside the mapped `leisure=park` outline)

**High confidence (+54):**
- **新座市総合運動公園** (Niiza Sports Park) — 11 at (35.7794, 139.5850); ways 673520914–921, 932–934.
- **和光市運動場 extension** — 6 at (35.7741, 139.6142); ways 1025572204, 1358471817–820, 1358471826. Sub-polygons untagged.
- **和光市総合体育館 tennis area** — 7 at (35.7692, 139.6151); ways 640296957–963. Adjacent to `leisure=sports_centre` 和光市総合体育館.
- **大泉さくら annexed** — 4 at (35.7745, 139.6014); ways 1041190348–351, 1041190302–303. Same 練馬区 facility.
- **朝霞中央公園テニスコート** — 6 at (35.7870, 139.5912); ways 682204511–518, 682677554.
- **朝霞市総合グラウンド / シンボルロード** — 4 at (35.7917, 139.5919); ways 682677555–558.
- **和光樹林公園** — 3 at (35.7809, 139.5960); ways 682195706–708. 都立 / Saitama Pref jointly-managed (`wikidata=Q28683334`).
- **あけぼの公園 (Asaka)** — 3 at (35.7921, 139.6045); ways 682204506–508.
- **大泉中央公園** — 1 at (35.7768, 139.5944); way 681110353. **都立**, `operator=東京都`, `wikidata=Q17221056`.
- **新座市西堀運動公園** — 4 at (35.7593, 139.5878); ways 674181576–579. ~60 m from 西本村憩いの森 polygon.
- **NE Wako park cluster** — 5 at (35.7810, 139.6107); ways 1299446557–561.

**Low confidence (+5):**
- Cluster J (3 at 35.7628, 139.5982; ways 650041413/416/418) — possibly 練馬区 小公園.
- Cluster R (1 at 35.7896, 139.5849; way 1047488079) and Cluster S (1 at 35.7823, 139.5910; way 1136457084) — isolated, no name tags; could be school/corporate.

### Remove

None. All 18 OSM-strict pitches anchor to named, on-the-day-public municipal parks.

### Excluded by design (correctly not counted)

- 2 courts (ways 670713963, 670713965) inside an unnamed `leisure=sports_centre sport=tennis` polygon (way/670713961) at (35.7674, 139.6240). Almost certainly a commercial tennis school. Correctly filtered.

## Cross-prefecture scope caveat

The circle centre lies ~150 m south of the **Tokyo–Saitama prefecture boundary**. Of 19 clusters:
- **Tokyo 23 wards (Nerima)**: D, J, K, O, P, Q, S — 12 of the OSM-strict 18.
- **Saitama (Wako, Asaka, Niiza)**: A, B, C, E, F, G, H, I, L, M, R — 6 of the OSM-strict 18 (青葉台 + 和光市運動場) and the bulk of additions.

Roughly **40–45 of the ~70 ground-truth courts sit in Saitama**, not Tokyo 23 wards. Same issue as Paris/Vincennes-in-94. The bbox-scoped 17.14 km² land figure also extends into Saitama. If re-scoped to a Tokyo 23 wards admin polygon, ground-truth is **~25–30 courts** and OSM-strict drops to **~12**. The headline ~70 is over the full 17.14 km² disc; flag for the cross-city methodology section.

## Tokyo-specific notes

- Public-park tennis is overwhelmingly **抽選 (lottery)** booked 1–2 months ahead via each municipality's 公共施設予約システム. Per the ethos, this counts as "on-the-day public" because any resident or visitor can apply.
- No padel conversion detected; padel remains mostly indoor/private in Japan as of 2026.
- Corporate housing courts are common in this NW belt (former Camp Drake area + 1970s–90s 社宅 estates); they appear in OSM as untagged 1–3 court pitches with no containing park polygon — hence the low-confidence flag on ~5 isolated clusters.
- **光が丘公園** (Hikarigaoka Park) — Nerima's flagship 8-court public venue mentioned in the brief — sits ~3.1 km SE of centre and is **outside** the 2.34 km radius.

## Sources

- `data/raw/overpass/global/{courts,parks,clubs}_tokyo_23_wards.json` (cached 2026-05-11; bbox scope extends into Saitama). 81 in-circle tennis pitches, 10,901 park polygons, 400 club elements.
- OSM tag-derived attributions: `addr:city=練馬区` / `operator=練馬区` on Nerima parks; `operator=東京都` + `website=tokyo-park.or.jp` on Ōizumi Chūō; `wikidata=Q28683334 wikipedia=ja:和光樹林公園` on Wakō Jurin; `website=city.nerima.tokyo.jp/.../oizumisakura.html` on Oizumi Sakura.
- Audit scripts: `scripts/tokyo_audit{,_detail,_boundary,_cluster_n}.py`.
- WebSearch and WebFetch were unavailable in this run; municipal reservation-system attributions rest on OSM tag values and standard Japanese public-park naming conventions.
