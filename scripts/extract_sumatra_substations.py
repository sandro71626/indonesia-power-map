"""
Ekstrak daftar Gardu Induk Eksisting dari Lampiran A (Sumatra + sistem
isolated) RUPTL 2025-2034, match dengan koordinat OSM. Hasil:
  - data/processed/substation_master_sumatra.csv
  - data/processed/substations_sumatra.geojson

Cakupan: 10 provinsi
  - 8 provinsi sistem Sumatra interkoneksi (Aceh, Sumatera Utara, Sumatera
    Barat, Riau, Jambi, Sumatera Selatan, Bengkulu, Lampung) — backbone 275 kV
  - 1 sistem isolated Batam–Bintan (Kepulauan Riau)
  - 1 sistem isolated Bangka & Belitung (Kep. Bangka Belitung)

Lihat docs/naming_conventions.md: 'Sumatra' = label region/sistem (English),
sedangkan 'Sumatera Utara/Barat/Selatan' tetap ejaan resmi BPS untuk nama
administratif provinsi.

Sumber:
  - data/raw/sources/RUPTL-2025-2034.pdf (Tabel Ax.4 per provinsi)
  - data/geojson/indonesia_substations.geojson (OSM)
  - data/overrides/substation_overrides.csv (shared dgn JAMALI; matched by
    pasangan ruptl_name + province)

Threshold matching identik dengan JAMALI iterasi 2:
  - score >= 0.85 → matched via fuzzy
  - score <  0.85 → UNMATCHED (kecuali ada override)
  - override apply pertama, mengalahkan fuzzy match

Catatan format heading RUPTL Lampiran A:
  - Mayoritas: "Tabel A<n>.4. Realisasi Kapasitas Trafo Gardu Induk (MVA)"
  - A8 (Babel) beda: "Tabel A8.4. Kapasitas Trafo Gardu Induk Eksisting"
  Extractor handle keduanya dengan regex fleksibel (kata "Trafo" wajib,
  "Realisasi" dan "Eksisting" opsional).
"""
import re
import json
import csv
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUPTL = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"
OSM_SUB = ROOT / "data/geojson/indonesia_substations.geojson"
OVERRIDES = ROOT / "data/overrides/substation_overrides.csv"
OUT_CSV = ROOT / "data/processed/substation_master_sumatra.csv"
OUT_GJ = ROOT / "data/processed/substations_sumatra.geojson"

MATCH_THRESHOLD = 0.85
ID_PREFIX = "GI-SMT"

# Per-provinsi: tabel ID, nama, system field, start/end page Lampiran A,
# bbox OSM (lat_min, lon_min, lat_max, lon_max).
# Page range diturunkan dari probe scripts/_probe_ruptl_tables.py.
#
# CATATAN URUTAN: RUPTL Lampiran A tidak mengikuti urutan alfabetis.
# Setelah Aceh & Sumut, RUPTL meloncat ke Riau → Kepri → Babel (timur), baru
# balik ke Sumbar → Jambi → Sumsel (tengah/barat), lalu Bengkulu → Lampung.
# Verifikasi ground-truth dilakukan dengan mencocokkan nama GI yang ter-extract
# ke nama kota/kabupaten administratif provinsi (mis. Duri, Dumai, Perawang
# untuk Riau di A3; Padang, Maninjau, Bungus untuk Sumbar di A6).
PROVINCES = [
    ("A1",  "Aceh",                       "Sumatra",  601, 616, ( 2.00,  94.90,  6.10,  98.20)),
    ("A2",  "Sumatera Utara",             "Sumatra",  617, 632, ( 0.90,  97.00,  4.50, 100.60)),
    ("A3",  "Riau",                       "Sumatra",  633, 645, (-1.50, 100.00,  3.00, 103.70)),
    ("A4",  "Kepulauan Riau",             "Batam",    646, 658, (-0.20, 103.20,  1.55, 105.00)),
    ("A5",  "Kepulauan Bangka Belitung",  "Babel",    659, 669, (-3.70, 105.00, -1.30, 108.50)),
    ("A6",  "Sumatera Barat",             "Sumatra",  670, 680, (-3.50,  98.50,  0.60, 102.00)),
    ("A7",  "Jambi",                      "Sumatra",  681, 691, (-2.80, 101.00, -0.50, 104.50)),
    ("A8",  "Sumatera Selatan",           "Sumatra",  692, 704, (-4.80, 102.30, -1.00, 106.20)),
    ("A9",  "Bengkulu",                   "Sumatra",  705, 715, (-5.50, 101.00, -2.00, 104.00)),
    ("A10", "Lampung",                    "Sumatra",  716, 729, (-6.00, 103.50, -3.60, 106.00)),
]


