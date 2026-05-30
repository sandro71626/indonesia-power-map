"""
Build generator_master_sumatra.csv dari pembangkit OSM Indonesia, filter ke
region Sumatra (10 provinsi: 8 mainland Sumatra interkoneksi + Batam + Babel),
kategorisasi PLT type, assign provinsi & sistem listrik.

Pola sama dengan extract_jamali_generators.py: OSM `power=plant` adalah sumber
otoritatif (sudah punya koordinat presisi). Tidak ada fuzzy matching atau
override CSV — extractor hanya mengkategorikan tipe pembangkit dan meng-assign
provinsi + sistem berdasarkan bbox.

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)

Output:
  - data/processed/generator_master_sumatra.csv
  - data/processed/generators_sumatra.geojson

Lihat docs/naming_conventions.md: 'Sumatra' = label region/sistem (English);
'Sumatera Utara/Barat/Selatan' tetap ejaan resmi BPS untuk provinsi.
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"
NAME_OVERRIDES = ROOT / "data/overrides/generator_name_overrides.csv"
OUT_CSV = ROOT / "data/processed/generator_master_sumatra.csv"
OUT_GJ = ROOT / "data/processed/generators_sumatra.geojson"

ID_PREFIX = "GEN-SMT"


def load_name_overrides():
    """Load mapping osm_id -> display_name. Original OSM name di-preserve di
    field `osm_name`."""
    overrides = {}
    if not NAME_OVERRIDES.exists():
        return overrides
    with open(NAME_OVERRIDES) as f:
        for r in csv.DictReader(f):
            overrides[r['osm_id'].strip()] = r['override_name'].strip()
    return overrides

# (provinsi, sistem, bbox) — bbox: (lat_min, lon_min, lat_max, lon_max).
#
# Urutan penting: pulau dengan sistem terisolasi (Kepri/Batam, Babel) dicek
# DULU, supaya plant di pulau-pulau itu tidak keburu ke-assign ke bbox
# provinsi mainland yang lebih luas. Sisanya mainland utara→selatan.
#
# Plant yang tidak masuk bbox manapun di-SKIP — artinya bukan region Sumatra
# (mis. PLTU Suralaya di Banten yang lat-nya kebetulan > -6.1 tapi lon-nya
# di luar bbox Lampung).
#
# Bbox Sumatera Selatan (lon_max 105.40) dan Babel (lon_min 105.50) sengaja
# dipisah oleh gap Selat Bangka supaya tidak ada plant yang ambigu.
PROVINCES = [
    ("Kepulauan Riau",            "Batam",   (-0.20, 103.40,  1.55, 105.00)),
    ("Kepulauan Bangka Belitung", "Babel",   (-3.70, 105.50, -1.30, 108.60)),
    ("Aceh",                      "Sumatra", ( 2.00,  94.80,  6.20,  98.30)),
    ("Sumatera Utara",            "Sumatra", ( 0.50,  97.00,  4.30, 100.60)),
    ("Riau",                      "Sumatra", (-1.20, 100.00,  3.00, 103.40)),
    ("Sumatera Barat",            "Sumatra", (-3.50,  98.40,  0.90, 101.80)),
    ("Jambi",                     "Sumatra", (-2.80, 101.00, -0.50, 104.50)),
    ("Sumatera Selatan",          "Sumatra", (-4.80, 102.30, -1.00, 105.40)),
    ("Bengkulu",                  "Sumatra", (-5.50, 101.00, -2.00, 103.50)),
    # Lampung — paling SE Bakauheni (lat ~-5.87, lon ~105.77). Sebelum fix,
    # bbox -6.10..-3.60 / 103.40..106.00 ter-leak ke Banten/Cilegon (lat -6.0,
    # lon 105.94+) sehingga PLTU Krakatau Chandra Energi, Cilegon Posco, &
    # PLTU Asahimas Chemical ter-tag dobel (Lampung di Sumatra + Banten di
    # JAMALI). Ketat ke lat_min -5.92, lon_max 105.85 (Bakauheni + ~5km buffer).
    ("Lampung",                   "Sumatra", (-5.92, 103.40, -3.60, 105.85)),
]


# Centroid geografis aproksimasi per provinsi (lat, lon). Dipakai sebagai
# tiebreaker kalau sebuah plant jatuh di zona overlap bbox >1 provinsi —
# provinsi nyata bukan persegi, jadi bbox-nya pasti overlap di perbatasan.
PROVINCE_CENTROIDS = {
    "Aceh":                       ( 4.50,  96.80),
    "Sumatera Utara":             ( 2.30,  99.00),
    "Riau":                       ( 0.50, 101.80),
    "Kepulauan Riau":             ( 0.90, 104.40),
    "Kepulauan Bangka Belitung":  (-2.50, 106.80),
    "Sumatera Barat":             (-0.80, 100.60),
    "Jambi":                      (-1.60, 102.80),
    "Sumatera Selatan":           (-3.20, 104.00),
    "Bengkulu":                   (-3.60, 102.30),
    "Lampung":                    (-4.80, 105.00),
}


def assign_province(lat, lon):
    """Return (province, system), atau (None, None) jika di luar region Sumatra.

    Bbox provinsi saling overlap di perbatasan (provinsi nyata bukan persegi).
    Strategi: kumpulkan semua provinsi yang bbox-nya memuat titik; kalau cuma
    1, pakai itu; kalau >1, pilih yang centroid-nya paling dekat ke titik
    (jarak Euclidean lat/lon). Ini mencegah plant ke-assign ke provinsi yang
    kebetulan dicek duluan padahal geografis-nya milik provinsi tetangga
    (mis. PLTU Ombilin yang fisiknya di Sumbar tapi masuk bbox Riau juga).
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


