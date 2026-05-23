"""
Build generator_master_kalimantan.csv dari pembangkit OSM Indonesia, filter ke
region Kalimantan (5 provinsi, 3 sub-sistem: Khatulistiwa / Kalselteng /
Mahakam), kategorisasi PLT type, assign provinsi & sistem listrik.

Pola sama dengan extract_sumatra_generators.py: OSM `power=plant` adalah
sumber otoritatif (sudah punya koordinat presisi). Tidak ada fuzzy matching
atau override CSV — extractor hanya mengkategorikan tipe pembangkit dan
meng-assign provinsi + sistem berdasarkan bbox + centroid tiebreak.

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)

Output:
  - data/processed/generator_master_kalimantan.csv
  - data/processed/generators_kalimantan.geojson
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"
OUT_CSV = ROOT / "data/processed/generator_master_kalimantan.csv"
OUT_GJ = ROOT / "data/processed/generators_kalimantan.geojson"

ID_PREFIX = "GEN-KLM"

# (provinsi, sistem, bbox) — bbox: (lat_min, lon_min, lat_max, lon_max).
# Semua provinsi Kalimantan di satu daratan; bbox pasti overlap di perbatasan
# dan di-resolve via centroid tiebreak di assign_province().
# Bbox Kaltim sengaja diperluas ke lat 2.60 supaya mencakup Berau (Tanjung
# Redeb) yang menjorok ke utara — catatan: plant Berau bisa saja ke-assign
# ke Kaltara oleh tiebreak, tapi system-nya tetap benar (sama-sama Mahakam).
PROVINCES = [
    ("Kalimantan Barat",   "Khatulistiwa", (-3.10, 108.50,  2.10, 114.30)),
    ("Kalimantan Tengah",  "Kalselteng",   (-3.70, 110.70,  0.10, 115.90)),
    ("Kalimantan Selatan", "Kalselteng",   (-4.80, 113.90, -1.30, 117.00)),
    ("Kalimantan Timur",   "Mahakam",      (-2.70, 113.30,  2.60, 119.10)),
    ("Kalimantan Utara",   "Mahakam",      ( 1.20, 114.50,  4.40, 118.20)),
]

# Centroid tiebreaker per provinsi (lat, lon). Bukan centroid geometris murni
# melainkan "pusat massa pembangkit/kota" — ditaruh di tempat fasilitas listrik
# provinsi itu sebenarnya terkonsentrasi. Penting untuk Kalteng: kota &
# pembangkitnya (Palangka Raya, Pulang Pisau, Sampit) ada di bagian SELATAN
# provinsi, dekat perbatasan Kalsel — jadi centroid ditaruh di selatan, bukan
# di tengah-geometris, supaya plant selatan Kalteng tidak ke-tiebreak ke Kalsel.
PROVINCE_CENTROIDS = {
    "Kalimantan Barat":   (-0.20, 111.30),
    "Kalimantan Tengah":  (-2.20, 113.40),
    "Kalimantan Selatan": (-3.30, 115.20),
    "Kalimantan Timur":   (-0.50, 116.30),
    "Kalimantan Utara":   ( 2.80, 116.50),
}


def assign_province(lat, lon):
    """Return (province, system), atau (None, None) jika di luar Kalimantan.

    Kumpulkan semua provinsi yang bbox-nya memuat titik; kalau >1, pilih yang
    centroid-nya paling dekat ke titik (jarak Euclidean lat/lon).
    """
    candidates = []
    for name, system, (la_min, lo_min, la_max, lo_max) in PROVINCES:
        if la_min <= lat <= la_max and lo_min <= lon <= lo_max:
            candidates.append((name, system))
    if not candidates:
        return None, None
    if len(candidates) == 1:
        return candidates[0]
    best, best_d2 = None, None
    for name, system in candidates:
        clat, clon = PROVINCE_CENTROIDS[name]
        d2 = (lat - clat) ** 2 + (lon - clon) ** 2
        if best_d2 is None or d2 < best_d2:
            best_d2, best = d2, (name, system)
    return best


# OSM plant:source -> tipe PLT Indonesia
SOURCE_MAP = {
    'hydro': 'PLTA',
    'coal': 'PLTU',
    'gas': 'PLTG',            # default open cycle; PLTGU jika combined cycle
    'geothermal': 'PLTP',
    'solar': 'PLTS',
    'wind': 'PLTB',
    'diesel': 'PLTD',
    'waste': 'PLTSa',
    'biomass': 'PLT Biomas',
    'oil': 'PLTD',
}


def derive_type(props, capacity_mw):
    """Tentukan tipe PLT. Prefer prefix nama (PLTx), fallback ke OSM tag."""
    name = (props.get('name') or '').strip()
    method = (props.get('plant:method') or '').lower()
    source = (props.get('plant:source') or '').lower()

    m = re.match(r'^(PLT(?:GU|MG|MH|U|G|A|P|S|B|M|D|Sa|Bm))\b', name, re.I)
    if m:
        return m.group(1).upper().replace('PLTSA', 'PLTSa')

    if source == 'gas' and 'combined' in method:
        return 'PLTGU'
    if source == 'hydro':
        if capacity_mw is not None:
            if capacity_mw >= 10:
                return 'PLTA'
            elif capacity_mw >= 1:
                return 'PLTM'
            else:
                return 'PLTMH'
        return 'PLTA'
    return SOURCE_MAP.get(source, 'Unknown')


def parse_capacity_mw(v):
    """Parse plant:output:electricity ke MW. Contoh: '660 MW', '660000 kW'."""
    if not v:
        return None
    s = str(v).strip().lower().replace(' ', '').replace(',', '.')
    m = re.match(r'^([\d\.]+)(mw|kw|gw)?$', s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or 'mw'
    if unit == 'kw':
        val /= 1000
    elif unit == 'gw':
        val *= 1000
    return round(val, 2)


def load_kalimantan_plants():
    """Load OSM plants di region Kalimantan (5 provinsi), dedupe by koordinat."""
    gj = json.load(open(PLANTS_GJ))
    seen_coords = {}
    plants = []
    skipped_outside = 0
    skipped_duplicate = 0
    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'Point':
            continue
        lon, lat = g['coordinates'][:2]
        province, system = assign_province(lat, lon)
        if province is None:
            skipped_outside += 1
            continue
        key = (round(lat, 4), round(lon, 4))
        if key in seen_coords:
            skipped_duplicate += 1
            continue
        seen_coords[key] = True
        plants.append((f, lat, lon, province, system))
    print(f"  skipped (luar region Kalimantan): {skipped_outside}")
    print(f"  skipped (duplicate coords):       {skipped_duplicate}")
    return plants


def run():
    plants = load_kalimantan_plants()
    print(f"OSM plants di region Kalimantan: {len(plants)}")

    rows = []
    by_system_type = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'mw': 0.0}))
    by_province = defaultdict(lambda: {'count': 0, 'mw': 0.0})
    next_id = 1

    for f, lat, lon, province, system in plants:
        props = f.get('properties', {})
        name = (props.get('name') or props.get('name:en') or '').strip()
        cap_mw = parse_capacity_mw(props.get('plant:output:electricity'))
        plt_type = derive_type(props, cap_mw)
        operator = (props.get('operator') or '').strip()
        method = (props.get('plant:method') or '').strip()

        flags = []
        if not name:
            flags.append('NO_NAME')
        if cap_mw is None:
            flags.append('NO_CAPACITY')
        if plt_type == 'Unknown':
            flags.append('NO_TYPE')

        row = {
            'id': f'{ID_PREFIX}-{next_id:04d}',
            'name': name or '(unnamed)',
            'type': plt_type,
            'capacity_mw': cap_mw if cap_mw is not None else '',
            'province': province,
            'system': system,
            'status': 'existing',
            'operator': operator,
            'method': method,
            'lat': lat, 'lon': lon,
            'osm_id': props.get('@id', ''),
            'osm_source': props.get('plant:source', ''),
            'review_flag': ';'.join(flags),
            'source_id': 'OSM-overpass',
        }
        rows.append(row)
        if cap_mw:
            by_system_type[system][plt_type]['count'] += 1
            by_system_type[system][plt_type]['mw'] += cap_mw
            by_province[province]['count'] += 1
            by_province[province]['mw'] += cap_mw
        next_id += 1

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as f:
        if not rows:
            print("\nERROR: tidak ada plant ter-extract.")
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Write GeoJSON
    features = []
    for r in rows:
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
            'properties': {k: v for k, v in r.items() if k not in ('lat', 'lon')}
        })
    with open(OUT_GJ, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f, ensure_ascii=False)

    # Summary: kategorisasi per sistem
    print(f"\n=== Kategorisasi pembangkit ({len(rows)} plant) ===")
    print(f"\n{'System':<14}{'Type':<10}{'Count':>7}{'Total MW':>12}")
    grand_count = 0
    grand_mw = 0.0
    for system in ['Khatulistiwa', 'Kalselteng', 'Mahakam']:
        if system not in by_system_type:
            continue
        for t, agg in sorted(by_system_type[system].items(), key=lambda x: -x[1]['mw']):
            print(f"{system:<14}{t:<10}{agg['count']:>7}{agg['mw']:>12,.0f}")
            grand_count += agg['count']
            grand_mw += agg['mw']
    print(f"\n{'TOTAL':<24}{grand_count:>7}{grand_mw:>12,.0f}")

    # Summary per provinsi
    print(f"\n=== Per provinsi (plant dengan kapasitas) ===")
    print(f"{'Provinsi':<22}{'Count':>7}{'Total MW':>12}")
    for name, _, _ in PROVINCES:
        if name not in by_province:
            continue
        agg = by_province[name]
        print(f"{name:<22}{agg['count']:>7}{agg['mw']:>12,.0f}")

    # Review flags
    n_no_name = sum(1 for r in rows if 'NO_NAME' in r['review_flag'])
    n_no_cap = sum(1 for r in rows if 'NO_CAPACITY' in r['review_flag'])
    n_no_type = sum(1 for r in rows if 'NO_TYPE' in r['review_flag'])
    print(f"\n=== Review flags ===")
    print(f"  NO_NAME:     {n_no_name}")
    print(f"  NO_CAPACITY: {n_no_cap}")
    print(f"  NO_TYPE:     {n_no_type}")

    print(f"\nWritten: {OUT_CSV} ({len(rows)} rows)")
    print(f"Written: {OUT_GJ} ({len(features)} features)")


if __name__ == '__main__':
    run()
