#!/usr/bin/env python3
"""For each unmatched court cluster, find what's actually there in OSM (any nearby polygon, any name)."""
import json
import math

CENTRE_LAT = -36.88759
CENTRE_LON = 174.76536

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
with open(f'{BASE}/parks_auckland.json') as f:
    parks = json.load(f)

# All polygons regardless of leisure type
all_polys = []
for p in parks['elements']:
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

# Look up by cluster point (test points - one per unmatched cluster)
test_points = [
    ('Cluster 2 (NE bare)', -36.87597, 174.78172),
    ('Cluster 4 (Newmarket)', -36.87747, 174.77614),
    ('Cluster 5 (Wesley?)', -36.88889, 174.76131),
    ('Cluster 7 (Newmarket Park?)', -36.88303, 174.76790),
    ('Cluster 8 (Hospital?)', -36.88820, 174.78032),
    ('Cluster 10 (north Mt Eden)', -36.86816, 174.76785),
    ('Cluster 11 (Mt Eden)', -36.87307, 174.76649),
    ('Cluster 14 (Epsom S)', -36.90020, 174.77744),
    ('Cluster 15 (Domain?)', -36.87894, 174.77798),
    ('Cluster 16 (school?)', -36.89618, 174.76359),
    ('Cluster 17 (Parnell)', -36.88227, 174.78318),
    ('Cluster 18 (Epsom)', -36.89878, 174.77750),
    ('Cluster 19 (Epsom)', -36.89779, 174.77527),
    ('Cluster 20 (Epsom E)', -36.89741, 174.77928),
    ('Cluster 23 (Domain?)', -36.88676, 174.77930),
    ('Cluster 24 (Domain?)', -36.88811, 174.77968),
    ('Cluster 25 (Parnell E)', -36.88049, 174.78709),
    ('Cluster 26 (Parnell)', -36.88232, 174.77929),
    ('Cluster 27 (Domain)', -36.87840, 174.77990),
    ('Cluster 28 (Parnell SE)', -36.88241, 174.78768),
    ('Cluster 29 (Epsom)', -36.89713, 174.76995),
    ('Cluster 30', -36.87029, 174.77896),
    ('Cluster 32', -36.88162, 174.78103),
    ('Cluster 33', -36.90545, 174.77269),
    ('Cluster 34', -36.87869, 174.76874),
    ('Cluster 38', -36.87714, 174.76910),
    ('Cluster 48', -36.88028, 174.76961),
    ('Cluster 49', -36.90762, 174.76050),
    ('Cluster 50', -36.87843, 174.75917),
    ('Cluster 53', -36.88070, 174.77106),
    ('Cluster 54', -36.88299, 174.76986),
    ('Cluster 55 (W Eden)', -36.88443, 174.74601),
    ('Cluster 56 (N Mt Eden)', -36.86982, 174.76332),
    ('Cluster 60', -36.88661, 174.78508),
    ('Cluster 67', -36.90104, 174.76273),
]

for label, lat, lon in test_points:
    print(f"\n{label} @ ({lat}, {lon}):")
    matches = []
    for poly in all_polys:
        if point_in_polygon(lat, lon, poly['poly']):
            matches.append(poly)
    if matches:
        for m in matches:
            tags = m['tags']
            # Print all interesting tags
            relevant = {k: v for k, v in tags.items() if k in ('name', 'leisure', 'landuse', 'amenity', 'sport', 'operator', 'access', 'club', 'man_made', 'building', 'school', 'park:type', 'ownership')}
            print(f"  {m['id']}: {relevant}")
    else:
        # Find nearest named polygon
        nearest = None
        nearest_d = 1e9
        for poly in all_polys:
            if not poly['tags'].get('name'):
                continue
            for pt in poly['poly'][:20]:
                d = haversine(lat, lon, pt[0], pt[1])
                if d < nearest_d:
                    nearest_d = d
                    nearest = poly
        if nearest:
            print(f"  (no containing polygon; nearest named: {nearest['id']} {nearest['tags'].get('name')!r} @ {nearest_d:.0f}m, leisure={nearest['tags'].get('leisure')!r}, landuse={nearest['tags'].get('landuse')!r}, amenity={nearest['tags'].get('amenity')!r})")
