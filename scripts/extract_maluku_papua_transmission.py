"""
Build transmission master untuk region Maluku & Papua dari OSM `power=line`,
filter tegangan >= 70 kV, kategorisasi voltage class, assign region.

Step 5 transmission — melengkapi Maluku/Papua setelah substations & generators.

Sama pola dengan extract_sulawesi_transmission.py: OSM line adalah sumber
otoritatif (punya geometri LineString). Filter ke tegangan transmisi (>= 70
kV), hitung panjang via haversine, kategorisasi voltage class.

Mirip generators Maluku/Papua, output di-split jadi DUA region — Maluku &
Papua tidak interkoneksi (kumpulan sistem pulau terisolasi):

  region 'maluku' : Maluku + Maluku Utara   -> system 'Maluku'
  region 'papua'  : Papua + Papua Barat     -> system 'Papua'

Bbox identik dengan generators:
  - Maluku Utara lon_min 125.30 untuk exclude line Sulawesi Utara (Lahendong
    interconnect 150 kV bocor kalau lon_min terlalu barat).
  - Maluku lon_min 125.50 untuk exclude line Sulteng timur (Banggai).
  - Maluku ↔ Papua Barat dan Papua ↔ Papua Barat overlap; centroid garis
    di-tiebreak ke centroid region terdekat.

Backbone Maluku & Papua mayoritas 150 kV; 70 kV pakai untuk sub-koridor /
sistem pulau kecil. 275 kV & 500 kV belum ada di region ini.

Sumber:
  - data/geojson/indonesia_lines.geojson (OSM via Overpass)

Output:
  - data/processed/transmission_master_maluku.csv + transmission_maluku.geojson
  - data/processed/transmission_master_papua.csv  + transmission_papua.geojson
"""
import re
import json
import csv
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINES_GJ = ROOT / "data/geojson/indonesia_lines.geojson"

REGIONS = ["maluku", "papua"]
ID_PREFIX = {"maluku": "TRM-MLK", "papua": "TRM-PAP"}
OUT_CSV = {
    "maluku": ROOT / "data/processed/transmission_master_maluku.csv",
    "papua":  ROOT / "data/processed/transmission_master_papua.csv",
}
OUT_GJ = {
    "maluku": ROOT / "data/processed/transmission_maluku.geojson",
    "papua":  ROOT / "data/processed/transmission_papua.geojson",
}

# Minimum transmission voltage (kV). Filter out distribusi <70 kV.
MIN_VOLTAGE_KV = 70

# (provinsi, region, system, bbox, centroid) — sama dengan generators.
# bbox     = (lat_min, lon_min, lat_max, lon_max)
# centroid = (lat, lon) — tiebreak overlap bbox via jarak Euclidean.
PROVINCES = [
    ("Maluku Utara", "maluku", "Maluku", (-2.60, 125.30,  3.10, 129.60), ( 0.80, 127.50)),
    ("Maluku",       "maluku", "Maluku", (-8.80, 125.50, -2.65, 135.80), (-3.70, 128.20)),
    ("Papua Barat",  "papua",  "Papua",  (-4.50, 129.00,  1.20, 135.20), (-0.86, 132.50)),
    ("Papua",        "papua",  "Papua",  (-9.60, 134.00,  0.70, 141.20), (-3.50, 138.50)),
]


def assign_province(lat, lon):
    """Return (province, region, system) atau (None,None,None) di luar region.

    Pakai pola multi-bbox + centroid tiebreak, sama dengan generators.
    """
    candidates = []
    for name, region, system, (la_min, lo_min, la_max, lo_max), centroid in PROVINCES:
        if la_min <= lat <= la_max and lo_min <= lon <= lo_max:
            candidates.append((name, region, system, centroid))
    if not candidates:
        return None, None, None
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1], candidates[0][2]
    best, best_d2 = None, None
    for name, region, system, (clat, clon) in candidates:
        d2 = (lat - clat) ** 2 + (lon - clon) ** 2
        if best_d2 is None or d2 < best_d2:
            best_d2, best = d2, (name, region, system)
    return best


def parse_voltages_kv(v):
    """OSM voltage tag (Volt) -> list of kV. '275000;150000' -> [275, 150]"""
    if not v:
        return []
    out = []
    for p in re.split(r'[;,]', str(v)):
        p = p.strip()
        if p.isdigit():
            out.append(int(p) / 1000)
    return out


