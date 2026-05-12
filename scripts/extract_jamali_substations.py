"""
Ekstrak daftar Gardu Induk Eksisting dari Lampiran B (Jamali) RUPTL 2025-2034,
match dengan koordinat OSM, hasil:
  - data/processed/substation_master_jamali.csv
  - data/processed/substations_jamali.geojson

Sumber:
  - data/raw/sources/RUPTL-2025-2034.pdf (Tabel Bx.4 per provinsi)
  - data/geojson/indonesia_substations.geojson (OSM)
"""
import re
import json
import csv
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path("/sessions/pensive-beautiful-bohr/mnt/Indonesia Power Map")
RUPTL = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"
OSM_SUB = ROOT / "data/geojson/indonesia_substations.geojson"
OUT_CSV = ROOT / "data/processed/substation_master_jamali.csv"
OUT_GJ = ROOT / "data/processed/substations_jamali.geojson"

# Per-provinsi: page range Lampiran B + bbox OSM
# bbox: (lat_min, lon_min, lat_max, lon_max)
PROVINCES = [
    ("B1", "DKI Jakarta",   "Jamali", 812, 823, (-6.45, 106.65, -6.05, 107.05)),
    ("B2", "Banten",        "Jamali", 824, 840, (-7.05, 105.10, -5.85, 106.85)),
    ("B3", "Jawa Barat",    "Jamali", 841, 873, (-7.85, 106.30, -5.95, 108.85)),
    ("B4", "Jawa Tengah",   "Jamali", 874, 897, (-8.30, 108.55, -6.30, 111.70)),
    ("B5", "DIY",           "Jamali", 898, 904, (-8.25, 110.00, -7.50, 110.85)),
    ("B6", "Jawa Timur",    "Jamali", 905, 937, (-8.80, 110.85, -6.60, 114.65)),
    ("B7", "Bali",          "Jamali", 938, 950, (-8.95, 114.40, -8.00, 115.75)),
]


def extract_table(pdf_path, table_id, start_page, end_page):
    """Ekstrak tabel "Gardu Induk Eksisting" dari range halaman tertentu.

    Beberapa provinsi pakai nomor tabel berbeda (DIY: B5.3, Bali: B7.4 tanpa
    'Realisasi'). Strategi: cari heading apapun yang punya pola
    'Tabel B<n>.<m> ... Gardu Induk Eksisting' dan ambil yang pertama.
    """
    out = subprocess.run(
        ['pdftotext', '-layout', '-f', str(start_page), '-l', str(end_page),
         str(pdf_path), '-'],
        capture_output=True, text=True
    ).stdout

    table_num = table_id.replace("B", "")  # "B1" -> "1"
    # Cari heading: "Tabel B<n>.<m>[.] [Realisasi] Kapasitas Gardu Induk Eksisting"
    # atau "Tabel B<n>.<m> Kapasitas Gardu Induk Eksisting"
    heading_pat = re.compile(
        rf'Tabel B{table_num}\.(\d+)\.?\s*(?:Realisasi\s+)?Kapasitas\s+Gardu\s+Induk\s+Eksisting[^\n]*\n'
    )
    m = heading_pat.search(out)
    if not m:
        return []
    found_subtable = int(m.group(1))  # e.g. 3 or 4

    # Boundary: heading tabel berikutnya (B<n>.<found+1>)
    end_pat = re.compile(rf'Tabel B{table_num}\.{found_subtable + 1}\b')
    end_m = end_pat.search(out, m.end())
    block = out[m.end():end_m.start() if end_m else len(out)]

    rows = []
    # Pattern row: <num> <name multi-words> <volt/volt> <trafo> <capacity>
    # Volt: 70/20, 150/20, 500/150, etc. (allow possible space variations)
    row_pat = re.compile(
        r'^\s*(\d{1,3})\s+(.+?)\s+(\d{2,3}\s*/\s*\d{2,3})\s+(\d+)\s+([\d\.,]+)\s*$'
    )
    for line in block.split('\n'):
        s = line.rstrip()
        if not s:
            continue
        # Skip header reprints
        if 'Tegangan' in s or 'Total Kapasitas' in s or 'Jumlah Trafo' in s or 'Nama GI' in s:
            continue
        # Skip pagination markers like "B -16"
        if re.match(r'^\s*B\s*-?\s*\d+\s*$', s):
            continue
        # Skip "Total" / "Jumlah" lines
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
    """OSM 'voltage' tag -> max kV value."""
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
    """Load OSM substations indexed by feature props."""
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
    """Fuzzy match. Return (cand, score) or (None, 0)."""
    tn = normalize_name(target_name)
    if not tn:
        return None, 0.0
    best, best_score = None, 0.0
    for c in candidates:
        cn = normalize_name(c['name'])
        if not cn:
            continue
        # Substring boost
        if tn == cn:
            score = 1.0
        elif tn in cn or cn in tn:
            # token overlap on any word in target
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


def run():
    osm_all = load_osm_substations()
    print(f"OSM substations (named): {len(osm_all)}")

    out_rows = []
    summary = []
    next_id = 1

    for pid, prov_name, system, start, end, bbox in PROVINCES:
        rupt_rows = extract_table(RUPTL, pid, start, end)
        osm_prov = filter_by_bbox(osm_all, bbox)

        matched = 0
        weak = 0  # 0.65 <= score < 0.85
        for r in rupt_rows:
            cand, score = best_match(r['name'], osm_prov)
            row = {
                'id': f'GI-JMB-{next_id:04d}',
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
                'match_score': round(score, 2) if cand else 0.0,
                'review_flag': '',
                'source_id': 'RUPTL-2025-2034',
                'source_table': f'Tabel {pid}.4',
            }
            if cand and score >= 0.65:
                row['osm_id'] = cand['osm_id']
                row['osm_name'] = cand['name']
                row['lat'] = cand['lat']
                row['lon'] = cand['lon']
                matched += 1
                if score < 0.85:
                    row['review_flag'] = 'LOW_SCORE'
                    weak += 1
            else:
                row['review_flag'] = 'UNMATCHED'
            out_rows.append(row)
            next_id += 1

        summary.append({
            'pid': pid, 'province': prov_name,
            'rupt_count': len(rupt_rows),
            'osm_in_bbox': len(osm_prov),
            'matched': matched,
            'unmatched': len(rupt_rows) - matched,
            'low_score': weak,
        })

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    # Write GeoJSON (only matched rows with coordinates)
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

    # Print summary
    print(f"\n{'PID':<4}{'Province':<14}{'RUPTL':>7}{'OSM_bbox':>10}{'Match':>8}{'Unmatch':>9}{'LowScore':>10}")
    total = {'rupt_count': 0, 'matched': 0, 'unmatched': 0, 'low_score': 0}
    for s in summary:
        print(f"{s['pid']:<4}{s['province']:<14}{s['rupt_count']:>7}{s['osm_in_bbox']:>10}{s['matched']:>8}{s['unmatched']:>9}{s['low_score']:>10}")
        for k in total:
            total[k] += s[k]
    print(f"{'':<4}{'TOTAL':<14}{total['rupt_count']:>7}{'':>10}{total['matched']:>8}{total['unmatched']:>9}{total['low_score']:>10}")
    print(f"\nWritten: {OUT_CSV}")
    print(f"Written: {OUT_GJ} ({len(features)} features)")


if __name__ == '__main__':
    run()