def load_sumatra_plants():
    """Load OSM plants di region Sumatra (10 provinsi), dedupe by koordinat."""
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
    print(f"  skipped (luar region Sumatra): {skipped_outside}")
    print(f"  skipped (duplicate coords):    {skipped_duplicate}")
    return plants


def run():
    plants = load_sumatra_plants()
    name_overrides = load_name_overrides()
    print(f"OSM plants di region Sumatra: {len(plants)}")
    print(f"Name overrides loaded: {len(name_overrides)}")

    rows = []
    by_system_type = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'mw': 0.0}))
    by_province = defaultdict(lambda: {'count': 0, 'mw': 0.0})
    next_id = 1

    for f, lat, lon, province, system in plants:
        props = f.get('properties', {})
        osm_name = (props.get('name') or props.get('name:en') or '').strip()
        osm_id = props.get('@id', '')
        name = name_overrides.get(osm_id, osm_name)
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
            'osm_name': osm_name,
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
    print(f"\n{'System':<10}{'Type':<10}{'Count':>7}{'Total MW':>12}")
    grand_count = 0
    grand_mw = 0.0
    for system in ['Sumatra', 'Batam', 'Babel']:
        if system not in by_system_type:
            continue
        for t, agg in sorted(by_system_type[system].items(), key=lambda x: -x[1]['mw']):
            print(f"{system:<10}{t:<10}{agg['count']:>7}{agg['mw']:>12,.0f}")
            grand_count += agg['count']
            grand_mw += agg['mw']
    print(f"\n{'TOTAL':<20}{grand_count:>7}{grand_mw:>12,.0f}")

    # Summary per provinsi
    print(f"\n=== Per provinsi (plant dengan kapasitas) ===")
    print(f"{'Provinsi':<28}{'Count':>7}{'Total MW':>12}")
    for name, _, _ in PROVINCES:
        if name not in by_province:
            continue
        agg = by_province[name]
        print(f"{name:<28}{agg['count']:>7}{agg['mw']:>12,.0f}")

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
