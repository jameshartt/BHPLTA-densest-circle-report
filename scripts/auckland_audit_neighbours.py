#!/usr/bin/env python3
"""Find nearest named features (schools, clubs, sports_centres) for each cluster point."""
import json
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1 = math.radians(lat1); p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
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
            return sum(c['lat'] for c in coords) / len(coords), sum(c['lon'] for c in coords) / len(coords)
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

# Load all three files to look for schools and named buildings
with open(f'{BASE}/parks_auckland.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_auckland.json') as f:
    clubs = json.load(f)

# Build all polys
all_polys = []
for p in parks['elements'] + clubs['elements']:
    tags = p.get('tags', {})
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            all_polys.append({'id': f'way/{p["id"]}', 'tags': tags, 'poly': poly})
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    all_polys.append({'id': f'rel/{p["id"]}', 'tags': tags, 'poly': poly})

# Clusters of interest
test_points = [
    ('C2 (NE bare 11)', -36.87597, 174.78172),
    ('C4 (Newmarket 7 priv)', -36.87747, 174.77614),
    ('C5 (6 ct)', -36.88889, 174.76131),
    ('C7 (5 ct)', -36.88303, 174.76790),
    ('C8 (5 ct)', -36.88820, 174.78032),
    ('C10 (4 N)', -36.86816, 174.76785),
    ('C11 (4 Mt Eden)', -36.87307, 174.76649),
    ('C14 (3 Epsom)', -36.90020, 174.77744),
    ('C15 (3)', -36.87894, 174.77798),
    ('C16 (3 customers)', -36.89618, 174.76359),
    ('C17 (3)', -36.88227, 174.78318),
    ('C18 (2 priv)', -36.89878, 174.77750),
    ('C19 (2 priv)', -36.89779, 174.77527),
    ('C20 (2 priv)', -36.89741, 174.77928),
    ('C23 (2)', -36.88676, 174.77930),
    ('C24 (2)', -36.88811, 174.77968),
    ('C25 (2)', -36.88049, 174.78709),
    ('C26 (2 priv)', -36.88232, 174.77929),
    ('C27 (2)', -36.87840, 174.77990),
    ('C28 (2)', -36.88241, 174.78768),
    ('C29 (2 priv)', -36.89713, 174.76995),
    ('C32', -36.88162, 174.78103),
    ('C34', -36.87869, 174.76874),
    ('C48 single', -36.88028, 174.76961),
    ('C50', -36.87843, 174.75917),
    ('C53 priv', -36.88070, 174.77106),
    ('C54 priv', -36.88299, 174.76986),
    ('C55 W', -36.88443, 174.74601),
    ('C56 N', -36.86982, 174.76332),
    ('C60 (1)', -36.88661, 174.78508),
    ('C67 (1)', -36.90104, 174.76273),
    ('C49 (1)', -36.90762, 174.76050),
    ('C30 (1)', -36.87029, 174.77896),
    ('C33 (1)', -36.90545, 174.77269),
    ('C38 priv', -36.87714, 174.76910),
]

for label, lat, lon in test_points:
    matches = []
    for poly in all_polys:
        if point_in_polygon(lat, lon, poly['poly']):
            matches.append(poly)
    # Show all containing polygons regardless of type
    print(f"\n{label} @ ({lat}, {lon}):")
    if matches:
        for m in matches:
            t = m['tags']
            print(f"  CONTAINS {m['id']}: name={t.get('name')!r} leisure={t.get('leisure')!r} amenity={t.get('amenity')!r} landuse={t.get('landuse')!r} sport={t.get('sport')!r} access={t.get('access')!r} operator={t.get('operator')!r}")
    # Closest 3 named polys within 200m by point-list
    candidates = []
    for poly in all_polys:
        name = poly['tags'].get('name')
        if not name:
            continue
        # min distance to any vertex
        mind = min(haversine(lat, lon, pt[0], pt[1]) for pt in poly['poly'][::max(1, len(poly['poly'])//30)])
        if mind < 250:
            candidates.append((mind, poly))
    candidates.sort(key=lambda x: x[0])
    for d, poly in candidates[:4]:
        t = poly['tags']
        print(f"   NEAR(<{d:.0f}m) {poly['id']}: {t.get('name')!r} leisure={t.get('leisure')!r} amenity={t.get('amenity')!r} operator={t.get('operator')!r}")
