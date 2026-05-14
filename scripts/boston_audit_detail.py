#!/usr/bin/env python3
"""Deep-dive on the 9 in-circle courts that are NOT inside a public-park polygon."""
import json
import math

CENTRE_LAT = 42.36992
CENTRE_LON = -71.12946
RADIUS_M = 2336.78

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
with open(f'{BASE}/courts_boston.json') as f:
    courts = json.load(f)
with open(f'{BASE}/parks_boston.json') as f:
    parks = json.load(f)

target_ids = {101674275, 101674277, 619598470, 619598471, 619598472,
              1358169548, 1358169549, 1358169550, 1358169551}

# All park polygons (any leisure), to see what they ARE inside
all_polygons = []
for p in parks['elements']:
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            all_polygons.append({'src': f"way/{p['id']}", 'tags': p.get('tags', {}), 'poly': poly})
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    all_polygons.append({'src': f"rel/{p['id']}", 'tags': p.get('tags', {}), 'poly': poly})

print(f"All polygons available: {len(all_polygons)}\n")

for c in courts['elements']:
    if c['id'] not in target_ids:
        continue
    lat, lon = centroid(c)
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    print(f"\n=== way/{c['id']} @ ({lat:.5f},{lon:.5f}), {d:.0f}m from centre ===")
    print(f"  tags: {c.get('tags', {})}")
    print("  Containing polygons (any leisure tag):")
    for pg in all_polygons:
        if point_in_polygon(lat, lon, pg['poly']):
            t = pg['tags']
            print(f"    {pg['src']} leisure={t.get('leisure','')} landuse={t.get('landuse','')} name={t.get('name','')!r} operator={t.get('operator','')!r} amenity={t.get('amenity','')!r}")
