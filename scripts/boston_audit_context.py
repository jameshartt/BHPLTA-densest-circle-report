#!/usr/bin/env python3
"""Look up nearby context features (clubs, parks, leisure tags) for each non-public-park court."""
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
            return sum(c['lat'] for c in coords)/len(coords), sum(c['lon'] for c in coords)/len(coords)
    return None, None

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'
with open(f'{BASE}/parks_boston.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_boston.json') as f:
    clubs = json.load(f)
with open(f'{BASE}/courts_boston.json') as f:
    courts = json.load(f)

# Group the 9 outliers
groups = {
    "Group A — south Brighton (clay, 2 courts)": [(42.35089, -71.13899), (42.35077, -71.13892)],
    "Group B — east bank (artificial turf, 3 courts)": [(42.35415, -71.11973), (42.35411, -71.11956), (42.35409, -71.11939)],
    "Group C — just SE of centre (4 courts)": [(42.36633, -71.12411), (42.36627, -71.12396), (42.36605, -71.12431), (42.36599, -71.12415)],
}

for label, pts in groups.items():
    print(f"\n========== {label} ==========")
    cx = sum(p[0] for p in pts)/len(pts)
    cy = sum(p[1] for p in pts)/len(pts)
    print(f"  Centroid: {cx:.5f}, {cy:.5f}")
    # Nearby features < 300m
    nearby = []
    for src, data in [('parks', parks), ('clubs', clubs)]:
        for e in data['elements']:
            lat, lon = centroid(e)
            if lat is None:
                continue
            d = haversine(cx, cy, lat, lon)
            if d <= 350:
                t = e.get('tags', {})
                nearby.append((d, src, e.get('type'), e['id'], t))
    nearby.sort()
    for d, src, typ, oid, t in nearby[:30]:
        name = t.get('name', '')
        keys_of_interest = {k: v for k, v in t.items() if k in ('leisure', 'landuse', 'amenity', 'operator', 'access', 'sport', 'name', 'club', 'school', 'university', 'addr:city')}
        print(f"  [{d:6.1f}m] {src}: {typ}/{oid} {keys_of_interest}")
