#!/usr/bin/env python3
"""Look at Cluster N — 2 courts inside a sports_centre tennis polygon (way/670713961)."""
import json
import math

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'

def haversine(a, b, c, d):
    R = 6371000.0
    p1 = math.radians(a); p2 = math.radians(c)
    dp = math.radians(c-a); dl = math.radians(d-b)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

with open(f'{BASE}/clubs_tokyo_23_wards.json') as f:
    clubs = json.load(f)

for cl in clubs['elements']:
    if cl.get('id') == 670713961:
        print("=== Club polygon way/670713961 ===")
        print(json.dumps(cl.get('tags', {}), ensure_ascii=False, indent=2))
        # show centroid
        if 'geometry' in cl:
            coords = cl['geometry']
            lat = sum(c['lat'] for c in coords) / len(coords)
            lon = sum(c['lon'] for c in coords) / len(coords)
            print(f"  centroid ({lat:.5f}, {lon:.5f}) dist from centre = {haversine(35.77557, 139.60057, lat, lon):.0f}m")
        break

# Also list any other club polygons with sport=tennis near centre
print("\n=== All sport=tennis or leisure=sports_centre near centre ===")
for cl in clubs['elements']:
    tags = cl.get('tags', {})
    if 'tennis' in str(tags.get('sport', '')).lower() or tags.get('club') == 'tennis':
        if cl.get('type') == 'way' and 'geometry' in cl:
            coords = cl['geometry']
            lat = sum(c['lat'] for c in coords) / len(coords)
            lon = sum(c['lon'] for c in coords) / len(coords)
        elif cl.get('type') == 'node':
            lat, lon = cl['lat'], cl['lon']
        else:
            continue
        d = haversine(35.77557, 139.60057, lat, lon)
        if d <= 3000:
            print(f"  {cl['type']}/{cl['id']} dist={d:.0f}m tags={tags}")
