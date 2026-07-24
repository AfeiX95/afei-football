#!/usr/bin/env python3
"""Dump raw API structure to understand field names."""
import json
import urllib.request

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode('utf-8'))

# Print the top-level keys
print("=== Top-level keys ===")
print(list(data.get('value', {}).keys()) if isinstance(data.get('value'), dict) else "value not a dict")

match_days = data.get('value', {}).get('matchInfoList', [])
print(f"\n=== Match days: {len(match_days)} ===")

for day_idx, day in enumerate(match_days):
    print(f"\n--- Day {day_idx}: date={day.get('date','?')} ---")
    print(f"  Keys: {list(day.keys())}")
    subs = day.get('subMatchList', [])
    for sub_idx, m in enumerate(subs):
        print(f"\n  Match {sub_idx}:")
        # Print ALL keys
        for k, v in m.items():
            if isinstance(v, str):
                print(f"    {k} = '{v}'")
            elif isinstance(v, (int, float)):
                print(f"    {k} = {v}")
            elif isinstance(v, dict):
                print(f"    {k} = (dict with {len(v)} keys)")
            elif isinstance(v, list):
                print(f"    {k} = (list of {len(v)} items)")
            else:
                print(f"    {k} = {type(v).__name__}: {v}")
        break  # Just first match for inspection
    if len(subs) > 0:
        break
