"""
Build transmission_master_jamali.csv + GeoJSON dari OSM lines.

Filter:
  - Hanya transmisi tegangan >= 70 kV (exclude distribusi 20 kV)
  - Garis di Jamali (exclude Lampung/Sumatera)

Output:
  - data/processed/transmission_master_jamali.csv
  - data/processed/transmission_jamali.geojson
"""
import re
import json
import csv
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

ROOT = Path("/sessions/pensive-beautiful-bohr/mnt/Indonesia Power Map")
LINES_GJ = ROOT / "data/geojson/indonesia_lines.geojson"
OUT_CSV = ROOT / "data/processed/transmission_master_jamali.csv"
OUT_GJ = ROOT / "data/processed/transmission_jamali.geojson"

# Minimum transmission voltage (kV). Filter out distribusi <70 kV.
MIN_VOLTAGE_KV = 70

def parse_voltages_kv(v):
    """OSM voltage tag (V) → list of kV. '500000;150000' → [500, 150]"""
    if not v: return []
    out = []
    for p in re.split(r'[;,]', str(v)):
        p = p.strip()
        if p.isdigit():
            out.append(int(p) / 1000)
    return out

def haversine_km(coords):
    """Length of LineString in km."""
    total = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i][:2]
        lon2, lat2 = coords[i+1][:2]
        dlon = radians(lon2 - lon1)
        dlat = radians(lat2 - lat1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        total += 2 * 6371 * asin(sqrt(a))
    return total

def in_jamali_centroid(coords):
    """Centroid-based filter: avg lat/lon harus dalam Jamali."""
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    if not (-9.0 <= avg_lat <= -5.3 and 105.0 <= avg_lon <= 115.8):
        return False
    # Exclude Lampung/Sumatera (sebelah barat Selat Sunda)
    if avg_lat > -6.0 and avg_lon < 105.7:
        return False
    return True

# Color & weight rule per voltage class
def voltage_class(max_kv):
    if max_kv >= 500: return ('500 kV', '#d62728', 3.0)
    if max_kv >= 275: return ('275 kV', '#9467bd', 2.5)
    if max_kv >= 150: return ('150 kV', '#1f77b4', 1.8)
    if max_kv >= 70:  return ('70 kV',  '#2ca02c', 1.2)
    return ('lain', '#999', 1.0)


def run():
    gj = json.load(open(LINES_GJ))
    rows = []
    features = []
    next_id = 1
    total_len_by_class = {'500 kV': 0, '275 kV': 0, '150 kV': 0, '70 kV': 0, 'lain': 0}
    count_by_class = {k: 0 for k in total_len_by_class}

    skipped_low_voltage = 0
    skipped_no_voltage = 0
    skipped_outside_jamali = 0

    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'LineString':
            continue
        coords = g['coordinates']
        if not in_jamali_centroid(coords):
            skipped_outside_jamali += 1
            continue
        props = f.get('properties', {})
        vs = parse_voltages_kv(props.get('voltage'))
        if not vs:
            skipped_no_voltage += 1
            continue
        max_v = max(vs)
        if max_v < MIN_VOLTAGE_KV:
            skipped_low_voltage += 1
            continue
        length_km = haversine_km(coords)
        vclass, color, weight = voltage_class(max_v)
        count_by_class[vclass] += 1
        total_len_by_class[vclass] += length_km

        # OSM voltage as raw string
        vstr = props.get('voltage', '')
        row = {
            'id': f'TRM-JMB-{next_id:04d}',
            'voltage_class': vclass,
            'voltage_kv_max': max_v,
            'voltage_kv_all': ';'.join(str(int(v)) for v in vs),
            'length_km': round(length_km, 3),
            'osm_id': props.get('@id', ''),
            'osm_voltage': vstr,
            'source_id': 'OSM-overpass',
        }
        rows.append(row)
        # Feature with line + styling props
        features.append({
            'type': 'Feature',
            'geometry': g,
            'properties': {**row, 'color': color, 'weight': weight}
        })
        next_id += 1

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Write GeoJSON
    with open(OUT_GJ, 'w') as fh:
        json.dump({'type': 'FeatureCollection', 'features': features}, fh, ensure_ascii=False)

    print(f"OSM lines processed:")
    print(f"  Outside Jamali: {skipped_outside_jamali}")
    print(f"  No voltage tag: {skipped_no_voltage}")
    print(f"  Below {MIN_VOLTAGE_KV} kV: {skipped_low_voltage}")
    print(f"  Included: {len(rows)}\n")

    print(f"Per voltage class:")
    print(f"  {'Class':<10}{'Lines':>8}{'Length (km)':>15}")
    total = 0
    for c in ['500 kV', '275 kV', '150 kV', '70 kV', 'lain']:
        if count_by_class[c] == 0: continue
        print(f"  {c:<10}{count_by_class[c]:>8}{total_len_by_class[c]:>15,.0f}")
        total += total_len_by_class[c]
    print(f"  {'TOTAL':<10}{sum(count_by_class.values()):>8}{total:>15,.0f}")

    print(f"\nWritten: {OUT_CSV}")
    print(f"Written: {OUT_GJ}")


if __name__ == '__main__':
    run()