def extract_table(pdf_path, table_id, start_page, end_page):
    """Ekstrak tabel Trafo Gardu Induk dari range halaman tertentu.

    Lampiran A pakai phrasing 'Realisasi Kapasitas Trafo Gardu Induk' (atau
    'Kapasitas Trafo Gardu Induk Eksisting' di A8). Heading wajib mengandung
    'Trafo' + 'Gardu Induk'; modifier 'Realisasi' / 'Eksisting' opsional.
    """
    out = subprocess.run(
        ['pdftotext', '-layout', '-f', str(start_page), '-l', str(end_page),
         str(pdf_path), '-'],
        capture_output=True, text=True
    ).stdout

    table_num = table_id.replace("A", "")  # "A1" -> "1"
    # Heading: "Tabel A<n>.<m>[.] [Realisasi] Kapasitas Trafo Gardu Induk [Eksisting]..."
    heading_pat = re.compile(
        rf'Tabel\s+A{table_num}\.(\d+)\.?\s*(?:Realisasi\s+)?Kapasitas\s+Trafo\s+Gardu\s+Induk(?:\s+Eksisting)?[^\n]*\n'
    )
    m = heading_pat.search(out)
    if not m:
        return []
    found_subtable = int(m.group(1))

    # Boundary: heading tabel berikutnya (A<n>.<found+1>)
    end_pat = re.compile(rf'Tabel\s+A{table_num}\.{found_subtable + 1}\b')
    end_m = end_pat.search(out, m.end())
    block = out[m.end():end_m.start() if end_m else len(out)]

    rows = []
    # Pattern row: <num> <name multi-words> <volt/volt> <trafo> <capacity>
    row_pat = re.compile(
        r'^\s*(\d{1,3})\s+(.+?)\s+(\d{2,3}\s*/\s*\d{2,3})\s+(\d+)\s+([\d\.,]+)\s*$'
    )
    for line in block.split('\n'):
        s = line.rstrip()
        if not s:
            continue
        if 'Tegangan' in s or 'Total Kapasitas' in s or 'Jumlah Trafo' in s or 'Nama GI' in s:
            continue
        # Skip pagination markers seperti "A -16"
        if re.match(r'^\s*A\s*-?\s*\d+\s*$', s):
            continue
        if re.search(r'^\s*(Total|Jumlah)\b', s, re.IGNORECASE):
            continue
        rm = row_pat.match(s)
        if rm:
            cap = rm.group(5).replace('.', '').replace(',', '.')
            try:
                cap_f = float(cap)
            except ValueError:
                cap_f = None
            rows.append({
                'src_no': int(rm.group(1)),
                'name': rm.group(2).strip(),
                'voltage': re.sub(r'\s+', '', rm.group(3)),
                'trafo_count': int(rm.group(4)),
                'capacity_mva': cap_f,
            })
    return rows


def parse_voltage_osm(v):
    if not v:
        return 0
    parts = re.split(r'[;,/]', str(v))
    vals = [int(p.strip()) for p in parts if p.strip().isdigit()]
    return max(vals) / 1000 if vals else 0


