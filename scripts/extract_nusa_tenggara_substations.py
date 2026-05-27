"""
Ekstrak daftar Gardu Induk Eksisting dari Lampiran C (Nusa Tenggara) RUPTL
2025-2034, match dengan koordinat OSM.

Step 6 mencakup 2 provinsi (Tabel C11-C12), ditulis ke DUA region terpisah
— mirip pola Maluku/Papua: NTB & NTT diperlakukan sebagai region berbeda
di peta.

  region 'ntb' : Nusa Tenggara Barat (C11)  -> system 'NTB'
  region 'ntt' : Nusa Tenggara Timur (C12)  -> system 'NTT'

Karakter NTB & NTT:
  - **NTB** punya interkoneksi parsial Lombok-Sumbawa (kabel laut 150 kV
    Selat Alas), tapi sistem Bima/Sumbawa Timur masih semi-isolated.
  - **NTT** kumpulan sistem pulau yang TIDAK interkoneksi (Sistem Flores,
    Sumba, Timor, Alor, Lembata, dst — sama pattern Maluku/Papua).

Untuk MVP, field `system` makro per provinsi ('NTB' / 'NTT'); detail
sub-sistem operasional bisa ditambah di iterasi berikutnya.

Satu extractor menulis dua set output:
  - data/processed/substation_master_ntb.csv + substations_ntb.geojson
  - data/processed/substation_master_ntt.csv + substations_ntt.geojson

Sumber:
  - data/raw/sources/RUPTL-2025-2034.pdf (Tabel C11-C12 per provinsi)
  - data/geojson/indonesia_substations.geojson (OSM)
  - data/overrides/substation_overrides.csv (shared; matched by ruptl_name + province)

Threshold matching identik dengan region sebelumnya: score >= 0.85 = matched
via fuzzy; di bawahnya UNMATCHED kecuali ada override. Override apply pertama.

Urutan provinsi C11=NTB, C12=NTT sudah DIVERIFIKASI lewat probe nama GI
(scripts/_probe_c_provinces.py):
  C11: Ampenan, Jeranjang, Sengkol, Mantang, Selong, Kuta — Lombok area.
  C12: Panaf, Tenau, Bolok, Maulafa, Naibonat, Nonohonis — Kupang/Timor.

Page range:
  C11.4 mulai p1153 (heading C11.5 di p1153 juga — tabel singkat, range
        ditetapkan 1153-1169 dengan parser auto-stop di C11.5).
  C12.4 mulai p1170 (heading C12.5 di p1171 — range 1170-1172 dengan
        parser auto-stop di C12.5).
"""
import re
import json
import csv
from difflib import SequenceMatcher
from pathlib import Path

from substation_table_parser import extract_table

ROOT = Path(__file__).resolve().parent.parent
RUPTL = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"
OSM_SUB = ROOT / "data/geojson/indonesia_substations.geojson"
OVERRIDES = ROOT / "data/overrides/substation_overrides.csv"

MATCH_THRESHOLD = 0.85

# Per-region: ID prefix + path output.
ID_PREFIX = {"ntb": "GI-NTB", "ntt": "GI-NTT"}
OUT_CSV = {
    "ntb": ROOT / "data/processed/substation_master_ntb.csv",
    "ntt": ROOT / "data/processed/substation_master_ntt.csv",
}
OUT_GJ = {
    "ntb": ROOT / "data/processed/substations_ntb.geojson",
    "ntt": ROOT / "data/processed/substations_ntt.geojson",
}

# Per-provinsi: tabel ID, nama provinsi, region, system, start/end page
# Lampiran C, bbox OSM (lat_min, lon_min, lat_max, lon_max).
#
# Bbox:
#   NTB lon_min 115.75 — sisi timur Selat Lombok. PLTU Celukan Bawang
#     (Bali, lon ~114.7) & semua plant Bali (lon < 115.7) ter-exclude.
#   NTT lon_min 119.10 — overlap minimal dgn Bima/NTB Timur (lon ~119.2);
#     mainland NTT (Flores barat / Labuan Bajo lon ~119.9) tetap masuk.
PROVINCES = [
    ("C11", "Nusa Tenggara Barat",  "ntb", "NTB", 1153, 1169, (-9.30, 115.75, -8.00, 119.30)),
    ("C12", "Nusa Tenggara Timur",  "ntt", "NTT", 1170, 1172, (-11.00, 119.10, -7.90, 125.30)),
]

REGIONS = ["ntb", "ntt"]


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
    print(f"  Override entries untuk NTB/NTT: {len(overrides_relevant)}")

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
        print("\nWARNING: override entries NTB/NTT tidak terpakai:")
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

    # Summary
    print(f"\n{'PID':<5}{'Province':<24}{'Region':<6}{'RUPTL':>7}{'OSM_bbox':>10}"
          f"{'Fuzzy':>7}{'Override':>10}{'Unmatch':>9}")
    total = {'rupt_count': 0, 'matched_fuzzy': 0, 'matched_override': 0, 'unmatched': 0}
    for s in summary:
        print(f"{s['pid']:<5}{s['province']:<24}{s['region']:<6}"
              f"{s['rupt_count']:>7}{s['osm_in_bbox']:>10}"
              f"{s['matched_fuzzy']:>7}{s['matched_override']:>10}{s['unmatched']:>9}")
        for k in total:
            total[k] += s[k]
    matched_total = total['matched_fuzzy'] + total['matched_override']
    rate = matched_total / total['rupt_count'] * 100 if total['rupt_count'] else 0
    print(f"{'':<5}{'TOTAL':<24}{'':<6}{total['rupt_count']:>7}{'':>10}"
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
        print(f"  {region:<5} matched={matched:>3} / rupt={rupt:>3} ({r:.1f}%)  unmatched={unm}")

    # Cetak UNMATCHED untuk review
    print("\n=== UNMATCHED untuk review override ===")
    for region in REGIONS:
        unmatched = [r for r in rows_by_region[region] if r['review_flag'] == 'UNMATCHED']
        if not unmatched:
            continue
        print(f"\n{region.upper()}:")
        for r in unmatched:
            print(f"  - {r['name']!r} ({r['province']}) — score={r['match_score']}")


if __name__ == '__main__':
    run()
