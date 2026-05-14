#!/usr/bin/env python3
"""Analyze Boston OSM data for the 2.34km circle ground-truth audit."""
import json
import math
from collections import defaultdict, Counter

CENTRE_LAT = 42.36992
CENTRE_LON = -71.12946
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

with open(f'{BASE}/courts_boston.json') as f:
    courts = json.load(f)
with open(f'{BASE}/parks_boston.json') as f:
    parks = json.load(f)
with open(f'{BASE}/clubs_boston.json') as f:
    clubs = json.load(f)

print(f"Total courts (Boston-scoped): {len(courts['elements'])}")
print(f"Total park polygons (Boston-scoped): {len(parks['elements'])}")
print(f"Total club elements: {len(clubs['elements'])}")

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

print(f"\nCourts within circle (Boston OSM scope only): {len(in_circle)}")

park_polygons = []
for p in parks['elements']:
    if p.get('type') == 'way' and 'geometry' in p:
        poly = [(g['lat'], g['lon']) for g in p['geometry']]
        if len(poly) >= 3:
            tags = p.get('tags', {})
            park_polygons.append({
                'id': p['id'],
                'tags': tags,
                'poly': poly,
                'name': tags.get('name', f"<unnamed {tags.get('leisure', '')}>"),
                'leisure': tags.get('leisure', '')
            })
    elif p.get('type') == 'relation' and 'members' in p:
        for m in p.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                poly = [(g['lat'], g['lon']) for g in m['geometry']]
                if len(poly) >= 3:
                    tags = p.get('tags', {})
                    park_polygons.append({
                        'id': f"rel:{p['id']}",
                        'tags': tags,
                        'poly': poly,
                        'name': tags.get('name', f"<unnamed rel {tags.get('leisure', '')}>"),
                        'leisure': tags.get('leisure', '')
                    })

print(f"Park polygon shells (including relation outers): {len(park_polygons)}")

PUBLIC_PARK_LEISURE = {'park', 'recreation_ground', 'garden', 'common', 'nature_reserve'}
venue_counts = defaultdict(lambda: {'count': 0, 'ids': [], 'tags_samples': [], 'in_public_park': False})

for c in in_circle:
    lat, lon = c['_lat'], c['_lon']
    tags = c.get('tags', {})
    name = tags.get('name', '') or tags.get('operator', '')
    sport = tags.get('sport', '')
    leisure = tags.get('leisure', '')
    access = tags.get('access', '')
    matched_parks = []
    for park in park_polygons:
        if park['leisure'] in PUBLIC_PARK_LEISURE:
            if point_in_polygon(lat, lon, park['poly']):
                matched_parks.append(park)
    in_public = bool(matched_parks)
    park_name = matched_parks[0]['name'] if matched_parks else '(no public park polygon)'
    key = park_name
    venue_counts[key]['count'] += 1
    venue_counts[key]['ids'].append(c['id'])
    venue_counts[key]['tags_samples'].append({
        'id': c['id'],
        'name': name,
        'sport': sport,
        'leisure': leisure,
        'access': access,
        'lat': round(lat, 5),
        'lon': round(lon, 5),
        'dist_m': round(c['_dist_m'], 1),
    })
    venue_counts[key]['in_public_park'] = in_public

print("\n--- Venue breakdown (court centroid -> containing public-park polygon) ---")
for venue, info in sorted(venue_counts.items(), key=lambda kv: -kv[1]['count']):
    print(f"\n{venue}: {info['count']} courts, in_public_park={info['in_public_park']}")
    for t in info['tags_samples']:
        print(f"  way/{t['id']}: name={t['name']!r}, sport={t['sport']!r}, access={t['access']!r}, dist={t['dist_m']}m @ {t['lat']},{t['lon']}")

tennis_only = [c for c in in_circle if 'tennis' in c.get('tags', {}).get('sport', '').lower()]
print(f"\nCourts in circle with sport contains 'tennis': {len(tennis_only)}")

strict_count = sum(info['count'] for info in venue_counts.values() if info['in_public_park'])
print(f"\nOSM-strict public-park count: {strict_count}")

sports = Counter(c.get('tags', {}).get('sport', '<none>') for c in in_circle)
print(f"\nSport tags within circle: {dict(sports)}")

print(f"\nFull disc area: {math.pi * (RADIUS_M/1000)**2:.3f} km²")

# Clubs in circle
print("\n--- Clubs (sports_centre / club=tennis) within 3 km of centre ---")
for cl in clubs['elements']:
    lat, lon = centroid(cl)
    if lat is None:
        continue
    d = haversine(CENTRE_LAT, CENTRE_LON, lat, lon)
    if d <= 3000:
        tags = cl.get('tags', {})
        name = tags.get('name', '')
        sport = tags.get('sport', '')
        club = tags.get('club', '')
        leisure = tags.get('leisure', '')
        access = tags.get('access', '')
        print(f"  {cl['type']}/{cl['id']}: {name!r} leisure={leisure!r} sport={sport!r} club={club!r} access={access!r} dist={d:.0f}m")