def normalize_name(s):
    s = s.lower()
    s = re.sub(r'[\(\)]', ' ', s)
    s = re.sub(r'[/\.\-]', ' ', s)
    s = s.replace('gardu induk', '').replace('gitet', '').replace('gis', '').replace(' gi ', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def load_osm_substations():
    gj = json.load(open(OSM_SUB))
    items = []
    for f in gj['features']:
        g = f.get('geometry')
        if not g or g['type'] != 'Point':
            continue
        lon, lat = g['coordinates'][:2]
        props = f.get('properties', {})
        name = props.get('name') or props.get('name:en') or ''
        if not name:
            continue
        items.append({
            'osm_id': props.get('@id', ''),
            'name': name,
            'lat': lat, 'lon': lon,
            'voltage_kv': parse_voltage_osm(props.get('voltage', '')),
        })
    return items


def filter_by_bbox(items, bbox):
    lat_min, lon_min, lat_max, lon_max = bbox
    return [x for x in items if lat_min <= x['lat'] <= lat_max
                              and lon_min <= x['lon'] <= lon_max]


def best_match(target_name, candidates):
    tn = normalize_name(target_name)
    if not tn:
        return None, 0.0
    best, best_score = None, 0.0
    for c in candidates:
        cn = normalize_name(c['name'])
        if not cn:
            continue
        if tn == cn:
            score = 1.0
        elif tn in cn or cn in tn:
            t_tokens = set(tn.split())
            c_tokens = set(cn.split())
            overlap = len(t_tokens & c_tokens) / max(len(t_tokens), 1)
            score = max(0.92, 0.7 + 0.25 * overlap)
        else:
            score = SequenceMatcher(None, tn, cn).ratio()
        if score > best_score:
            best_score = score
            best = c
    return best, best_score


def load_overrides():
    """Load override CSV (shared dengan JAMALI). Match by (ruptl_name, province)."""
    overrides = {}
    if not OVERRIDES.exists():
        return overrides
    with open(OVERRIDES) as f:
        for r in csv.DictReader(f):
            key = (r['ruptl_name'].strip(), r['province'].strip())
            overrides[key] = {
                'coord_source': r['coord_source'].strip(),
                'osm_id': r['osm_id'].strip(),
                'osm_name': r['osm_name'].strip(),
                'lat': float(r['lat']),
                'lon': float(r['lon']),
                'notes': r.get('notes', '').strip(),
            }
    return overrides


def run():
    osm_all = load_osm_substations()
    overrides = load_overrides()
    print(f"OSM substations (named): {len(osm_all)}")
    print(f"Manual overrides loaded: {len(overrides)} (filter ke provinsi Sumatra)")

    # Filter overrides ke provinsi Sumatra saja (untuk warning stale yang akurat)
    sumatra_provinces = {p[1] for p in PROVINCES}
    overrides_relevant = {k: v for k, v in overrides.items() if k[1] in sumatra_provinces}
    print(f"  Override entries untuk Sumatra region: {len(overrides_relevant)}")

    out_rows = []
    summary = []
    next_id = 1
    used_overrides = set()

    for pid, prov_name, system, start, end, bbox in PROVINCES:
        rupt_rows = extract_table(RUPTL, pid, start, end)
        osm_prov = filter_by_bbox(osm_all, bbox)

        matched_fuzzy = 0
        matched_override = 0
        for r in rupt_rows:
            row = {
                'id': f'{ID_PREFIX}-{next_id:04d}',
                'name': r['name'],
                'voltage': r['voltage'],
                'trafo_count': r['trafo_count'],
                'capacity_mva': r['capacity_mva'],
                'province': prov_name,
                'system': system,
                'osm_id': '',
                'osm_name': '',
                'lat': '',
                'lon': '',
                'match_score': 0.0,
                'match_source': '',
                'review_flag': '',
                'source_id': 'RUPTL-2025-2034',
                'source_table': f'Tabel {pid}.4',
            }
            ov_key = (r['name'].strip(), prov_name)
            if ov_key in overrides:
                ov = overrides[ov_key]
                row['osm_id'] = ov['osm_id']
                row['osm_name'] = ov['osm_name']
                row['lat'] = ov['lat']
                row['lon'] = ov['lon']
                row['match_score'] = 1.0
                row['match_source'] = f"override:{ov['coord_source']}"
                used_overrides.add(ov_key)
                matched_override += 1
            else:
                cand, score = best_match(r['name'], osm_prov)
                row['match_score'] = round(score, 2) if cand else 0.0
                if cand and score >= MATCH_THRESHOLD:
                    row['osm_id'] = cand['osm_id']
                    row['osm_name'] = cand['name']
                    row['lat'] = cand['lat']
                    row['lon'] = cand['lon']
                    row['match_source'] = 'osm_fuzzy'
                    matched_fuzzy += 1
                else:
                    row['review_flag'] = 'UNMATCHED'
            out_rows.append(row)
            next_id += 1

        summary.append({
            'pid': pid, 'province': prov_name, 'system': system,
            'rupt_count': len(rupt_rows),
            'osm_in_bbox': len(osm_prov),
            'matched_fuzzy': matched_fuzzy,
            'matched_override': matched_override,
            'unmatched': len(rupt_rows) - matched_fuzzy - matched_override,
        })

    # Warn override Sumatra yang gak dipakai (mungkin nama berubah)
    stale = set(overrides_relevant.keys()) - used_overrides
    if stale:
        print("\nWARNING: override entries Sumatra tidak terpakai:")
        for k in sorted(stale):
            print(f"  - {k}")

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as f:
        if not out_rows:
            print("\nERROR: out_rows kosong — kemungkinan extraction gagal untuk semua provinsi.")
            return
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    # Write GeoJSON
    features = []
    for r in out_rows:
        if r['lat'] == '' or r['lon'] == '':
            continue
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
            'properties': {k: v for k, v in r.items() if k not in ('lat', 'lon')}
        })
    geojson = {'type': 'FeatureCollection', 'features': features}
    with open(OUT_GJ, 'w') as f:
        json.dump(geojson, f, ensure_ascii=False)

    # Summary
    print(f"\n{'PID':<4}{'Province':<25}{'System':<10}{'RUPTL':>7}{'OSM_bbox':>10}{'Fuzzy':>7}{'Override':>10}{'Unmatch':>9}")
    total = {'rupt_count': 0, 'matched_fuzzy': 0, 'matched_override': 0, 'unmatched': 0}
    for s in summary:
        print(f"{s['pid']:<4}{s['province']:<25}{s['system']:<10}"
              f"{s['rupt_count']:>7}{s['osm_in_bbox']:>10}"
              f"{s['matched_fuzzy']:>7}{s['matched_override']:>10}{s['unmatched']:>9}")
        for k in total:
            total[k] += s[k]
    matched_total = total['matched_fuzzy'] + total['matched_override']
    rate = matched_total / total['rupt_count'] * 100 if total['rupt_count'] else 0
    print(f"{'':<4}{'TOTAL':<25}{'':<10}{total['rupt_count']:>7}{'':>10}"
          f"{total['matched_fuzzy']:>7}{total['matched_override']:>10}{total['unmatched']:>9}")
    print(f"\nMatch rate: {matched_total}/{total['rupt_count']} = {rate:.1f}%")
    print(f"  via fuzzy (score >= {MATCH_THRESHOLD}): {total['matched_fuzzy']}")
    print(f"  via manual override:                    {total['matched_override']}")
    print(f"  unmatched:                              {total['unmatched']}")

    # Breakdown per system
    print("\nBreakdown per system:")
    sys_total = {}
    for s in summary:
        st = sys_total.setdefault(s['system'], {'rupt': 0, 'matched': 0, 'unmatched': 0})
        st['rupt'] += s['rupt_count']
        st['matched'] += s['matched_fuzzy'] + s['matched_override']
        st['unmatched'] += s['unmatched']
    for sys_name, st in sys_total.items():
        r = st['matched'] / st['rupt'] * 100 if st['rupt'] else 0
        print(f"  {sys_name:<10} matched={st['matched']:>3} / rupt={st['rupt']:>3} ({r:.1f}%)  unmatched={st['unmatched']}")

    print(f"\nWritten: {OUT_CSV}")
    print(f"Written: {OUT_GJ} ({len(features)} features)")


if __name__ == '__main__':
    run()
