"""
Build generator master untuk region Maluku & Papua dari OSM `power=plant`,
kategorisasi PLT type, assign provinsi & region.

Step 5 generators — melengkapi Maluku/Papua setelah substations selesai.

Sama dengan extract_sulawesi_generators.py: OSM plant adalah sumber otoritatif
(sudah punya koordinat presisi). Tidak ada fuzzy matching atau override
koordinat — extractor hanya mengkategorikan tipe PLT dan meng-assign provinsi
+ region berdasarkan bbox + centroid tiebreak.

Mirip substations Maluku/Papua, output di-split jadi DUA region — sesuai
karakter Maluku/Papua sebagai kumpulan sistem pulau yang TIDAK
interkoneksi:

  region 'maluku' : Maluku + Maluku Utara   -> system 'Maluku'
  region 'papua'  : Papua + Papua Barat     -> system 'Papua'

Bbox catatan penting:
  - Maluku Utara lon_min 125.30 (bukan 123.90 seperti substations) untuk
    EXCLUDE plant Sulawesi Utara yang OSM-nya bocor ke bbox: contoh
    PLTP Lahendong (lon 124.83) ter-include kalau lon_min terlalu barat.
    Sula Islands tepi paling barat (lon ~125.3-126.1) tetap masuk.
  - Maluku lon_min 125.50 untuk exclude potensi plant Sulteng timur
    (Banggai Islands lon ~123-125).
  - Maluku ↔ Papua Barat dan Papua ↔ Papua Barat overlap besar; centroid
    tiebreak menangani (centroid Maluku=Ambon, Papua Barat=Bird's Head,
    Papua=tengah Papua bagian timur).

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)

Output:
  - data/processed/generator_master_maluku.csv + generators_maluku.geojson
  - data/processed/generator_master_papua.csv  + generators_papua.geojson
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"

REGIONS = ["maluku", "papua"]
ID_PREFIX = {"maluku": "GEN-MLK", "papua": "GEN-PAP"}
OUT_CSV = {
    "maluku": ROOT / "data/processed/generator_master_maluku.csv",
    "papua":  ROOT / "data/processed/generator_master_papua.csv",
}
OUT_GJ = {
    "maluku": ROOT / "data/processed/generators_maluku.geojson",
    "papua":  ROOT / "data/processed/generators_papua.geojson",
}

# (provinsi, region, system, bbox, centroid)
#   bbox     = (lat_min, lon_min, lat_max, lon_max)
#   centroid = (lat, lon) — pusat massa provinsi, tiebreak overlap bbox.
PROVINCES = [
    # Maluku Utara — Ternate-Tidore-Halmahera-Morotai-Sula. lon_min 125.30
    # exclude Lahendong (lon 124.83) & plant Sulut lain. Sula Islands tepi
    # barat (lon ~125.3-126.1) tetap masuk.
    ("Maluku Utara", "maluku", "Maluku", (-2.60, 125.30,  3.10, 129.60), ( 0.80, 127.50)),
    # Maluku — Buru-Seram-Ambon-Banda-Kei-Tanimbar-Aru. lon_min 125.50
    # exclude potensi plant Sulteng timur (Banggai lon ~123-125).
    ("Maluku",       "maluku", "Maluku", (-8.80, 125.50, -2.65, 135.80), (-3.70, 128.20)),
    # Papua Barat — Bird's Head (Sorong-Manokwari-Raja Ampat-Bintuni-Fakfak).
    # Termasuk Papua Barat Daya yang di RUPTL 2025 masih digabung.
    ("Papua Barat",  "papua",  "Papua",  (-4.50, 129.00,  1.20, 135.20), (-0.86, 132.50)),
    # Papua — bagian timur (Jayapura-Wamena-Timika-Merauke-Biak-Nabire).
    ("Papua",        "papua",  "Papua",  (-9.60, 134.00,  0.70, 141.20), (-3.50, 138.50)),
]

# Urutan provinsi unik (untuk ringkasan per-provinsi).
PROVINCE_ORDER = []
for _p, _r, _s, _b, _c in PROVINCES:
    if _p not in PROVINCE_ORDER:
        PROVINCE_ORDER.append(_p)

# Override assign per osm_id — cadangan kalau bbox+centroid masih salah.
# Format: 'way/123' / 'node/123' -> (provinsi, region, sistem).
PROVINCE_OVERRIDE = {
    # contoh: "way/123456789": ("Maluku", "maluku", "Maluku"),
}


def assign_province(lat, lon):
    """Return (province, region, system), atau (None,None,None) kalau luar region.

    Kumpulkan semua entri PROVINCES yang bbox-nya memuat titik; kalau >1,
    pilih entri yang centroid-nya paling dekat ke titik. Pakai pola
    multi-bbox + centroid tiebreak, sama dengan Sulawesi generators.
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
    """Tentukan tipe PLT. Prefer prefix nama (PLTx), fallback ke OSM tag.

    Tambahan untuk Maluku/Papua: kenali prefix PLTMG (Pembangkit Listrik
    Tenaga Mesin Gas — banyak dipakai di Indonesia Timur untuk gas engine
    plant), supaya tidak salah jadi PLTGU/PLTG.
    """
    name = (props.get('name') or '').strip()
    method = (props.get('plant:method') or '').lower()
    source = (props.get('plant:source') or '').lower()

    # PLTMG = gas engine; PLTGU = combined cycle; PLTG = open cycle.
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
    """Parse plant:output:electricity ke MW. Contoh: '660 MW', '660000 kW',
    '600 kWp', '75 kW'. 'yes' / non-numeric -> None."""
    if not v:
        return None
    s = str(v).strip().lower().replace(' ', '').replace(',', '.')
    # 'kwp' (solar peak) treat as kw
    s = s.replace('kwp', 'kw')
    m = re.match(r'^([\d\.]+)(mw|kw|gw)?$', s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or 'mw'
    if unit == 'kw':
        val /= 1000
    elif unit == 'gw':
        val *= 1000
    return round(val, 3)


def load_plants():
    """Load OSM plants di region Maluku/Papua dengan dua-pass dedup.

    Pass 1 (konsisten dgn region lain): dedupe persis (round 4 desimal,
    ~11 m) — drop entri kedua dst dengan koord identik.

    Pass 2 (khusus Maluku/Papua): cluster di 3 desimal (~111 m); kalau satu
    cluster memuat entri bernama DAN entri (unnamed)/duplikat-nama,
    pertahankan entri bernama saja. Motivasi: dataset OSM Maluku/Papua punya
    pola cluster tagging — contoh PLTD Fakfak ter-tag 6x (2 bernama + 4
    unnamed) dalam radius 30 m, dan PLN-tagged "(unnamed)" plant menempel di
    plant utama yang sudah punya nama. Pass 2 menghindari overcount tanpa
    merge unit pembangkit yang valid berbeda (mis. Weda Bay 1-4 vs 5-8 vs
    9-11 yang nama-beda → tetap dipisah).
    """
    gj = json.load(open(PLANTS_GJ))
    seen_coords = {}
    pass1 = []
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
            province, region, system = PROVINCE_OVERRIDE[osm_id]
            n_override += 1
        else:
            province, region, system = assign_province(lat, lon)
        if province is None:
            skipped_outside += 1
            continue
        key = (round(lat, 4), round(lon, 4))
        if key in seen_coords:
            skipped_duplicate += 1
            continue
        seen_coords[key] = True
        pass1.append((f, lat, lon, province, region, system))

    # Pass 2: cluster dedup
    from collections import defaultdict
    clusters = defaultdict(list)
    for item in pass1:
        f, lat, lon, _, _, _ = item
        ck = (round(lat, 3), round(lon, 3))
        clusters[ck].append(item)

    plants = []
    skipped_cluster = 0
    for ck, group in clusters.items():
        if len(group) == 1:
            plants.append(group[0])
            continue
        # Grup per nama (normalized lowercase, '' untuk unnamed)
        by_name = defaultdict(list)
        for item in group:
            f = item[0]
            nm = ((f.get('properties', {}).get('name') or '').strip().lower())
            by_name[nm].append(item)
        has_named = any(nm for nm in by_name)
        for nm, items in by_name.items():
            if nm == '' and has_named:
                # Cluster punya entri bernama → drop entri (unnamed) yang nempel.
                skipped_cluster += len(items)
                continue
            if len(items) == 1:
                plants.append(items[0])
            else:
                # Multiple entri nama identik → pilih yang punya capacity,
                # fallback ke yang pertama.
                def _cap(it):
                    return parse_capacity_mw(
                        it[0].get('properties', {}).get('plant:output:electricity'))
                best = next((it for it in items if _cap(it) is not None), items[0])
                plants.append(best)
                skipped_cluster += len(items) - 1

    print(f"  skipped (luar region Maluku/Papua): {skipped_outside}")
    print(f"  skipped (duplicate coords 4-dec):   {skipped_duplicate}")
    print(f"  skipped (cluster dedup 3-dec):      {skipped_cluster}")
    if n_override:
        print(f"  province override di-apply:         {n_override}")
    return plants


def run():
    plants = load_plants()
    print(f"OSM plants di region Maluku/Papua: {len(plants)}")

    rows_by_region = {r: [] for r in REGIONS}
    next_id = {r: 1 for r in REGIONS}
    by_system_type = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'mw': 0.0}))
    by_province = defaultdict(lambda: {'count': 0, 'mw': 0.0})

    for f, lat, lon, province, region, system in plants:
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
            'id': f'{ID_PREFIX[region]}-{next_id[region]:04d}',
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
        rows_by_region[region].append(row)
        next_id[region] += 1
        if cap_mw:
            by_system_type[system][plt_type]['count'] += 1
            by_system_type[system][plt_type]['mw'] += cap_mw
            by_province[province]['count'] += 1
            by_province[province]['mw'] += cap_mw

    # Write per-region CSV + GeoJSON
    grand_rows = 0
    grand_features = 0
    for region in REGIONS:
        rows = rows_by_region[region]
        if not rows:
            print(f"\nERROR: tidak ada plant di region {region}.")
            continue
        with open(OUT_CSV[region], 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
        features = []
        for r in rows:
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
                'properties': {k: v for k, v in r.items() if k not in ('lat', 'lon')}
            })
        with open(OUT_GJ[region], 'w') as f:
            json.dump({'type': 'FeatureCollection', 'features': features}, f, ensure_ascii=False)
        print(f"\nWritten: {OUT_CSV[region]} ({len(rows)} rows)")
        print(f"Written: {OUT_GJ[region]} ({len(features)} features)")
        grand_rows += len(rows)
        grand_features += len(features)

    # Summary: kategorisasi per sistem (region)
    print(f"\n=== Kategorisasi pembangkit ({grand_rows} plant) ===")
    print(f"\n{'System':<10}{'Type':<10}{'Count':>7}{'Total MW':>12}")
    grand_count = 0
    grand_mw = 0.0
    for system in ['Maluku', 'Papua']:
        if system not in by_system_type:
            continue
        for t, agg in sorted(by_system_type[system].items(), key=lambda x: -x[1]['mw']):
            print(f"{system:<10}{t:<10}{agg['count']:>7}{agg['mw']:>12,.2f}")
            grand_count += agg['count']
            grand_mw += agg['mw']
    print(f"\n{'TOTAL':<20}{grand_count:>7}{grand_mw:>12,.2f}")

    # Summary per provinsi
    print(f"\n=== Per provinsi (plant dengan kapasitas) ===")
    print(f"{'Provinsi':<16}{'Count':>7}{'Total MW':>12}")
    for name in PROVINCE_ORDER:
        if name not in by_province:
            continue
        agg = by_province[name]
        print(f"{name:<16}{agg['count']:>7}{agg['mw']:>12,.2f}")

    # Review flags total
    n_no_name = sum(1 for r in rows_by_region['maluku'] + rows_by_region['papua']
                    if 'NO_NAME' in r['review_flag'])
    n_no_cap = sum(1 for r in rows_by_region['maluku'] + rows_by_region['papua']
                   if 'NO_CAPACITY' in r['review_flag'])
    n_no_type = sum(1 for r in rows_by_region['maluku'] + rows_by_region['papua']
                    if 'NO_TYPE' in r['review_flag'])
    print(f"\n=== Review flags ===")
    print(f"  NO_NAME:     {n_no_name}")
    print(f"  NO_CAPACITY: {n_no_cap}")
    print(f"  NO_TYPE:     {n_no_type}")


if __name__ == '__main__':
    run()
