"""
Build transmission_master_kalimantan.csv + GeoJSON dari OSM lines, filter ke
region Kalimantan (3 sub-sistem: Khatulistiwa, Kalselteng, Mahakam).

Pola sama dengan extract_sumatra_transmission.py: OSM `power=line` adalah
sumber otoritatif (punya geometri LineString). Extractor memfilter tegangan
transmisi (>= 70 kV), menghitung panjang via haversine, mengkategorikan
voltage class, dan meng-assign sistem listrik berdasar centroid garis.

Beda dengan Sumatra: ketiga sub-sistem Kalimantan ada di satu daratan dan
bersebelahan, jadi bbox-nya overlap di perbatasan. assign_system memakai
centroid tiebreak (sama seperti extractor generator Kalimantan).

Filter:
  - Hanya transmisi tegangan >= 70 kV (exclude distribusi 20 kV)
  - Garis yang centroid-nya jatuh di region Kalimantan

Output:
  - data/processed/transmission_master_kalimantan.csv
  - data/processed/transmission_kalimantan.geojson
"""
import re
import json
import csv
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINES_GJ = ROOT / "data/geojson/indonesia_lines.geojson"
OUT_CSV = ROOT / "data/processed/transmission_master_kalimantan.csv"
OUT_GJ = ROOT / "data/processed/transmission_kalimantan.geojson"

ID_PREFIX = "TRM-KLM"

# Minimum transmission voltage (kV). Filter out distribusi <70 kV.
MIN_VOLTAGE_KV = 70

# Sub-sistem listrik Kalimantan + bbox (lat_min, lon_min, lat_max, lon_max).
# Bbox = union provinsi penyusun sistem:
#   Khatulistiwa = Kalbar
#   Kalselteng   = Kalteng + Kalsel
#   Mahakam      = Kaltim + Kaltara
SYSTEMS = [
    ("Khatulistiwa", (-3.10, 108.50,  2.10, 114.30)),
    ("Kalselteng",   (-4.80, 110.70,  0.10, 117.00)),
    ("Mahakam",      (-2.70, 113.30,  4.40, 119.10)),
]

# Centroid tiebreaker per sistem (lat, lon) — dipakai kalau centroid garis
# jatuh di overlap bbox >1 sistem.
SYSTEM_CENTROIDS = {
    "Khatulistiwa": (-0.20, 111.30),
    "Kalselteng":   (-2.50, 114.00),
    "Mahakam":      ( 0.30, 116.40),
}


def assign_system(centroid_lat, centroid_lon):
    """Return nama sistem, atau None kalau di luar region Kalimantan.

    Bbox sistem overlap di perbatasan; kalau centroid garis masuk >1 bbox,
    pilih sistem dengan centroid terdekat (jarak Euclidean lat/lon).
    """
    candidates = []
    for name, (la_min, lo_min, la_max, lo_max) in SYSTEMS:
        if la_min <= centroid_lat <= la_max and lo_min <= centroid_lon <= lo_max:
            candidates.append(name)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    best, best_d2 = None, None
    for name in candidates:
        clat, clon = SYSTEM_CENTROIDS[name]
        d2 = (centroid_lat - clat) ** 2 + (centroid_lon - clon) ** 2
        if best_d2 is None or d2 < best_d2:
            best_d2, best = d2, name
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

    Warna konsisten dengan docs/design_decisions.md. Kalimantan backbone
    150 kV; 275 kV sebagian dalam pembangunan; 500 kV belum ada.
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
    rows = []
    features = []
    next_id = 1

    classes = ['500 kV', '275 kV', '150 kV', '70 kV', 'lain']
    count_by_class = {c: 0 for c in classes}
    length_by_class = {c: 0.0 for c in classes}
    count_by_system = {s[0]: 0 for s in SYSTEMS}
    length_by_system = {s[0]: 0.0 for s in SYSTEMS}

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
        system = assign_system(clat, clon)
        if system is None:
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
        count_by_system[system] += 1
        length_by_system[system] += length_km

        row = {
            'id': f'{ID_PREFIX}-{next_id:04d}',
            'system': system,
            'voltage_class': vclass,
            'voltage_kv_max': max_v,
            'voltage_kv_all': ';'.join(str(int(v)) for v in vs),
            'length_km': round(length_km, 3),
            'osm_id': props.get('@id', ''),
            'osm_voltage': props.get('voltage', ''),
            'source_id': 'OSM-overpass',
        }
        rows.append(row)
        features.append({
            'type': 'Feature',
            'geometry': g,
            'properties': {**row, 'color': color, 'weight': weight}
        })
        next_id += 1

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as fh:
        if not rows:
            print("ERROR: tidak ada line ter-extract.")
            return
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Write GeoJSON
    with open(OUT_GJ, 'w') as fh:
        json.dump({'type': 'FeatureCollection', 'features': features}, fh, ensure_ascii=False)

    # Summary
    print("OSM lines diproses:")
    print(f"  Bukan LineString valid:    {skipped_not_line}")
    print(f"  Di luar region Kalimantan: {skipped_outside}")
    print(f"  Tanpa tag voltage:         {skipped_no_voltage}")
    print(f"  Di bawah {MIN_VOLTAGE_KV} kV:            {skipped_low_voltage}")
    print(f"  Included:                  {len(rows)}\n")

    print("Per voltage class:")
    print(f"  {'Class':<10}{'Lines':>8}{'Length (km)':>15}")
    total_n = 0
    total_len = 0.0
    for c in classes:
        if count_by_class[c] == 0:
            continue
        print(f"  {c:<10}{count_by_class[c]:>8}{length_by_class[c]:>15,.0f}")
        total_n += count_by_class[c]
        total_len += length_by_class[c]
    print(f"  {'TOTAL':<10}{total_n:>8}{total_len:>15,.0f}")

    print("\nPer sistem:")
    print(f"  {'System':<14}{'Lines':>8}{'Length (km)':>15}")
    for s, _ in SYSTEMS:
        if count_by_system[s] == 0:
            continue
        print(f"  {s:<14}{count_by_system[s]:>8}{length_by_system[s]:>15,.0f}")

    print(f"\nWritten: {OUT_CSV} ({len(rows)} rows)")
    print(f"Written: {OUT_GJ} ({len(features)} features)")


if __name__ == '__main__':
    run()