def haversine_km(coords):
    """Panjang LineString dalam km."""
    total = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i][:2]
        lon2, lat2 = coords[i + 1][:2]
        dlon = radians(lon2 - lon1)
        dlat = radians(lat2 - lat1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        total += 2 * 6371 * asin(sqrt(a))
    return total


def centroid(coords):
    """Rata-rata lat/lon dari semua titik LineString. Return (lat, lon)."""
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def voltage_class(max_kv):
    """Return (label, warna hex, weight) per kelas tegangan.

    Warna konsisten dengan docs/design_decisions.md. Backbone Maluku/Papua
    150 kV; 70 kV sub-koridor. 275 kV & 500 kV belum ada di region ini.
    """
    if max_kv >= 500:
        return ('500 kV', '#d62728', 3.0)
    if max_kv >= 275:
        return ('275 kV', '#9467bd', 2.5)
    if max_kv >= 150:
        return ('150 kV', '#1f77b4', 1.8)
    if max_kv >= 70:
        return ('70 kV', '#2ca02c', 1.2)
    return ('lain', '#999', 1.0)


def run():
    gj = json.load(open(LINES_GJ))
    rows_by_region = {r: [] for r in REGIONS}
    features_by_region = {r: [] for r in REGIONS}
    next_id = {r: 1 for r in REGIONS}

    classes = ['500 kV', '275 kV', '150 kV', '70 kV', 'lain']
    count_by_class = {c: 0 for c in classes}
    length_by_class = {c: 0.0 for c in classes}
    count_by_province = {p[0]: 0 for p in PROVINCES}
    length_by_province = {p[0]: 0.0 for p in PROVINCES}
    count_by_region = {r: 0 for r in REGIONS}
    length_by_region = {r: 0.0 for r in REGIONS}

    skipped_not_line = 0
    skipped_outside = 0
    skipped_no_voltage = 0
    skipped_low_voltage = 0

    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'LineString':
            skipped_not_line += 1
            continue
        coords = g['coordinates']
        if len(coords) < 2:
            skipped_not_line += 1
            continue
        clat, clon = centroid(coords)
        province, region, system = assign_province(clat, clon)
        if region is None:
            skipped_outside += 1
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
        length_by_class[vclass] += length_km
        count_by_province[province] += 1
        length_by_province[province] += length_km
        count_by_region[region] += 1
        length_by_region[region] += length_km

        row = {
            'id': f'{ID_PREFIX[region]}-{next_id[region]:04d}',
            'province': province,
            'system': system,
            'voltage_class': vclass,
            'voltage_kv_max': max_v,
            'voltage_kv_all': ';'.join(str(int(v)) for v in vs),
            'length_km': round(length_km, 3),
            'osm_id': props.get('@id', ''),
            'osm_voltage': props.get('voltage', ''),
            'source_id': 'OSM-overpass',
        }
        rows_by_region[region].append(row)
        features_by_region[region].append({
            'type': 'Feature',
            'geometry': g,
            'properties': {**row, 'color': color, 'weight': weight}
        })
        next_id[region] += 1

    # Write per-region CSV + GeoJSON
    for region in REGIONS:
        rows = rows_by_region[region]
        feats = features_by_region[region]
        if not rows:
            print(f"\nERROR: tidak ada line di region {region}.")
            continue
        with open(OUT_CSV[region], 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
        with open(OUT_GJ[region], 'w') as fh:
            json.dump({'type': 'FeatureCollection', 'features': feats}, fh, ensure_ascii=False)
        print(f"\nWritten: {OUT_CSV[region]} ({len(rows)} rows)")
        print(f"Written: {OUT_GJ[region]} ({len(feats)} features)")

    # Summary
    print("\nOSM lines diproses:")
    print(f"  Bukan LineString valid:      {skipped_not_line}")
    print(f"  Di luar region Maluku/Papua: {skipped_outside}")
    print(f"  Tanpa tag voltage:           {skipped_no_voltage}")
    print(f"  Di bawah {MIN_VOLTAGE_KV} kV:              {skipped_low_voltage}")
    total_n = sum(len(rows_by_region[r]) for r in REGIONS)
    print(f"  Included:                    {total_n}\n")

    print("Per voltage class:")
    print(f"  {'Class':<10}{'Lines':>8}{'Length (km)':>15}")
    total_len = 0.0
    for c in classes:
        if count_by_class[c] == 0:
            continue
        print(f"  {c:<10}{count_by_class[c]:>8}{length_by_class[c]:>15,.1f}")
        total_len += length_by_class[c]
    print(f"  {'TOTAL':<10}{total_n:>8}{total_len:>15,.1f}")

    print("\nPer region:")
    print(f"  {'Region':<10}{'Lines':>8}{'Length (km)':>15}")
    for r in REGIONS:
        if count_by_region[r] == 0:
            continue
        print(f"  {r:<10}{count_by_region[r]:>8}{length_by_region[r]:>15,.1f}")

    print("\nPer provinsi:")
    print(f"  {'Provinsi':<16}{'Lines':>8}{'Length (km)':>15}")
    for p, _, _, _, _ in PROVINCES:
        if count_by_province[p] == 0:
            continue
        print(f"  {p:<16}{count_by_province[p]:>8}{length_by_province[p]:>15,.1f}")


if __name__ == '__main__':
    run()
