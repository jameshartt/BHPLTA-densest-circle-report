#!/usr/bin/env python3
"""Verify the 18 Daly Field court tags - any padel, any with access restrictions?"""
import json

BASE = '/home/jameshartt/Development/Tennis/tennis-courts-analysis/data/raw/overpass/global'
with open(f'{BASE}/courts_boston.json') as f:
    courts = json.load(f)

daly_ids = list(range(722644397, 722644415))
for c in courts['elements']:
    if c['id'] in daly_ids:
        print(f"way/{c['id']}: {c.get('tags', {})}")
