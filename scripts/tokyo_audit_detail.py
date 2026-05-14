#!/usr/bin/env python3
"""Deeper Tokyo audit: dump all tags and pinpoint each cluster of courts."""
import json
import math
from collections import defaultdict

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

with open(f'{BASE}/courts_tokyo_23_wards.json') as f:
    courts = json.load(f)
with open(f'{BASE}/parks_tokyo_23_wards.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_tokyo_23_wards.json') as f:
    clubs = json.load(f)

# Build park polygons (any leisure)
park_polygons = []
for p in parks['elements']:
    tags = p.get('tags', {})
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            park_polygons.append({'id': f"way/{p['id']}", 'tags': tags, 'poly': poly})
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    park_polygons.append({'id': f"relation/{p['id']}", 'tags': tags, 'poly': poly})

club_polygons = []
for cl in clubs['elements']:
    tags = cl.get('tags', {})
    if cl.get('type') == 'way' and 'geometry' in cl:
        poly = [(g['lat'], g['lon']) for g in cl['geometry']]
        if len(poly) >= 3:
            club_polygons.append({'id': f"way/{cl['id']}", 'tags': tags, 'poly': poly})
    elif cl.get('type') == 'relation' and 'members' in cl:
        for m in cl.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    club_polygons.append({'id': f"relation/{cl['id']}", 'tags': tags, 'poly': poly})

PUBLIC_PARK_LEISURE = {'park', 'recreation_ground', 'garden', 'common', 'nature_reserve'}

# Cluster in-circle tennis courts by tight spatial grouping (~150m)
in_circle = []
for c in courts['elements']:
    lat, lon = centroid(c)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= RADIUS_M and 'tennis' in str(c.get('tags', {}).get('sport', '')).lower():
        c['_lat'] = lat; c['_lon'] = lon; c['_dist_m'] = d
        in_circle.append(c)

# Simple clustering by union-find on courts <=200m apart
parent = list(range(len(in_circle)))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(x, y):
    parent[find(x)] = find(y)
for i in range(len(in_circle)):
    for j in range(i+1, len(in_circle)):
        d = haversine(in_circle[i]['_lat'], in_circle[i]['_lon'], in_circle[j]['_lat'], in_circle[j]['_lon'])
        if d <= 200:
            union(i, j)

groups = defaultdict(list)
for i in range(len(in_circle)):
    groups[find(i)].append(in_circle[i])

# Find nearest park (any leisure) for each cluster (point-in-polygon first, then nearest)
def nearest_park_for(lat, lon, prefer_public=True):
    # First: containing polygon
    for pp in park_polygons:
        if point_in_polygon(lat, lon, pp['poly']):
            return ('contains', pp, 0)
    # Then nearest park boundary
    best = None; best_d = 1e9
    for pp in park_polygons:
        for pt in pp['poly']:
            d = haversine(lat, lon, pt[0], pt[1])
            if d < best_d:
                best_d = d; best = pp
    return ('nearest', best, best_d)

print(f"Total clusters of in-circle tennis courts: {len(groups)}")
print()
for gid, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    members.sort(key=lambda c: c['_dist_m'])
    n = len(members)
    clat = sum(c['_lat'] for c in members) / n
    clon = sum(c['_lon'] for c in members) / n
    cdist = haversine(CENTRE_LAT, CENTRE_LON, clat, clon)
    # find park
    rel, park, pd = nearest_park_for(clat, clon)
    # check club polygon containment
    in_clubs = []
    for cl in club_polygons:
        if point_in_polygon(clat, clon, cl['poly']):
            in_clubs.append(cl)
    print(f"=== Cluster ({n} courts) centred ({clat:.5f},{clon:.5f}) dist_centre={cdist:.0f}m ===")
    if park:
        ptags = park['tags']
        print(f"  Park: {rel} '{ptags.get('name','')}' (en={ptags.get('name:en','')!r}) id={park['id']} "
              f"leisure={ptags.get('leisure','')} operator={ptags.get('operator','')!r} "
              f"access={ptags.get('access','')!r} fee={ptags.get('fee','')!r} dist={pd:.0f}m")
        # Show all interesting tags
        keep = {k: v for k, v in ptags.items() if k in
                ('name','name:en','name:ja','leisure','operator','operator:en','access','fee',
                 'website','description','official_name','wikidata','wikipedia','addr:ward',
                 'addr:city','addr:state','park:type','park_type')}
        if keep:
            print(f"  Park tags: {keep}")
    else:
        print("  No park found")
    if in_clubs:
        for cl in in_clubs:
            print(f"  CLUB-CONTAIN: {cl['id']} {cl['tags']}")
    # Court tags
    sample_tags = {}
    for c in members:
        for k, v in c.get('tags', {}).items():
            sample_tags[k] = v
    print(f"  Court tag union: {sample_tags}")
    for c in members[:3]:
        print(f"    way/{c['id']} @ ({c['_lat']:.5f},{c['_lon']:.5f}) {c['_dist_m']:.0f}m surface={c.get('tags',{}).get('surface','')}")
    print()
