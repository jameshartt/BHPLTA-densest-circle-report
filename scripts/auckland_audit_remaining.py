#!/usr/bin/env python3
"""For remaining unidentified clusters, do wider distance search."""
import json
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1 = math.radians(lat1); p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

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

with open(f'{BASE}/parks_auckland.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_auckland.json') as f:
    clubs = json.load(f)

all_polys = []
for src in (parks, clubs):
    for p in src['elements']:
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

# Look for remaining unmatched clusters with wider radius
test_points = [
    ('C4 Newmarket priv 7ct', -36.87747, 174.77614),
    ('C5 6ct', -36.88889, 174.76131),
    ('C7 5ct', -36.88303, 174.76790),
    ('C10 4 N', -36.86816, 174.76785),
    ('C15 3ct', -36.87894, 174.77798),
    ('C19 2priv', -36.89779, 174.77527),
    ('C29 2priv', -36.89713, 174.76995),
    ('C30 1', -36.87029, 174.77896),
    ('C48 1', -36.88028, 174.76961),
    ('C53 priv', -36.88070, 174.77106),
    ('C54 priv', -36.88299, 174.76986),
    ('C60 1', -36.88661, 174.78508),
    ('C67 1', -36.90104, 174.76273),
]

for label, lat, lon in test_points:
    print(f"\n{label} @ ({lat}, {lon}):")
    nearby = []
    for poly in all_polys:
        name = poly['tags'].get('name')
        if not name:
            continue
        mind = min(haversine(lat, lon, pt[0], pt[1]) for pt in poly['poly'])
        if mind < 600:
            nearby.append((mind, poly))
    nearby.sort(key=lambda x: x[0])
    for d, poly in nearby[:6]:
        t = poly['tags']
        print(f"  {d:5.0f}m {poly['id']}: {t.get('name')!r} leisure={t.get('leisure')!r} amenity={t.get('amenity')!r} landuse={t.get('landuse')!r} operator={t.get('operator')!r}")
