"""
Build generator master untuk region NTB & NTT dari OSM `power=plant`,
kategorisasi PLT type, assign provinsi & region.

Step 6 generators — Nusa Tenggara setelah substations selesai.

Pola identik dgn extract_maluku_papua_generators.py: OSM plant adalah sumber
otoritatif. Tidak ada fuzzy matching atau override koordinat — extractor
hanya mengkategorikan tipe PLT dan assign provinsi/region berdasarkan
bbox + centroid tiebreak.

Mirip substations NTB/NTT, output di-split jadi DUA region:

  region 'ntb' : Nusa Tenggara Barat  -> system 'NTB'
  region 'ntt' : Nusa Tenggara Timur  -> system 'NTT'

NTB punya interkoneksi parsial Lombok-Sumbawa via kabel laut 150 kV Selat
Alas; NTT kumpulan sistem pulau terisolasi. Untuk MVP cukup label makro.

Bbox catatan:
  - NTB lon_min 115.75 — exclude PLTU Celukan Bawang (Bali, lon 114.85),
    PLTG/PLTDG Pesanggaran (Bali, lon 115.21), PLTG Pemaron (Bali, lon
    115.06). Pulau Lombok bagian terbarat (Mataram-Ampenan lon ~116.07)
    tetap masuk.
  - NTT lon_min 119.10 — overlap minimal dgn NTB Timur (Bima lon ~118.7,
    Sape lon ~118.96). Labuan Bajo (lon 119.88) masuk NTT.
  - NTB ↔ NTT bbox overlap di lon 119.10-119.30 — kecil, centroid tiebreak
    menangani.

Cluster dedup dua-pass (warisan Maluku/Papua) tetap di-apply meski NTB/NTT
dataset OSM lebih bersih — defensive untuk kasus PLN-tagged unnamed yang
nempel ke plant bernama.

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)

Output:
  - data/processed/generator_master_ntb.csv + generators_ntb.geojson
  - data/processed/generator_master_ntt.csv + generators_ntt.geojson
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"

REGIONS = ["ntb", "ntt"]
ID_PREFIX = {"ntb": "GEN-NTB", "ntt": "GEN-NTT"}
OUT_CSV = {
    "ntb": ROOT / "data/processed/generator_master_ntb.csv",
    "ntt": ROOT / "data/processed/generator_master_ntt.csv",
}
OUT_GJ = {
    "ntb": ROOT / "data/processed/generators_ntb.geojson",
    "ntt": ROOT / "data/processed/generators_ntt.geojson",
}

# (provinsi, region, system, bbox, centroid)
#   bbox     = (lat_min, lon_min, lat_max, lon_max)
#   centroid = (lat, lon) — pusat massa provinsi, tiebreak overlap bbox.
PROVINCES = [
    # NTB — Lombok + Sumbawa. lon_min 115.75 exclude semua plant Bali
    # (Celukan Bawang lon 114.85, Pesanggaran lon 115.21, Pemaron lon 115.06).
    ("Nusa Tenggara Barat", "ntb", "NTB", (-9.30, 115.75, -8.00, 119.30), (-8.50, 117.50)),
    # NTT — Flores, Sumba, Timor, Alor, Lembata, sub-pulau lain. lon_min
    # 119.10 overlap minimal dgn Bima/Sumbawa Timur (lon ~118.7-119.0).
    ("Nusa Tenggara Timur", "ntt", "NTT", (-11.00, 119.10, -7.90, 125.30), (-9.00, 122.00)),
]

PROVINCE_ORDER = []
for _p, _r, _s, _b, _c in PROVINCES:
    if _p not in PROVINCE_ORDER:
        PROVINCE_ORDER.append(_p)

PROVINCE_OVERRIDE = {
    # contoh: "way/123456789": ("Nusa Tenggara Barat", "ntb", "NTB"),
}


def assign_province(lat, lon):
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


SOURCE_MAP = {
    'hydro': 'PLTA',
    'coal': 'PLTU',
    'gas': 'PLTG',
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

    Catatan NTB/NTT: dataset memuat beberapa PLTS dengan nama panjang
    ("Lombok New Peaker Steam Gas Engine Power Plant") dan typo "PTLD"
    (bukan PLTD). Regex prefix tetap match yang valid; sisanya fallback
    ke source tag.
    """
    name = (props.get('name') or '').strip()
    method = (props.get('plant:method') or '').lower()
    source = (props.get('plant:source') or '').lower()

    m = re.match(r'^(PLT(?:GU|MG|MH|U|G|A|P|S|B|M|D|Sa|Bm))\b', name, re.I)
    if m:
        return m.group(1).upper().replace('PLTSA', 'PLTSa')
    # NTB/NTT: tangani prefix "Komplek PLTMG ..." atau "Unit PLTU ..."
    # yang mendahului PLT-token. Search anywhere in name.
    m = re.search(r'\b(PLT(?:GU|MG|MH|U|G|A|P|S|B|M|D|Sa|Bm))\b', name, re.I)
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
    """Parse plant:output:electricity ke MW. Handle 'kWp' (solar peak)."""
    if not v:
        return None
    s = str(v).strip().lower().replace(' ', '').replace(',', '.')
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
    """Load OSM plants di region NTB/NTT dengan dua-pass dedup.

    Pass 1: dedupe 4-desimal (~11 m).
    Pass 2: cluster 3-desimal (~111 m) — drop entri unnamed yang nempel
    ke plant bernama; keep semua entri valid bernama berbeda.
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
        by_name = defaultdict(list)
        for item in group:
            f = item[0]
            nm = ((f.get('properties', {}).get('name') or '').strip().lower())
            by_name[nm].append(item)
        has_named = any(nm for nm in by_name)
        for nm, items in by_name.items():
            if nm == '' and has_named:
                skipped_cluster += len(items)
                continue
            if len(items) == 1:
                plants.append(items[0])
            else:
                def _cap(it):
                    return parse_capacity_mw(
                        it[0].get('properties', {}).get('plant:output:electricity'))
                best = next((it for it in items if _cap(it) is not None), items[0])
                plants.append(best)
                skipped_cluster += len(items) - 1

    print(f"  skipped (luar region NTB/NTT):    {skipped_outside}")
    print(f"  skipped (duplicate coords 4-dec): {skipped_duplicate}")
    print(f"  skipped (cluster dedup 3-dec):    {skipped_cluster}")
    if n_override:
        print(f"  province override di-apply:       {n_override}")
    return plants


def run():
    plants = load_plants()
    print(f"OSM plants di region NTB/NTT: {len(plants)}")

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

    print(f"\n=== Kategorisasi pembangkit ({grand_rows} plant) ===")
    print(f"\n{'System':<8}{'Type':<10}{'Count':>7}{'Total MW':>12}")
    grand_count = 0
    grand_mw = 0.0
    for system in ['NTB', 'NTT']:
        if system not in by_system_type:
            continue
        for t, agg in sorted(by_system_type[system].items(), key=lambda x: -x[1]['mw']):
            print(f"{system:<8}{t:<10}{agg['count']:>7}{agg['mw']:>12,.2f}")
            grand_count += agg['count']
            grand_mw += agg['mw']
    print(f"\n{'TOTAL':<18}{grand_count:>7}{grand_mw:>12,.2f}")

    print(f"\n=== Per provinsi (plant dengan kapasitas) ===")
    print(f"{'Provinsi':<24}{'Count':>7}{'Total MW':>12}")
    for name in PROVINCE_ORDER:
        if name not in by_province:
            continue
        agg = by_province[name]
        print(f"{name:<24}{agg['count']:>7}{agg['mw']:>12,.2f}")

    n_no_name = sum(1 for r in rows_by_region['ntb'] + rows_by_region['ntt']
                    if 'NO_NAME' in r['review_flag'])
    n_no_cap = sum(1 for r in rows_by_region['ntb'] + rows_by_region['ntt']
                   if 'NO_CAPACITY' in r['review_flag'])
    n_no_type = sum(1 for r in rows_by_region['ntb'] + rows_by_region['ntt']
                    if 'NO_TYPE' in r['review_flag'])
    print(f"\n=== Review flags ===")
    print(f"  NO_NAME:     {n_no_name}")
    print(f"  NO_CAPACITY: {n_no_cap}")
    print(f"  NO_TYPE:     {n_no_type}")


if __name__ == '__main__':
    run()
