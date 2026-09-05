# Panduan Reconciliation: IPM Baseline ↔ RUPTL Rincian Pembangkit

Reconciliation adalah proses membandingkan dua sumber data pembangkit — baseline OSM (existing IPM) dan Rincian RUPTL PLN 2025–2034 — untuk menemukan match yang confident, probable, ambigu, dan yang belum ter-cover di salah satu sisi. Hasilnya adalah dataset gabungan (`generator_master_reconciled_{region}.csv`) dengan **provenance per field** dan **conflict flags** yang bisa direview.

Dokumen ini menjelaskan cara menjalankan pipeline, cara membaca hasilnya, dan cara memberikan manual override untuk kasus ambigu.

---

## Arsitektur

```
data/processed/generator_master_{region}.csv         (IPM baseline dari OSM)
                    +
data/processed/ruptl_generators_{region}.csv         (RUPTL Rincian row-level)
                    +
data/overrides/generator_matches.csv                 (manual decisions)
                    ↓
        scripts/reconcile_generators.py
                    ↓
data/processed/generator_master_reconciled_{region}.csv   (superset dataset)
data/reconciliation/report_{region}_{ts}.md               (audit report)
```

Reconciliation TIDAK menyentuh frontend, bundle_web_data, atau file lain. Ini murni pipeline batch di sisi `scripts/`.

---

## Menjalankan reconciliation

### Prerequisite

Pastikan sudah ada:

```
data/processed/generator_master_{region}.csv       ← sudah ada (baseline OSM)
data/processed/ruptl_generators_{region}.csv       ← harus di-extract dulu
data/overrides/generator_matches.csv               ← default: empty header only
```

RUPTL Rincian pembangkit di-extract oleh `scripts/extract_ruptl_generators.py` (lihat bagian bawah).

### Dry-run (default)

Selalu jalankan dry-run dulu untuk lihat berapa tier di tiap kategori:

```bash
python3 scripts/reconcile_generators.py --region jamali
```

Output di stdout:

```
[reconcile] region=jamali
  IPM baseline: data/processed/generator_master_jamali.csv
  RUPTL rows:   data/processed/ruptl_generators_jamali.csv
  Overrides:    data/overrides/generator_matches.csv
  → 196 IPM rows, 380 RUPTL rows, 0 overrides

== Tier summary ==
  CONFIRMED_MATCH             120
  PROBABLE_MATCH               45
  AMBIGUOUS                    18
  CONFLICT                      7
  UNMATCHED_IPM                31
  UNMATCHED_RUPTL             190
  TOTAL                       411

(dry-run — pass --write untuk simpan output)
```

Bandingkan dengan expectation lo:
- **CONFIRMED_MATCH** tinggi = baseline OSM cocok dengan RUPTL untuk pembangkit besar
- **UNMATCHED_RUPTL** = kandidat pembangkit yang bisa ditambah ke IPM (mungkin planned atau small-scale yang belum di-map di OSM)
- **UNMATCHED_IPM** = pembangkit OSM tanpa entry RUPTL — bisa jadi rooftop/captive di luar scope RUPTL, atau nama beda yang perlu manual override

### Tuning thresholds

Semua threshold configurable via CLI:

| Flag | Default | Fungsi |
|---|---|---|
| `--min-mw` | 1.0 | RUPTL rows < ini MW di-skip |
| `--radius` | 2.0 km | Radius untuk tier CONFIRMED |
| `--radius-name` | 15.0 km | Radius untuk same-name PROBABLE |
| `--radius-type` | 15.0 km | Radius untuk same-type AMBIGUOUS check |
| `--cap-tol` | 0.20 | Toleransi kapasitas untuk CONFIRMED |
| `--doubt-mw` | 100.0 MW | Threshold "large plant" untuk flag AMBIGUOUS |

Contoh: strict mode (lebih banyak yang jadi AMBIGUOUS, less CONFIRMED):

```bash
python3 scripts/reconcile_generators.py --region jamali \
    --radius 1.0 --cap-tol 0.10
```

### Menulis output

Setelah puas dengan tier summary, tambah `--write`:

