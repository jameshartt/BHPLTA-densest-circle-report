#!/usr/bin/env python3
"""Identify the park polygon containing the 18 Daly Field courts."""
import json
import math

CENTRE_LAT = 42.36992
CENTRE_LON = -71.12946

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
with open(f'{BASE}/parks_boston.json') as f:
    parks = json.load(f)

# What polygon(s) contain the centre?
candidates = []
for p in parks['elements']:
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3 and point_in_polygon(CENTRE_LAT, CENTRE_LON, poly):
            candidates.append(('way', p['id'], p.get('tags', {}), None))
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3 and point_in_polygon(CENTRE_LAT, CENTRE_LON, poly):
                    candidates.append(('relation', p['id'], p.get('tags', {}), m.get('ref')))

print(f"Polygons containing centre ({CENTRE_LAT},{CENTRE_LON}):")
for t, oid, tags, member_ref in candidates:
    print(f"  {t}/{oid} (member way:{member_ref}) tags={tags}")
