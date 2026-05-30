"""
Build generator_master_sulawesi.csv dari pembangkit OSM Indonesia, filter ke
region Sulawesi (6 provinsi, 3 sub-sistem: Sulutgo / Sulteng / Sulselrabar),
kategorisasi PLT type, assign provinsi & sistem listrik.

Pola sama dengan extract_kalimantan_generators.py: OSM `power=plant` adalah
sumber otoritatif (sudah punya koordinat presisi). Tidak ada fuzzy matching
atau override koordinat — extractor hanya mengkategorikan tipe pembangkit dan
meng-assign provinsi + sistem berdasarkan bbox + centroid tiebreak.

Beda dengan Kalimantan: geografi Sulawesi (huruf K, empat semenanjung)
membuat bbox provinsi banyak yang overlap. Dua penanganan:

  1. Centroid PER-BBOX, bukan per-provinsi. Tiap entri PROVINCES punya
     centroid sendiri, jadi satu provinsi boleh punya >1 bbox dengan
     centroid yang berbeda. Dipakai untuk tiga lobe di zona tripoint
     Sulsel/Sulteng/Sultra yang sama-latitude:
       - lobe Morowali (Sulteng menjorok ke tenggara) — supaya plant
         IMIP/Bungku tetap ke Sulteng;
       - lobe Luwu Timur (Sulsel, Sorowako/Malili) — supaya kompleks
         PLTA Vale (Larona/Balambano/Karebbe) tetap ke Sulsel;
       - strip Kolaka Utara (Sultra menjorok ke utara) — supaya plant
         pantai barat tetap ke Sulawesi Tenggara.

  2. PROVINCE_OVERRIDE — dict osm_id -> (provinsi, sistem). Cadangan untuk
     plant yang lobe-bbox pun masih salah assign. Saat ini kosong — tiga
     lobe-bbox di atas sudah cukup; disimpan sebagai mekanisme bila
     re-pull OSM berikutnya memunculkan kasus baru.

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)

Output:
  - data/processed/generator_master_sulawesi.csv
  - data/processed/generators_sulawesi.geojson
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"
NAME_OVERRIDES = ROOT / "data/overrides/generator_name_overrides.csv"
OUT_CSV = ROOT / "data/processed/generator_master_sulawesi.csv"
OUT_GJ = ROOT / "data/processed/generators_sulawesi.geojson"

ID_PREFIX = "GEN-SLW"


def load_name_overrides():
    """Load mapping osm_id -> display_name dari generator_name_overrides.csv.

    Untuk normalisasi nama plant non-Indonesia (English deskriptif di plant
    captive industrial Morowali-Konawe). Original OSM name di-preserve di
    field `osm_name` saat write CSV."""
    overrides = {}
    if not NAME_OVERRIDES.exists():
        return overrides
    with open(NAME_OVERRIDES) as f:
        for r in csv.DictReader(f):
            overrides[r['osm_id'].strip()] = r['override_name'].strip()
    return overrides

# Urutan sistem untuk ringkasan.
SYSTEMS = ["Sulutgo", "Sulteng", "Sulselrabar"]

# (provinsi, sistem, bbox, centroid)
#   bbox     = (lat_min, lon_min, lat_max, lon_max)
#   centroid = (lat, lon) — "pusat massa pembangkit/kota" provinsi, dipakai
#              sebagai tiebreak kalau satu titik masuk >1 bbox.
#
# Satu provinsi boleh punya >1 entri (lihat Sulteng & Sulawesi Tenggara).
PROVINCES = [
    # Sulawesi Utara — semenanjung utara + kepulauan Sangihe-Talaud.
    # lon_max 127.00: cukup menutup Talaud, berhenti sebelum Ternate
    # (Maluku Utara, lon ~127,4).
    ("Sulawesi Utara",    "Sulutgo",     ( 0.00, 123.30,  5.70, 127.00), ( 1.40, 124.85)),
    # Gorontalo — di antara Sulut & Sulteng.
    ("Gorontalo",         "Sulutgo",     ( 0.20, 121.10,  1.10, 123.50), ( 0.60, 122.60)),
    # Sulawesi Tengah — provinsi terbesar; bbox utama menutup Palu, Poso,
    # Donggala, semenanjung timur (Banggai/Luwuk).
    ("Sulawesi Tengah",   "Sulteng",     (-3.10, 119.00,  1.50, 124.30), (-1.00, 120.30)),
    # Sulawesi Tengah — lobe Morowali (tenggara). Selatitude dengan
    # Sulawesi Tenggara; centroid sendiri di Morowali supaya plant
    # IMIP/Bungku tetap ke Sulteng.
    ("Sulawesi Tengah",   "Sulteng",     (-3.10, 121.50, -2.40, 123.00), (-2.70, 122.10)),
    # Sulawesi Barat — strip pantai barat. lon_max 119.55: menutup Mamasa
    # (timur Sulbar) tapi berhenti sebelum Palu (lon ~119,9 → Sulteng).
    ("Sulawesi Barat",    "Sulselrabar", (-3.55, 118.50, -0.85, 119.55), (-2.40, 119.10)),
    # Sulawesi Selatan — semenanjung barat daya + Kepulauan Selayar.
    ("Sulawesi Selatan",  "Sulselrabar", (-7.50, 118.70, -1.90, 121.40), (-4.30, 119.80)),
    # Sulawesi Selatan — lobe Luwu Timur (Sorowako/Malili). Kompleks PLTA
    # Vale (Larona/Balambano/Karebbe) di sini selatitude dengan Morowali &
    # Kolaka Utara; centroid sendiri supaya tidak ke-tiebreak ke tetangga.
    ("Sulawesi Selatan",  "Sulselrabar", (-2.85, 120.95, -2.45, 121.50), (-2.65, 121.25)),
    # Sulawesi Tenggara — semenanjung tenggara + Buton/Muna/Wakatobi.
    ("Sulawesi Tenggara", "Sulselrabar", (-6.50, 120.70, -3.05, 124.60), (-4.10, 122.40)),
    # Sulawesi Tenggara — strip Kolaka Utara (pantai barat, menjorok ke
    # utara). lon_max 121.13: berhenti sebelum kompleks PLTA Vale di Luwu
    # Timur (lon ~121,18+). Saat ini belum ada plant OSM di strip ini.
    ("Sulawesi Tenggara", "Sulselrabar", (-3.05, 120.90, -2.60, 121.13), (-2.85, 121.02)),
]

# Urutan provinsi unik (untuk ringkasan per-provinsi).
PROVINCE_ORDER = []
for _p, _s, _b, _c in PROVINCES:
    if _p not in PROVINCE_ORDER:
        PROVINCE_ORDER.append(_p)

# Override assign per osm_id — untuk plant zona tripoint Sulsel/Sulteng/Sultra
# (sekitar Sorowako–Poso) yang bbox+centroid tetap salah. Diisi setelah
# inspeksi run pertama. Format: 'way/123' / 'node/123' -> (provinsi, sistem).
PROVINCE_OVERRIDE = {
    # contoh: "way/123456789": ("Sulawesi Selatan", "Sulselrabar"),
}


def assign_province(lat, lon):
    """Return (province, system), atau (None, None) jika di luar Sulawesi.

    Kumpulkan semua entri PROVINCES yang bbox-nya memuat titik; kalau >1,
    pilih entri yang centroid-nya paling dekat ke titik (jarak Euclidean
    lat/lon). Centroid bersifat per-bbox, jadi satu provinsi boleh punya
    beberapa bbox dengan centroid berbeda.
    """
    candidates = []
    for name, system, (la_min, lo_min, la_max, lo_max), centroid in PROVINCES:
        if la_min <= lat <= la_max and lo_min <= lon <= lo_max:
            candidates.append((name, system, centroid))
    if not candidates:
        return None, None
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1]
    best, best_d2 = None, None
    for name, system, (clat, clon) in candidates:
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


def load_sulawesi_plants():
    """Load OSM plants di region Sulawesi (6 provinsi), dedupe by koordinat."""
    gj = json.load(open(PLANTS_GJ))
    seen_coords = {}
    plants = []
    skipped_outside = 0
    skipped_duplicate = 0
    n_override = 0
    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'Point':
            continue
        lon, lat = g['coordinates'][:2]
        osm_id = f.get('properties', {}).get('@id', '')
        if osm_id in PROVINCE_OVERRIDE:
            province, system = PROVINCE_OVERRIDE[osm_id]
            n_override += 1
        else:
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
    print(f"  skipped (luar region Sulawesi): {skipped_outside}")
    print(f"  skipped (duplicate coords):     {skipped_duplicate}")
    if n_override:
        print(f"  province override di-apply:     {n_override}")
    return plants


def run():
    plants = load_sulawesi_plants()
    name_overrides = load_name_overrides()
    print(f"OSM plants di region Sulawesi: {len(plants)}")
    print(f"Name overrides loaded: {len(name_overrides)}")

    rows = []
    by_system_type = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'mw': 0.0}))
    by_province = defaultdict(lambda: {'count': 0, 'mw': 0.0})
    next_id = 1
    used_overrides = set()

    for f, lat, lon, province, system in plants:
        props = f.get('properties', {})
        osm_name = (props.get('name') or props.get('name:en') or '').strip()
        osm_id = props.get('@id', '')

        # Apply name override jika ada (normalisasi nama English/Mandarin).
        if osm_id in name_overrides:
            display_name = name_overrides[osm_id]
            used_overrides.add(osm_id)
        else:
            display_name = osm_name

        cap_mw = parse_capacity_mw(props.get('plant:output:electricity'))
        plt_type = derive_type(props, cap_mw)
        operator = (props.get('operator') or '').strip()
        method = (props.get('plant:method') or '').strip()

        flags = []
        if not display_name:
            flags.append('NO_NAME')
        if cap_mw is None:
            flags.append('NO_CAPACITY')
        if plt_type == 'Unknown':
            flags.append('NO_TYPE')

        row = {
            'id': f'{ID_PREFIX}-{next_id:04d}',
            'name': display_name or '(unnamed)',
            'osm_name': osm_name,  # Original OSM name, untuk audit trail
            'type': plt_type,
            'capacity_mw': cap_mw if cap_mw is not None else '',
            'province': province,
            'system': system,
            'status': 'existing',
            'operator': operator,
            'method': method,
            'lat': lat, 'lon': lon,
            'osm_id': osm_id,
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
    for system in SYSTEMS:
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
    for name in PROVINCE_ORDER:
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

    # Daftar plant zona tripoint (untuk verifikasi manual urutan provinsi).
    # Cetak plant yang lat -3.3..-1.8 & lon 120.3..122.5 — area Sorowako,
    # Poso, Luwu Timur, Morowali, Kolaka Utara.
    print(f"\n=== Plant di zona tripoint (cek assign manual) ===")
    trip = [r for r in rows
            if -3.3 <= r['lat'] <= -1.8 and 120.3 <= r['lon'] <= 122.5]
    if trip:
        for r in sorted(trip, key=lambda x: (x['province'], x['lat'])):
            print(f"  {r['province']:<20} {r['name']:<28} "
                  f"({r['lat']:.3f},{r['lon']:.3f})  {r['osm_id']}")
    else:
        print("  (tidak ada)")

    print(f"\nWritten: {OUT_CSV} ({len(rows)} rows)")
    print(f"Written: {OUT_GJ} ({len(features)} features)")


if __name__ == '__main__':
    run()