```bash
python3 scripts/reconcile_generators.py --region jamali --write
```

Menulis:
- `data/processed/generator_master_reconciled_jamali.csv` (superset dataset)
- `data/reconciliation/report_jamali_{timestamp}.md` (audit report berbahasa Indonesian)

Report berisi daftar case yang perlu review (AMBIGUOUS + CONFLICT + UNMATCHED_RUPTL), sorted by MW descending.

---

## Membaca output CSV

Output `generator_master_reconciled_{region}.csv` punya **kolom kanonik** + **kolom `_source`** + **kolom original per sumber** + **kolom conflict flag**.

### Identity
| Kolom | Isi |
|---|---|
| `id` | ID unik (dari IPM kalau match, atau `RUPTL:xxx` kalau baru) |
| `ipm_id` | ID di baseline IPM (kosong kalau UNMATCHED_RUPTL) |
| `ruptl_id` | ID di RUPTL row (kosong kalau UNMATCHED_IPM) |

### Canonical fields (nilai final yang dipakai)
| Kolom | Companion source |
|---|---|
| `name` | `name_source` (ipm_osm / ruptl / override) |
| `capacity_mw` | `capacity_mw_source` |
| `type` | `type_source` |
| `role` | `role_source` |
| `operator` | `operator_source` |
| `status` | `status_source` |
| `lat, lon` | `coord_source` (ipm_osm / ruptl_geocoded / override / unassigned) |

### Match metadata
| Kolom | Isi |
|---|---|
| `match_tier` | CONFIRMED_MATCH / PROBABLE_MATCH / AMBIGUOUS / CONFLICT / UNMATCHED_IPM / UNMATCHED_RUPTL |
| `match_score` | 0.10–1.00 (untuk sorting) |
| `match_reason` | Human-readable string ("coord 1.2 km ≤ 2, type=PLTU matches, ...") |

### Audit (original values, never overwritten)
- `capacity_mw_ipm`, `capacity_mw_ruptl`
- `type_ipm`, `type_ruptl`
- `role_ipm`, `role_ruptl`

### Conflict flags
- `has_capacity_conflict` = true kalau diff > 30%
- `has_type_conflict` = true kalau IPM & RUPTL berbeda `type`
- `has_role_conflict` = true kalau berbeda `role`
- `has_location_conflict` = true kalau jarak > 5 km padahal match

Filter Excel/pandas berdasarkan salah satu conflict flag untuk temukan case yang perlu review meski tier CONFIRMED.

---

## Manual override

Ketika reconciliation dry-run menghasilkan case AMBIGUOUS atau CONFLICT, ada 4 keputusan yang bisa lo tulis di `data/overrides/generator_matches.csv`:

| `decision` | Efek |
|---|---|
| `merge` | Force-merge RUPTL row ke IPM id spesifik → tier jadi CONFIRMED_MATCH, reason "manual override: merge" |
| `keep_separate` | Force RUPTL row jadi UNMATCHED_RUPTL, jangan digabung ke IPM |
| `drop_ruptl` | Skip RUPTL row (mis. duplikat) |
| `drop_ipm` | (belum diimplementasi — untuk masa depan) |

### Format CSV

```csv
override_id,decision,ipm_id,ruptl_id,capacity_override,type_override,role_override,operator_override,reason,reviewed_by,reviewed_at
```

- `override_id` = ID internal untuk audit lo (bebas, mis. OVR-001, OVR-002, ...)
- `decision` = salah satu dari 4 di atas
- `ipm_id` = IPM row id (untuk decision `merge`)
- `ruptl_id` = RUPTL row id
- `*_override` = kalau lo mau force nilai kanonik yang berbeda dari IPM/RUPTL (kosong = ikut default rule)
- `reason` = catatan lo — kenapa keputusan ini diambil
- `reviewed_by, reviewed_at` = tracking

### Contoh

