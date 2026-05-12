"""
Build generator_master_jamali.csv dari 600 pembangkit OSM Indonesia,
filter ke Jamali, kategorisasi (PLTU/PLTA/PLTG/dll), kapasitas, provinsi,
dan validasi terhadap agregat RUPTL Tabel Bx.3.

Sumber:
  - data/geojson/indonesia_plants.geojson (OSM via Overpass)
  - data/raw/sources/RUPTL-2025-2034.pdf (untuk validasi agregat)

Output:
  - data/processed/generator_master_jamali.csv
  - data/processed/generators_jamali.geojson
"""
import re
import json
import csv
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT = Path("/sessions/pensive-beautiful-bohr/mnt/Indonesia Power Map")
PLANTS_GJ = ROOT / "data/geojson/indonesia_plants.geojson"
RUPTL = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"
OUT_CSV = ROOT / "data/processed/generator_master_jamali.csv"
OUT_GJ = ROOT / "data/processed/generators_jamali.geojson"

# Per-provinsi bbox (untuk assign provinsi dari koordinat)
# (lat_min, lon_min, lat_max, lon_max)
PROVINCES = [
    ("DKI Jakarta",  (-6.45, 106.65, -5.40, 107.05)),   # extended north for Kepulauan Seribu
    ("Banten",       (-7.05, 105.10, -5.85, 106.65)),
    ("Jawa Barat",   (-7.85, 106.30, -5.95, 108.85)),
    ("Jawa Tengah",  (-8.30, 108.55, -6.30, 110.95)),   # extended east for Tanjung Jati B (Jepara)
    ("DIY",          (-8.25, 110.00, -7.50, 110.85)),
    ("Jawa Timur",   (-8.85, 110.95, -5.80, 114.65)),   # extended north for Bawean
    ("Bali",         (-8.95, 114.40, -8.00, 115.75)),
]

def assign_province(lat, lon):
    # Prioritas: provinsi terkecil dulu (DKI sebelum Banten/Jabar)
    # Karena bbox DKI sangat sempit, akan match duluan
    for name, (la_min, lo_min, la_max, lo_max) in PROVINCES:
        if la_min <= lat <= la_max and lo_min <= lon <= lo_max:
            return name
    return "Other Jamali"

# OSM plant:source -> Indonesian PLT type
SOURCE_MAP = {
    'hydro': 'PLTA',          # bisa juga PLTM/PLTMH untuk kapasitas kecil
    'coal': 'PLTU',
    'gas': 'PLTG',            # default open cycle; PLTGU jika method=combined_cycle
    'geothermal': 'PLTP',
    'solar': 'PLTS',
    'wind': 'PLTB',
    'diesel': 'PLTD',
    'waste': 'PLTSa',         # PLT Sampah / WTE
    'biomass': 'PLT Biomas',
    'oil': 'PLTD',            # cadangan
}

def derive_type(props, capacity_mw):
    """Tentukan PLT type. Prefer name prefix (PLTx), fallback ke OSM tag."""
    name = (props.get('name') or '').strip()
    method = (props.get('plant:method') or '').lower()
    source = (props.get('plant:source') or '').lower()

    # Coba ambil dari name (PLTU, PLTGU, PLTA, dll)
    m = re.match(r'^(PLT(?:GU|MG|MH|U|G|A|P|S|B|M|D|Sa|Bm))\b', name, re.I)
    if m:
        return m.group(1).upper().replace('PLTSA','PLTSa')

    # Fallback OSM source
    if source == 'gas' and 'combined' in method:
        return 'PLTGU'
    # Hidro kapasitas besar (≥10 MW) = PLTA, 1-10 MW = PLTM, <1 MW = PLTMH
    if source == 'hydro':
        if capacity_mw is not None:
            if capacity_mw >= 10: return 'PLTA'
            elif capacity_mw >= 1: return 'PLTM'
            else: return 'PLTMH'
        return 'PLTA'
    return SOURCE_MAP.get(source, 'Unknown')

