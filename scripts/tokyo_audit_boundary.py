#!/usr/bin/env python3
"""Identify each tennis-court cluster's containing municipality (ward / city).

We look for the nearest 'place' / 'admin' related polygon, plus we use the
park's `addr:city` / `addr:state` tags if present. We also check whether the
ward-level boundary (e.g. 練馬区, 板橋区) is present in the parks dataset.
"""
import json
import math
from collections import defaultdict, Counter

CENTRE_LAT = 35.77557
CENTRE_LON = 139.60057
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
            return (sum(c['lat'] for c in coords) / len(coords),
                    sum(c['lon'] for c in coords) / len(coords))
    return None, None

def point_in_polygon(lat, lon, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        yi, xi = poly[i]; yj, xj = poly[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'

with open(f'{BASE}/parks_tokyo_23_wards.json') as f:
    parks = json.load(f)

# Distribution of addr:city in parks near centre
city_counts = Counter()
parks_near = []
for p in parks['elements']:
    tags = p.get('tags', {})
    lat, lon = centroid(p)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= RADIUS_M + 200:
        addr_city = tags.get('addr:city', '')
        addr_state = tags.get('addr:state', '')
        if addr_city:
            city_counts[addr_city] += 1
        parks_near.append({
            'id': p['id'], 'name': tags.get('name', ''), 'addr_city': addr_city,
            'addr_state': addr_state, 'operator': tags.get('operator', ''), 'd': d,
        })

print("=== Park addr:city counts within RADIUS+200m ===")
for city, n in city_counts.most_common():
    print(f"  {city}: {n} parks")

# Show parks with addr:state set
state_counts = Counter()
for p in parks_near:
    if p['addr_state']:
        state_counts[p['addr_state']] += 1
print("\n=== Park addr:state counts ===")
for s, n in state_counts.most_common():
    print(f"  {s}: {n} parks")

# Operator counts (likely 東京都, 練馬区, 板橋区, 朝霞市, 和光市 etc.)
op_counts = Counter()
for p in parks_near:
    if p['operator']:
        op_counts[p['operator']] += 1
print("\n=== Park operator counts ===")
for op, n in op_counts.most_common():
    print(f"  {op}: {n} parks")

# Try to find admin boundaries: relations with admin_level / boundary in any data
print("\n=== Look for boundary polygons in parks file ===")
n_boundary = 0
for p in parks['elements']:
    tags = p.get('tags', {})
    if 'boundary' in tags or 'admin_level' in tags:
        n_boundary += 1
        if n_boundary <= 30:
            print(f"  {p['type']}/{p['id']} {dict(list(tags.items())[:8])}")
print(f"Total boundary-like in parks file: {n_boundary}")

# Each cluster centroid → identify city by nearest park's addr:city
cluster_centres = [
    ('Cluster A', 35.77938, 139.58501, 11, '希望が丘公園 area / 大泉学園町'),
    ('Cluster B', 35.77406, 139.61420, 10, '和光市運動場'),
    ('Cluster C', 35.76921, 139.61509, 7, 'south of 和光市運動場 / 稲荷山憩いの森'),
    ('Cluster D', 35.77487, 139.60111, 7, '大泉さくら運動公園'),
    ('Cluster E', 35.79438, 139.59044, 6, '青葉台公園 (Asaka)'),
    ('Cluster F', 35.78699, 139.59116, 6, '朝霞中央公園 (Asaka Central Park)'),
    ('Cluster G', 35.78089, 139.61071, 5, 'NW corner / 和光市'),
    ('Cluster H', 35.75931, 139.58782, 4, '西本村憩いの森 (south)'),
    ('Cluster I', 35.79165, 139.59191, 4, '朝霞シンボルロード (Asaka)'),
    ('Cluster J', 35.76282, 139.59817, 3, '?? unnamed park (south)'),
    ('Cluster K', 35.77808, 139.59026, 3, '大泉学園町希望が丘公園 east'),
    ('Cluster L', 35.78091, 139.59598, 3, '和光樹林公園 (Wako Jurin)'),
    ('Cluster M', 35.79212, 139.60449, 3, 'あけぼの公園 (Asaka)'),
    ('Cluster N', 35.76735, 139.62403, 2, 'tennis club polygon'),
    ('Cluster O', 35.77322, 139.60456, 2, 'unnamed park'),
    ('Cluster P', 35.75632, 139.59751, 2, 'びくに公園'),
    ('Cluster Q', 35.77681, 139.59437, 1, '大泉中央公園 (Oizumi Chuo)'),
    ('Cluster R', 35.78959, 139.58485, 1, 'near 青葉台 (Asaka)'),
    ('Cluster S', 35.78230, 139.59096, 1, '希望が丘 area'),
]

# Park polygons (only with addr:city or operator) — try to find which one contains each cluster
park_polys = []
for p in parks['elements']:
    tags = p.get('tags', {})
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            park_polys.append({'id': f"way/{p['id']}", 'tags': tags, 'poly': poly})
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    park_polys.append({'id': f"relation/{p['id']}", 'tags': tags, 'poly': poly})

print("\n=== Cluster -> nearest park addr:city heuristic ===")
for name, lat, lon, n, label in cluster_centres:
    # Find nearest park with addr:city or operator within 600m
    best = None; best_d = 1e9
    for pp in park_polys:
        tags = pp['tags']
        if not (tags.get('addr:city') or tags.get('operator') or tags.get('addr:state')):
            continue
        # use poly centroid
        plat = sum(pt[0] for pt in pp['poly']) / len(pp['poly'])
        plon = sum(pt[1] for pt in pp['poly']) / len(pp['poly'])
        d = haversine(lat, lon, plat, plon)
        if d < best_d:
            best_d = d; best = pp
    if best:
        t = best['tags']
        print(f"  {name} ({n}) {label}: nearest tagged park '{t.get('name','')}' addr:city={t.get('addr:city','')} state={t.get('addr:state','')} op={t.get('operator','')!r} d={best_d:.0f}m")
    else:
        print(f"  {name} ({n}) {label}: no tagged park near")