```csv
override_id,decision,ipm_id,ruptl_id,capacity_override,type_override,role_override,operator_override,reason,reviewed_by,reviewed_at
OVR-001,merge,GEN-JMB-0042,RUPTL-JMB-P-115,,,,,"OSM 'PLTU Cirebon Unit 1' dan RUPTL 'PLTU Cirebon 1' obviously same plant",sandro,2026-09-05
OVR-002,keep_separate,,RUPTL-SUM-P-089,,,,,"Semen Indonesia holding vs Semen Gresik Tuban — beda lokasi",sandro,2026-09-05
OVR-003,drop_ruptl,,RUPTL-JMB-P-201,,,,,"Duplikat baris dalam RUPTL — sudah tercatat sebagai RUPTL-JMB-P-198",sandro,2026-09-06
OVR-004,merge,GEN-JMB-0055,RUPTL-JMB-P-078,660,,,,"IPM lists 500 MW (2010 nameplate), RUPTL 660 MW (post-uprate) — pakai angka baru",sandro,2026-09-05
```

### Iterative workflow

1. Run `python3 scripts/reconcile_generators.py --region jamali` (dry-run)
2. Cek report → identifikasi case AMBIGUOUS/CONFLICT yang penting
3. Edit `data/overrides/generator_matches.csv` — tambah baris override
4. Re-run → tier akan berubah sesuai decision
5. Ulangi sampai puas
6. Run terakhir dengan `--write`

Override tetap tersimpan — reconciliation deterministik. Kalau data baseline OSM update dan RUPTL update, override tetap berlaku selama `ipm_id`/`ruptl_id`-nya masih ada.

---

## Interpretasi hasil per tier

### CONFIRMED_MATCH
Coord ≤ 2 km, type match, capacity within tolerance. **Tinggi confidence, aman dipakai as-is.** IPM values dominan (baseline is master), RUPTL values disimpan sebagai `_ruptl` companion untuk audit.

### PROBABLE_MATCH
Nama-stem match dalam 15 km, atau token set identik. **Aman untuk sebagian besar analisis**, tapi patut spot-check bila ada `has_*_conflict` flag.

### AMBIGUOUS
Multiple candidates (untuk 1 RUPTL row) atau large plant (> 100 MW) tanpa clear match. **WAJIB review manual** — tulis override untuk decide.

### CONFLICT
Match ada tapi salah satu attribute berbeda drastis (mis. capacity > 30% off, atau type PLTU vs PLTGU). **WAJIB review** — mungkin data salah salah satu sisi, atau memang plant sudah di-uprate/di-repurpose.

### UNMATCHED_IPM
IPM row tanpa RUPTL counterpart. Bisa jadi:
- Pembangkit captive/community di luar scope RUPTL — normal
- Pembangkit rooftop PV / kecil — normal
- Pembangkit yang seharusnya ada di RUPTL tapi nama berbeda — bikin override

### UNMATCHED_RUPTL
RUPTL row tanpa IPM counterpart. Kandidat plant untuk ditambah ke IPM dataset. Bisa jadi:
- Planned plant (belum operating) — cek `status` column
- Existing plant yang belum di-map di OSM — kandidat add + geocoding manual
- False alarm karena nama beda — bikin override `merge`

---

## RUPTL row extractor

`scripts/extract_ruptl_generators.py` extract Rincian pembangkit table dari PDF RUPTL 2025–2034 per region. Output ke `data/processed/ruptl_generators_{region}.csv`.

Format output (columns):
```
id, name, type, capacity_mw, province, region_key, status,
target_cod_year, cod_re_base, cod_ared, developer, source_table, source_page
```

Cara pakai:
```bash
python3 scripts/extract_ruptl_generators.py --region jamali \
    --pdf data/raw/sources/RUPTL-2025-2034.pdf
```

Detail parsing PDF ada di file itu sendiri. Kalau parsing gagal untuk region tertentu (RUPTL table format tidak seragam antarprovinsi), fallback: bikin `ruptl_generators_{region}.csv` manual dari copy-paste PDF, lalu run reconciler.

---

## Log iterasi

Catat tiap run yang signifikan di `docs/reconciliation_log_generators.md` — tanggal, thresholds, tier counts, jumlah override baru, decision penting. Mirror pola `docs/extraction_log_substations_jamali.md`.
