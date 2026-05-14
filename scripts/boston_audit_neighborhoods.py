#!/usr/bin/env python3
"""Look at all parks (any leisure) and clubs within the circle for context.
Also check whether Daly Field area is well-tagged."""
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

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'
with open(f'{BASE}/parks_boston.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_boston.json') as f:
    clubs = json.load(f)

# Look at the Charles River Reservation polygon
print("=== Park polygons near centre (within 250m) tagged Charles River Reservation or similar ===")
for p in parks['elements']:
    t = p.get('tags', {})
    name = t.get('name', '')
    if 'charles' in name.lower() or 'daly' in name.lower():
        lat, lon = centroid(p)
        if lat is None:
            continue
        d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
        print(f"  {p['type']}/{p['id']} {t} dist={d:.0f}m")

# All named parks in circle
print("\n=== All named parks/leisure inside circle ===")
seen = set()
for p in parks['elements']:
    t = p.get('tags', {})
    name = t.get('name', '')
    leisure = t.get('leisure', '')
    if not name or not leisure:
        continue
    lat, lon = centroid(p)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= RADIUS_M:
        key = (name, leisure)
        if key in seen:
            continue
        seen.add(key)
        access = t.get('access', '')
        operator = t.get('operator', '')
        print(f"  [{d:6.0f}m] {leisure:18s} access={access!r:10s} name={name!r} op={operator!r}")

# All clubs in circle
print("\n=== All sports_centre / club elements in circle ===")
for cl in clubs['elements']:
    lat, lon = centroid(cl)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= RADIUS_M:
        t = cl.get('tags', {})
        print(f"  [{d:6.0f}m] {cl['type']}/{cl['id']} name={t.get('name','')!r} sport={t.get('sport','')!r} access={t.get('access','')!r}")
