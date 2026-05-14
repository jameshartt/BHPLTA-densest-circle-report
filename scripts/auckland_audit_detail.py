#!/usr/bin/env python3
"""Detailed lookup for Auckland — find named courts, group unmatched clusters by proximity, look up park polygons that contain them with all leisure tags."""
import json
import math
from collections import defaultdict

CENTRE_LAT = -36.88759
CENTRE_LON = 174.76536
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

with open(f'{BASE}/courts_auckland.json') as f:
    courts = json.load(f)
with open(f'{BASE}/parks_auckland.json') as f:
    parks = json.load(f)

# Build all park-like polygons (any leisure tag, plus landuse=recreation_ground)
all_polygons = []
for p in parks['elements']:
    tags = p.get('tags', {})
    name = tags.get('name', '')
    leisure = tags.get('leisure', '')
    landuse = tags.get('landuse', '')
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            all_polygons.append({
                'id': f'way/{p["id"]}',
                'name': name,
                'leisure': leisure,
                'landuse': landuse,
                'tags': tags,
                'poly': poly,
            })
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    all_polygons.append({
                        'id': f'rel/{p["id"]}',
                        'name': name,
                        'leisure': leisure,
                        'landuse': landuse,
                        'tags': tags,
                        'poly': poly,
                    })

# Get courts in circle, look up ALL containing polygons
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

# Cluster courts by proximity (within 80m)
def cluster_courts(courts, threshold=80):
    used = [False] * len(courts)
    clusters = []
    for i, c in enumerate(courts):
        if used[i]:
            continue
        used[i] = True
        cluster = [c]
        for j in range(i+1, len(courts)):
            if used[j]:
                continue
            for cc in cluster:
                if haversine(cc['_lat'], cc['_lon'], courts[j]['_lat'], courts[j]['_lon']) <= threshold:
                    cluster.append(courts[j])
                    used[j] = True
                    break
        clusters.append(cluster)
    return clusters

clusters = cluster_courts(in_circle)
print(f"Found {len(clusters)} clusters of courts within circle\n")

for ci, cluster in enumerate(sorted(clusters, key=lambda cl: -len(cl))):
    # Compute centroid
    clat = sum(c['_lat'] for c in cluster) / len(cluster)
    clon = sum(c['_lon'] for c in cluster) / len(cluster)
    # Look up containing polygons
    matches = []
    for poly in all_polygons:
        if point_in_polygon(clat, clon, poly['poly']):
            matches.append(poly)
    # Get tags
    sample = cluster[0]
    tags = sample.get('tags', {})
    access_tags = set(c.get('tags', {}).get('access', '') for c in cluster)
    name_tags = set(c.get('tags', {}).get('name', '') for c in cluster if c.get('tags', {}).get('name'))
    operator_tags = set(c.get('tags', {}).get('operator', '') for c in cluster if c.get('tags', {}).get('operator'))
    print(f"\n=== Cluster {ci+1}: {len(cluster)} courts @ ({clat:.5f}, {clon:.5f}) dist={haversine(CENTRE_LAT, CENTRE_LON, clat, clon):.0f}m ===")
    print(f"  access tags: {access_tags}")
    if name_tags:
        print(f"  name tags: {name_tags}")
    if operator_tags:
        print(f"  operator tags: {operator_tags}")
    print(f"  court IDs: {[c['id'] for c in cluster[:6]]}{'...' if len(cluster) > 6 else ''}")
    if matches:
        for m in matches:
            print(f"  CONTAINED in {m['id']}: name={m['name']!r} leisure={m['leisure']!r} landuse={m['landuse']!r}")
            interesting = {k:v for k,v in m['tags'].items() if k in ('access', 'operator', 'sport', 'club', 'amenity', 'park:type', 'ownership')}
            if interesting:
                print(f"     extra: {interesting}")
    else:
        print(f"  (no containing polygon — bare court)")