def parse_capacity_mw(v):
    """Parse plant:output:electricity to MW. Examples: '660 MW', '660000 kW'."""
    if not v: return None
    s = str(v).strip().lower().replace(' ', '').replace(',', '.')
    m = re.match(r'^([\d\.]+)(mw|kw|gw)?$', s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or 'mw'
    if unit == 'kw': val /= 1000
    elif unit == 'gw': val *= 1000
    return round(val, 2)

def load_jamali_plants():
    """Load OSM plants di area Jamali, exclude Lampung/Sumatera dan dedupe."""
    gj = json.load(open(PLANTS_GJ))
    seen_coords = {}  # (round_lat, round_lon) -> first feature seen
    plants = []
    skipped_lampung = 0
    skipped_duplicate = 0
    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'Point':
            continue
        lon, lat = g['coordinates'][:2]
        # Jamali outer bbox
        if not (-9.0 <= lat <= -5.3 and 105.0 <= lon <= 115.8):
            continue
        # Exclude Lampung/Sumatera: lat > -6.0 dan lon < 105.7 = sisi barat Selat Sunda
        if lat > -6.0 and lon < 105.7:
            skipped_lampung += 1
            continue
        # Dedupe by coords (rounded to 4 decimals = ~10m precision)
        key = (round(lat, 4), round(lon, 4))
        if key in seen_coords:
            skipped_duplicate += 1
            continue
        seen_coords[key] = True
        plants.append((f, lat, lon))
    print(f"  skipped (Sumatera/Lampung): {skipped_lampung}")
    print(f"  skipped (duplicates): {skipped_duplicate}")
    return plants

def extract_ruptl_aggregates():
    """Extract Tabel Bx.3 'Rekap Pembangkit Tenaga Listrik Eksisting' per provinsi
    untuk validation. Format:
       Jenis Pembangkit   Sistem      Jumlah Unit    Total Kapasitas (MW)   Daya Mampu Netto
    """
    out = subprocess.run(['pdftotext','-layout','-f','811','-l','950',str(RUPTL),'-'],
                         capture_output=True, text=True).stdout
    # Lampiran B subbab → table number
    # B1.3, B2.3, B3.3, B4.3, B5.<?>, B6.3, B7.3
    # Actually for B5 the rekap pembangkit might be implicit. Skip for simplicity.
    aggregates = defaultdict(lambda: defaultdict(lambda: {'unit': 0, 'mw': 0.0}))
    province_map = {'B1':'DKI Jakarta','B2':'Banten','B3':'Jawa Barat','B4':'Jawa Tengah',
                    'B5':'DIY','B6':'Jawa Timur','B7':'Bali'}
    # Cari tabel rekap pembangkit eksisting di setiap subbab
    pattern = re.compile(
        r'Tabel (B[1-7])\.\d+\.?\s*Rekap[^P]*Pembangkit[^E]*Eksisting[^\n]*\n'
    )
    matches = list(pattern.finditer(out))
    for i, m in enumerate(matches):
        prov_id = m.group(1)
        prov = province_map.get(prov_id)
        end = matches[i+1].start() if i+1 < len(matches) else m.end() + 4000
        block = out[m.end():end]
        # Each row: Jenis Sistem Unit Capacity DMN ...
        # Example: "       PLTU         Jawa Bali        6           105        102        102"
        for line in block.split('\n'):
            s = line.strip()
            row = re.match(
                r'^(PLT(?:GU|MG|MH|U|G|A|P|S|B|M|D|Sa))\s+\S.*?\s+(\d+)\s+([\d\.,]+)\s',
                s
            )
            if row:
                t = row.group(1).upper().replace('PLTSA','PLTSa')
                unit = int(row.group(2))
                mw = float(row.group(3).replace('.','').replace(',','.'))
                aggregates[prov][t]['unit'] += unit
                aggregates[prov][t]['mw'] += mw
    return aggregates


def run():
    plants = load_jamali_plants()
    print(f"OSM plants in Jamali: {len(plants)}")

    rows = []
    by_province_type = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'mw': 0.0}))
    next_id = 1

    for f, lat, lon in plants:
        props = f.get('properties', {})
        name = (props.get('name') or props.get('name:en') or '').strip()
        cap_mw = parse_capacity_mw(props.get('plant:output:electricity'))
        plt_type = derive_type(props, cap_mw)
        province = assign_province(lat, lon)
        operator = (props.get('operator') or '').strip()
        method = (props.get('plant:method') or '').strip()

        flags = []
        if not name: flags.append('NO_NAME')
        if cap_mw is None: flags.append('NO_CAPACITY')
        if plt_type == 'Unknown': flags.append('NO_TYPE')

        row = {
            'id': f'GEN-JMB-{next_id:04d}',
            'name': name or '(unnamed)',
            'type': plt_type,
            'capacity_mw': cap_mw if cap_mw is not None else '',
            'province': province,
            'system': 'Jamali',
            'status': 'existing',  # OSM = current state
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
            by_province_type[province][plt_type]['count'] += 1
            by_province_type[province][plt_type]['mw'] += cap_mw
        next_id += 1

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as f:
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

    # Print summary
    print(f"\n=== OSM plants categorization ({len(rows)} plants) ===")
    print(f"\n{'Province':<14}{'Type':<10}{'Count':>7}{'Total MW':>12}")
    grand_total_mw = 0
    grand_total_count = 0
    for prov in [p[0] for p in PROVINCES] + ['Other Jamali']:
        if prov not in by_province_type: continue
        for t, agg in sorted(by_province_type[prov].items(), key=lambda x: -x[1]['mw']):
            print(f"{prov:<14}{t:<10}{agg['count']:>7}{agg['mw']:>12,.0f}")
            grand_total_mw += agg['mw']
            grand_total_count += agg['count']
    print(f"\n{'TOTAL':<14}{'':<10}{grand_total_count:>7}{grand_total_mw:>12,.0f}")

    # Compare with RUPTL aggregates
    print("\n=== Validation vs RUPTL Tabel Bx.3 aggregates ===")
    ruptl_agg = extract_ruptl_aggregates()
    for prov, by_type in ruptl_agg.items():
        print(f"\n{prov}:")
        print(f"  {'Type':<10}{'RUPTL_unit':>12}{'OSM_count':>11}{'RUPTL_MW':>11}{'OSM_MW':>10}")
        all_types = set(by_type.keys()) | set(by_province_type[prov].keys())
        for t in sorted(all_types):
            r = by_type.get(t, {'unit': 0, 'mw': 0})
            o = by_province_type[prov].get(t, {'count': 0, 'mw': 0})
            print(f"  {t:<10}{r['unit']:>12}{o['count']:>11}{r['mw']:>11,.0f}{o['mw']:>10,.0f}")

    print(f"\nWritten: {OUT_CSV}")
    print(f"Written: {OUT_GJ}")


if __name__ == '__main__':
    run()
