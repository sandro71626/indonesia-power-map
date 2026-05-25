"""
Ekstrak daftar Gardu Induk Eksisting dari Lampiran C (Maluku & Papua) RUPTL
2025-2034, match dengan koordinat OSM.

Step 5 mencakup 4 provinsi (Tabel C7-C10), ditulis ke DUA region terpisah —
sesuai pilihan: Maluku & Papua jadi dua region berbeda di peta.

  region 'maluku' : Maluku (C7) + Maluku Utara (C8)      -> system 'Maluku'
  region 'papua'  : Papua (C9) + Papua Barat (C10)       -> system 'Papua'

Berbeda dari region sebelumnya, Maluku & Papua TIDAK punya grid
interkoneksi — keduanya kumpulan sistem pulau yang terisolasi. Karena itu
field `system` cuma dua makro-grup (Maluku / Papua), bukan sub-sistem
interkoneksi. Provinsi tetap jadi field tersendiri.

Satu extractor menulis dua set output:
  - data/processed/substation_master_maluku.csv  + substations_maluku.geojson
  - data/processed/substation_master_papua.csv   + substations_papua.geojson

Sumber:
  - data/raw/sources/RUPTL-2025-2034.pdf (Tabel C7-C10 per provinsi)
  - data/geojson/indonesia_substations.geojson (OSM)
  - data/overrides/substation_overrides.csv (shared; matched by ruptl_name + province)

Threshold matching identik dengan region sebelumnya: score >= 0.85 = matched
via fuzzy; di bawahnya UNMATCHED kecuali ada override. Override apply pertama.

PENTING — format tabel Lampiran C Maluku/Papua MULTI-TEGANGAN: satu GI bisa
membentang beberapa baris (satu baris per level tegangan trafo), dan nama GI
ada di baris TENGAH blok itu — kadang di baris tanpa data sama sekali.
extract_table() menangani ini (lihat docstring fungsinya); trafo_count &
capacity_mva = JUMLAH seluruh level tegangan GI tsb.

Urutan provinsi C7-C10 sudah DIVERIFIKASI lewat probe nama GI
(scripts/_probe_c_provinces.py):
  C7=Maluku, C8=Maluku Utara, C9=Papua, C10=Papua Barat.
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

MATCH_THRESHOLD = 0.85

# Per-region: ID prefix + path output.
ID_PREFIX = {"maluku": "GI-MLK", "papua": "GI-PAP"}
OUT_CSV = {
    "maluku": ROOT / "data/processed/substation_master_maluku.csv",
    "papua":  ROOT / "data/processed/substation_master_papua.csv",
}
OUT_GJ = {
    "maluku": ROOT / "data/processed/substations_maluku.geojson",
    "papua":  ROOT / "data/processed/substations_papua.geojson",
}

# Per-provinsi: tabel ID, nama provinsi, region, system, start/end page
# Lampiran C, bbox OSM (lat_min, lon_min, lat_max, lon_max).
# Page range dari probe scripts/_probe_c_provinces.py:
#   C7 p1063, C8 p1088, C9 p1111, C10 p1135.
PROVINCES = [
    ("C7",  "Maluku",       "maluku", "Maluku", 1063, 1087, (-8.80, 125.00, -2.65, 135.80)),
    ("C8",  "Maluku Utara", "maluku", "Maluku", 1088, 1110, (-2.60, 123.90,  3.10, 129.60)),
    ("C9",  "Papua",        "papua",  "Papua",  1111, 1134, (-9.60, 134.00,  0.70, 141.20)),
    ("C10", "Papua Barat",  "papua",  "Papua",  1135, 1152, (-4.50, 129.00,  1.20, 135.20)),
]

REGIONS = ["maluku", "papua"]


def extract_table(pdf_path, table_id, start_page, end_page):
    """Ekstrak tabel Trafo Gardu Induk; menangani format MULTI-TEGANGAN.

    Heading wajib mengandung 'Trafo' + 'Gardu Induk'; modifier 'Realisasi'
    dan 'Eksisting' opsional.

    Tabel Lampiran C Maluku/Papua memakai layout di mana satu GI bisa
    membentang beberapa baris (satu baris per level tegangan trafo). Sel
    'No' & 'Nama GI' di-merge vertikal, jadi pdftotext me-render nama di
    baris TENGAH blok GI — kadang di baris yang juga memuat data tegangan,
    kadang di baris sendiri tanpa data.

    Strategi:
      1. Klasifikasi tiap baris jadi NAME (ada nomor + nama) atau VOLT
         (hanya tegangan + jumlah trafo + kapasitas, tanpa nomor/nama).
      2. Kelompokkan: tiap NAME "menyerap" baris VOLT di atas & bawahnya
         secara SIMETRIS — karena sel nama di-merge & ter-render di tengah
         blok, jumlah VOLT di atas selalu == jumlah VOLT di bawah.
      3. trafo_count & capacity_mva tiap GI = JUMLAH semua level tegangan;
         voltage = level tegangan unik (desc), mis. '150/70/20'.

    GI satu-tegangan = blok berukuran 1 (curang khusus tidak perlu) — algo
    yang sama menanganinya tanpa kasus khusus.
    """
    out = subprocess.run(
        ['pdftotext', '-layout', '-f', str(start_page), '-l', str(end_page),
         str(pdf_path), '-'],
        capture_output=True, text=True
    ).stdout

    table_num = table_id.replace("C", "")  # "C7" -> "7"
    heading_pat = re.compile(
        rf'Tabel\s+C{table_num}\.(\d+)\.?\s*(?:Realisasi\s+)?Kapasitas\s+Trafo\s+Gardu\s+Induk(?:\s+Eksisting)?[^\n]*\n'
    )
    m = heading_pat.search(out)
    if not m:
        return []
    found_subtable = int(m.group(1))

    end_pat = re.compile(rf'Tabel\s+C{table_num}\.{found_subtable + 1}\b')
    end_m = end_pat.search(out, m.end())
    block = out[m.end():end_m.start() if end_m else len(out)]

    # VOLT = satu baris tegangan: HV/LV  jumlah_trafo  kapasitas.
    VOLT = r'(\d{2,3})\s*/\s*(\d{2,3})\s+(\d+)\s+([\d.,]+)'
    volt_only_re = re.compile(rf'^\s*{VOLT}\s*$')                 # baris VOLT
    name_data_re = re.compile(rf'^\s*(\d{{1,3}})\s+(.+?)\s+{VOLT}\s*$')  # NAME + data
    name_only_re = re.compile(r'^\s*(\d{1,3})\s+([A-Za-z(].*?)\s*$')     # NAME tanpa data

    def to_cap(s):
        s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return 0.0

    # --- Tahap 1: klasifikasi tiap baris ---
    entries = []   # {'type':'name'|'volt', 'no'?, 'name'?, 'row': (hv,lv,cnt,cap) | None}
    for line in block.split('\n'):
        s = line.rstrip()
        if not s.strip():
            continue
        if 'Tegangan' in s or 'Total Kapasitas' in s or 'Jumlah Trafo' in s or 'Nama GI' in s:
            continue
        if re.match(r'^\s*C\s*-?\s*\d+\s*$', s):
            continue
        if re.search(r'^\s*(Total|Jumlah)\b', s, re.IGNORECASE):
            continue
        mv = volt_only_re.match(s)
        if mv:
            entries.append({'type': 'volt', 'row': (
                int(mv.group(1)), int(mv.group(2)),
                int(mv.group(3)), to_cap(mv.group(4)))})
            continue
        md = name_data_re.match(s)
        if md:
            entries.append({'type': 'name', 'no': int(md.group(1)),
                            'name': md.group(2).strip(), 'row': (
                                int(md.group(3)), int(md.group(4)),
                                int(md.group(5)), to_cap(md.group(6)))})
            continue
        mo = name_only_re.match(s)
        if mo:
            entries.append({'type': 'name', 'no': int(mo.group(1)),
                            'name': mo.group(2).strip(), 'row': None})
            continue
        # baris lain (catatan kaki dll) diabaikan

    # --- Tahap 2: grup VOLT di sekitar tiap NAME secara simetris ---
    n = len(entries)
    claimed = [False] * n
    rows = []
    for ni in [i for i, e in enumerate(entries) if e['type'] == 'name']:
        claimed[ni] = True
        r = 0
        while True:
            lo, hi = ni - r - 1, ni + r + 1
            if lo < 0 or hi >= n:
                break
            if (entries[lo]['type'] == 'volt' and not claimed[lo]
                    and entries[hi]['type'] == 'volt' and not claimed[hi]):
                claimed[lo] = claimed[hi] = True
                r += 1
            else:
                break

        name_e = entries[ni]
        vrows = [entries[k]['row'] for k in range(ni - r, ni + r + 1)
                 if entries[k].get('row')]
        if vrows:
            levels = sorted({v for (hv, lv, c, cap) in vrows for v in (hv, lv)},
                            reverse=True)
            rows.append({
                'src_no': name_e['no'],
                'name': name_e['name'],
                'voltage': '/'.join(str(x) for x in levels),
                'trafo_count': sum(c for (hv, lv, c, cap) in vrows),
                'capacity_mva': round(sum(cap for (hv, lv, c, cap) in vrows), 2),
            })
        else:
            # GI tanpa baris data tegangan — tetap dicatat utk transparansi
            rows.append({'src_no': name_e['no'], 'name': name_e['name'],
                         'voltage': '', 'trafo_count': 0, 'capacity_mva': None})

    leftover = sum(1 for i in range(n)
                   if entries[i]['type'] == 'volt' and not claimed[i])
    if leftover:
        print(f"  WARNING {table_id}: {leftover} baris tegangan tak ter-grup "
              f"(tabel mungkin malformed)")

    rows.sort(key=lambda x: x['src_no'])
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
    """Load override CSV (shared). Match by (ruptl_name, province)."""
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
    print(f"Manual overrides loaded: {len(overrides)}")

    region_provinces = {p[1] for p in PROVINCES}
    overrides_relevant = {k: v for k, v in overrides.items() if k[1] in region_provinces}
    print(f"  Override entries untuk Maluku/Papua: {len(overrides_relevant)}")

    rows_by_region = {r: [] for r in REGIONS}
    next_id = {r: 1 for r in REGIONS}
    summary = []
    used_overrides = set()

    for pid, prov_name, region, system, start, end, bbox in PROVINCES:
        rupt_rows = extract_table(RUPTL, pid, start, end)
        osm_prov = filter_by_bbox(osm_all, bbox)

        matched_fuzzy = 0
        matched_override = 0
        for r in rupt_rows:
            row = {
                'id': f'{ID_PREFIX[region]}-{next_id[region]:04d}',
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
            rows_by_region[region].append(row)
            next_id[region] += 1

        summary.append({
            'pid': pid, 'province': prov_name, 'region': region,
            'rupt_count': len(rupt_rows),
            'osm_in_bbox': len(osm_prov),
            'matched_fuzzy': matched_fuzzy,
            'matched_override': matched_override,
            'unmatched': len(rupt_rows) - matched_fuzzy - matched_override,
        })

    stale = set(overrides_relevant.keys()) - used_overrides
    if stale:
        print("\nWARNING: override entries Maluku/Papua tidak terpakai:")
        for k in sorted(stale):
            print(f"  - {k}")

    # Write per-region CSV + GeoJSON
    for region in REGIONS:
        out_rows = rows_by_region[region]
        if not out_rows:
            print(f"\nERROR: out_rows kosong untuk region {region}.")
            continue
        with open(OUT_CSV[region], 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            for r in out_rows:
                w.writerow(r)
        features = []
        for r in out_rows:
            if r['lat'] == '' or r['lon'] == '':
                continue
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
                'properties': {k: v for k, v in r.items() if k not in ('lat', 'lon')}
            })
        with open(OUT_GJ[region], 'w') as f:
            json.dump({'type': 'FeatureCollection', 'features': features}, f, ensure_ascii=False)
        print(f"\nWritten: {OUT_CSV[region]} ({len(out_rows)} rows)")
        print(f"Written: {OUT_GJ[region]} ({len(features)} features)")

    # Summary per provinsi
    print(f"\n{'PID':<5}{'Province':<16}{'Region':<9}{'RUPTL':>7}{'OSM_bbox':>10}"
          f"{'Fuzzy':>7}{'Override':>10}{'Unmatch':>9}")
    total = {'rupt_count': 0, 'matched_fuzzy': 0, 'matched_override': 0, 'unmatched': 0}
    for s in summary:
        print(f"{s['pid']:<5}{s['province']:<16}{s['region']:<9}"
              f"{s['rupt_count']:>7}{s['osm_in_bbox']:>10}"
              f"{s['matched_fuzzy']:>7}{s['matched_override']:>10}{s['unmatched']:>9}")
        for k in total:
            total[k] += s[k]
    matched_total = total['matched_fuzzy'] + total['matched_override']
    rate = matched_total / total['rupt_count'] * 100 if total['rupt_count'] else 0
    print(f"{'':<5}{'TOTAL':<16}{'':<9}{total['rupt_count']:>7}{'':>10}"
          f"{total['matched_fuzzy']:>7}{total['matched_override']:>10}{total['unmatched']:>9}")
    print(f"\nMatch rate keseluruhan: {matched_total}/{total['rupt_count']} = {rate:.1f}%")

    # Breakdown per region
    print("\nBreakdown per region:")
    for region in REGIONS:
        rs = [s for s in summary if s['region'] == region]
        rupt = sum(s['rupt_count'] for s in rs)
        matched = sum(s['matched_fuzzy'] + s['matched_override'] for s in rs)
        unm = sum(s['unmatched'] for s in rs)
        r = matched / rupt * 100 if rupt else 0
        print(f"  {region:<8} matched={matched:>3} / rupt={rupt:>3} ({r:.1f}%)  unmatched={unm}")


if __name__ == '__main__':
    run()
