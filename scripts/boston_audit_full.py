#!/usr/bin/env python3
"""List every tennis court tagged in Boston within 5km of centre for context."""
import json
import math

CENTRE_LAT = 42.36992
CENTRE_LON = -71.12946

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
with open(f'{BASE}/courts_boston.json') as f:
    courts = json.load(f)

within3 = []
for c in courts['elements']:
    lat, lon = centroid(c)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= 3500:
        within3.append((d, c['id'], lat, lon, c.get('tags', {})))

within3.sort()
print(f"All tennis courts within 3.5 km of centre ({len(within3)}):")
for d, oid, lat, lon, t in within3:
    surface = t.get('surface', '')
    lit = t.get('lit', '')
    print(f"  [{d:6.1f}m] way/{oid} ({lat:.5f},{lon:.5f}) surface={surface!r} lit={lit!r}")
