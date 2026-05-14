#!/usr/bin/env python3
"""Analyze Tokyo (23 wards) OSM data for the 2.34km circle ground-truth audit.

Centre: 35.77557, 139.60057 (Nerima / Itabashi area)
Radius: 2336.78 m
"""
import json
import math
from collections import defaultdict, Counter

CENTRE_LAT = 35.77557
CENTRE_LON = 139.60057
RADIUS_M = 2336.78

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def centroid(elem):
    if elem.get('type') == 'node':
        return elem['lat'], elem['lon']
    if 'center' in elem:
        return elem['center']['lat'], elem['center']['lon']
    if 'geometry' in elem:
        coords = elem['geometry']
        if coords:
            lat = sum(c['lat'] for c in coords) / len(coords)
            lon = sum(c['lon'] for c in coords) / len(coords)
            return lat, lon
    return None, None

def point_in_polygon(lat, lon, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        yi, xi = poly[i]
        yj, xj = poly[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'

with open(f'{BASE}/courts_tokyo_23_wards.json') as f:
    courts = json.load(f)
with open(f'{BASE}/parks_tokyo_23_wards.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_tokyo_23_wards.json') as f:
    clubs = json.load(f)

print(f"Total courts (Tokyo-scoped): {len(courts['elements'])}")
print(f"Total park polygons (Tokyo-scoped): {len(parks['elements'])}")
print(f"Total club elements: {len(clubs['elements'])}")

in_circle = []
for c in courts['elements']:
    lat, lon = centroid(c)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= RADIUS_M:
        c['_lat'] = lat
        c['_lon'] = lon
        c['_dist_m'] = d
        in_circle.append(c)

print(f"\nCourts within circle (Tokyo OSM scope only): {len(in_circle)}")
tennis_only = [c for c in in_circle if 'tennis' in str(c.get('tags', {}).get('sport', '')).lower()]
print(f"  of which tagged tennis: {len(tennis_only)}")

# Build park polygons
park_polygons = []
for p in parks['elements']:
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            tags = p.get('tags', {})
            park_polygons.append({
                'id': f"way/{p['id']}",
                'tags': tags,
                'poly': poly,
                'name': tags.get('name', f"<unnamed {tags.get('leisure', '')}>"),
                'name_en': tags.get('name:en', ''),
                'leisure': tags.get('leisure', ''),
                'operator': tags.get('operator', ''),
                'access': tags.get('access', ''),
            })
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    tags = p.get('tags', {})
                    park_polygons.append({
                        'id': f"relation/{p['id']}",
                        'tags': tags,
                        'poly': poly,
                        'name': tags.get('name', f"<unnamed rel {tags.get('leisure', '')}>"),
                        'name_en': tags.get('name:en', ''),
                        'leisure': tags.get('leisure', ''),
                        'operator': tags.get('operator', ''),
                        'access': tags.get('access', ''),
                    })

print(f"Park polygon shells (including relation outers): {len(park_polygons)}")

# Build club polygons
club_polygons = []
for cl in clubs['elements']:
    if cl.get('type') == 'way' and 'geometry' in cl:
        poly = [(g['lat'], g['lon']) for g in cl['geometry']]
        if len(poly) >= 3:
            tags = cl.get('tags', {})
            club_polygons.append({
                'id': f"way/{cl['id']}",
                'tags': tags,
                'poly': poly,
                'name': tags.get('name', f"<unnamed club>"),
                'leisure': tags.get('leisure', ''),
                'sport': tags.get('sport', ''),
                'club': tags.get('club', ''),
                'access': tags.get('access', ''),
            })
    elif cl.get('type') == 'relation' and 'members' in cl:
        for m in cl.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    tags = cl.get('tags', {})
                    club_polygons.append({
                        'id': f"relation/{cl['id']}",
                        'tags': tags,
                        'poly': poly,
                        'name': tags.get('name', f"<unnamed club rel>"),
                        'leisure': tags.get('leisure', ''),
                        'sport': tags.get('sport', ''),
                        'club': tags.get('club', ''),
                        'access': tags.get('access', ''),
                    })

print(f"Club polygon shells: {len(club_polygons)}")

PUBLIC_PARK_LEISURE = {'park', 'recreation_ground', 'garden', 'common', 'nature_reserve'}

# Classify each in-circle tennis court
print("\n=== Court classification ===")
in_park_no_club = []
in_park_and_club = []
in_club_only = []
neither = []
for c in tennis_only:
    lat, lon = c['_lat'], c['_lon']
    tags = c.get('tags', {})
    matched_parks_public = []
    matched_parks_any = []
    for park in park_polygons:
        if point_in_polygon(lat, lon, park['poly']):
            matched_parks_any.append(park)
            if park['leisure'] in PUBLIC_PARK_LEISURE:
                matched_parks_public.append(park)
    matched_clubs = []
    for club in club_polygons:
        if point_in_polygon(lat, lon, club['poly']):
            matched_clubs.append(club)
    info = {
        'id': c['id'],
        'lat': lat,
        'lon': lon,
        'd': c['_dist_m'],
        'tags': tags,
        'parks_pub': matched_parks_public,
        'parks_any': matched_parks_any,
        'clubs': matched_clubs,
    }
    if matched_parks_public and not matched_clubs:
        in_park_no_club.append(info)
    elif matched_parks_public and matched_clubs:
        in_park_and_club.append(info)
    elif matched_clubs:
        in_club_only.append(info)
    else:
        neither.append(info)

def summarize(label, items):
    print(f"\n--- {label}: {len(items)} ---")
    # group by containing park-name
    groups = defaultdict(list)
    for it in items:
        if it['parks_pub']:
            key = it['parks_pub'][0]['name'] + ' [' + it['parks_pub'][0]['id'] + ']'
        elif it['parks_any']:
            key = '(non-public park) ' + it['parks_any'][0]['name']
        elif it['clubs']:
            key = '(club) ' + it['clubs'][0]['name']
        else:
            key = '(no polygon)'
        groups[key].append(it)
    for k in sorted(groups.keys(), key=lambda s: -len(groups[s])):
        items_k = groups[k]
        print(f"  [{len(items_k)}] {k}")
        for it in items_k[:8]:
            n = it['tags'].get('name', '') or it['tags'].get('name:en', '')
            print(f"      way/{it['id']} @ ({it['lat']:.5f},{it['lon']:.5f}) {it['d']:.0f}m name='{n}'")

summarize("IN-PARK (public-park leisure tag), NOT in club", in_park_no_club)
summarize("IN-PARK AND IN-CLUB (overlapping polygons)", in_park_and_club)
summarize("IN-CLUB only", in_club_only)
summarize("NEITHER (in circle but not in any park/club polygon)", neither)

print(f"\n=== OSM-strict (in public-park leisure tag, not in a club polygon): {len(in_park_no_club)} ===")

# Also dump all clubs in or near the circle, to understand exclusions
print("\n=== Club polygons near circle centre (within radius+500m) ===")
for cl in club_polygons:
    lats = [c[0] for c in cl['poly']]
    lons = [c[1] for c in cl['poly']]
    clat = sum(lats)/len(lats)
    clon = sum(lons)/len(lons)
    d = haversine(CENTRE_LAT, CENTRE_LON, clat, clon)
    if d <= RADIUS_M + 500:
        print(f"  {cl['id']} '{cl['name']}' leisure={cl['leisure']} sport={cl['sport']} club={cl['club']} access={cl['access']} dist={d:.0f}m")

# Park polygons containing courts (group together)
print("\n=== Parks containing in-circle tennis courts (any leisure tag) ===")
park_with_courts = defaultdict(int)
park_with_courts_tags = {}
for it in in_park_no_club + in_park_and_club:
    for p in it['parks_pub'] + it['parks_any']:
        park_with_courts[p['id']] += 1
        park_with_courts_tags[p['id']] = p
for pid, n in sorted(park_with_courts.items(), key=lambda kv: -kv[1]):
    p = park_with_courts_tags[pid]
    print(f"  [{n} courts] {pid} '{p['name']}' (en={p['name_en']!r}) leisure={p['leisure']} operator={p['operator']!r} access={p['access']!r}")

# Show neither-courts park context: nearest park within 50m
print("\n=== 'Neither' courts: nearest park polygon within 100m ===")
for it in neither:
    best = None
    best_d = 1e9
    for p in park_polygons:
        for pt in p['poly']:
            d = haversine(it['lat'], it['lon'], pt[0], pt[1])
            if d < best_d:
                best_d = d
                best = p
    if best:
        n = it['tags'].get('name', '') or it['tags'].get('name:en', '')
        print(f"  way/{it['id']} ({it['lat']:.5f},{it['lon']:.5f}) name='{n}' -> nearest park '{best['name']}' [{best['id']}] dist~{best_d:.0f}m leisure={best['leisure']}")
