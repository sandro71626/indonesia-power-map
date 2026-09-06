# Reconciliation Override Files

Persistent manual override layer untuk reconciliation pipeline (generator/substation/transmission). Setiap kali pipeline dijalankan, override CSV di-baca dan diterapkan ke hasil auto-matching. **Manual > automatic** — analyst curation adalah source of truth.

## File

| File | Object type | Read by |
|---|---|---|
| `generator_reconciliation_overrides.csv` | Generator (pembangkit) | `scripts/reconcile_generators.py` |
| `substation_reconciliation_overrides.csv` | Substation (gardu induk) | `scripts/detect_substation_delta.py` |
| `transmission_reconciliation_overrides.csv` | Transmission (saluran) | `scripts/reconcile_transmission.py` |

**Catatan:** file `generator_matches.csv` (legacy) dan `substation_overrides.csv` (coord/name curation) memiliki **skema berbeda dan tujuan berbeda** — jangan digabung dengan file di atas.

## Skema kolom (sama untuk 3 file)

| Kolom | Wajib untuk | Deskripsi |
|---|---|---|
| `override_id` | selalu | ID unik audit trail (mis. `OVR-JMB-001`) |
| `region` | selalu | `jamali` / `sumatra` / `kalimantan` / `sulawesi` / `maluku` / `papua` / `ntb` / `ntt` |
| `baseline_id` | context-dependent | IPM ID (`GEN-JMB-0001` / `GI-JMB-0001` / OSM `way/xxx` untuk trm) |
| `ruptl_id` | context-dependent | RUPTL row ID (`RUPTL-JAMALI-P-0001` / `-GI-` / `-T-`) |
| `decision` | selalu | salah satu dari 6 canonical enum (lihat di bawah) |
| `field` | field-level saja | nama kolom target (mis. `capacity_mw`) |
| `override_value` | field-level saja | nilai eksplisit |
| `reason` | selalu | Justifikasi free-text |
| `reviewed_by` | selalu | Nama analyst |
| `review_date` | selalu | ISO date `YYYY-MM-DD` |

## Canonical decision enum

| Decision | Wajib kolom | Efek |
|---|---|---|
| `CONFIRM_MATCH` | `baseline_id` + `ruptl_id` | Endorse auto-detected match. Tier jadi CONFIRMED, reason: "manual CONFIRM_MATCH". |
| `FORCE_MATCH` | `baseline_id` + `ruptl_id` | Force pair yang algorithm miss (mis. algorithm returned UNMATCHED, tapi analyst yakin baseline `GEN-JMB-0055` ↔ RUPTL `RUPTL-JAMALI-P-0089`). Tier jadi CONFIRMED. |
| `REJECT_MATCH` | `baseline_id` + `ruptl_id` | Reject auto match. Baseline balik ke UNMATCHED, ruptl balik ke UNMATCHED_RUPTL. |
| `KEEP_BASELINE` | `baseline_id` (+ optional `field`) | Untuk kasus CONFLICT: keep baseline value, ignore RUPTL suggestion. Kalau ada `field`, hanya field itu yang dipertahankan. |
| `USE_RUPTL_VALUE` | `ruptl_id` + `field` + `override_value` | Field-level: apply nilai spesifik ke canonical field (mis. capacity IPM 500 MW tapi RUPTL 660 MW post-uprate → USE_RUPTL_VALUE dengan `field=capacity_mw`, `override_value=660`). |
| `IGNORE_RUPTL_ROW` | `ruptl_id` | Skip RUPTL row entirely (garbage/duplicate extraction). Row tidak akan muncul di hasil reconciliation. |

## Contoh isi

```csv
override_id,region,baseline_id,ruptl_id,decision,field,override_value,reason,reviewed_by,review_date
OVR-JMB-001,jamali,GEN-JMB-0055,RUPTL-JAMALI-P-0089,FORCE_MATCH,,,PLTU Cirebon Unit 1 vs OSM 'Cirebon-1',sandro,2026-09-06
OVR-JMB-002,jamali,,RUPTL-JAMALI-P-0198,IGNORE_RUPTL_ROW,,,Duplikat RUPTL-JAMALI-P-0201 (extractor artifact),sandro,2026-09-06
OVR-JMB-003,jamali,GEN-JMB-0042,RUPTL-JAMALI-P-0115,REJECT_MATCH,,,Nama mirip tapi lokasi terpaut 40 km (Semen Indonesia vs Semen Gresik),sandro,2026-09-06
OVR-JMB-004,jamali,GEN-JMB-0055,RUPTL-JAMALI-P-0089,USE_RUPTL_VALUE,capacity_mw,660,IPM 500 MW nameplate 2010; RUPTL 660 MW post-uprate 2018,sandro,2026-09-06
```

## Precedence order

Setiap RUPTL row diproses:

1. **Row-level check** — Ada override dengan `ruptl_id` matching?
   - `IGNORE_RUPTL_ROW` → skip row, done.
   - `FORCE_MATCH` (tanpa baseline_id auto match) → attempt force pair, tag CONFIRMED.
2. **Auto matching** — Algorithm normal (cascade generators / delta detector sub / endpoint pair trm).
3. **Pair-level check** — Ada override dengan matching `(baseline_id, ruptl_id)`?
   - `CONFIRM_MATCH` → keep auto match, tag CONFIRMED, tambah provenance.
   - `REJECT_MATCH` → split, baseline+ruptl kembali unmatched.
   - `FORCE_MATCH` → same effect as CONFIRM (endorse).
4. **Field-level check** — Ada override dengan `field`+`override_value`? Apply nilai eksplisit.
5. **Provenance** — Kalau override applied, tag output row dengan `override_id`, `override_by`, `override_date`, `override_reason`, `override_decision`.

## Workflow: review → rerun

```bash
# 1. Jalankan reconciliation pertama
python3 scripts/reconcile_generators.py --region jamali --write
python3 scripts/detect_substation_delta.py --region jamali --write
python3 scripts/reconcile_transmission.py --region jamali --write

# 2. Buka report untuk lihat cases yang perlu review
open data/reconciliation/report_jamali_*.md
# Lihat "Cases needing manual review" section untuk AMBIGUOUS / CONFLICT / UNMATCHED_RUPTL

# 3. Analyst edit override CSV
open data/overrides/generator_reconciliation_overrides.csv
# Add decisions per case

# 4. Cross-check override state (validation + stale check)
python3 scripts/audit_reconciliation_overrides.py --region jamali

# 5. Rerun pipeline — override otomatis di-load + applied
python3 scripts/run_region_pipeline.py --region jamali

# 6. Report baru punya section "Override audit" di bagian akhir yang
#    tampilkan: jumlah applied, invalid, unused, stale.
```

Override CSV **reusable** — sekali ditulis, akan terus di-apply di semua reconciliation berikutnya, sampai analyst delete atau modify. Kalau baseline/ruptl ID berubah (karena re-extraction), override otomatis di-tag STALE (via `audit_reconciliation_overrides.py` atau di dalam per-region report).

## Provenance columns di output

Reconciled CSV / delta CSV akan punya kolom tambahan kalau override applied:

- `override_applied` (`true` / kosong)
- `override_id` (link ke override row)
- `override_decision` (enum yang di-apply)
- `override_by` (analyst name)
- `override_date` (review date)
- `override_reason` (justifikasi analyst)

Downstream (bundle_web_data / frontend popup) bisa consume field ini untuk visual indicator "manually curated" kalau nanti diperlukan.

## Validation warnings

`load_overrides()` akan menolak baris dengan:
- `override_id` kosong
- `decision` unknown / kosong
- `region` kosong
- Kolom wajib per-decision hilang (mis. `USE_RUPTL_VALUE` tanpa `field`/`override_value`)

Warning muncul di console reconciler + di audit report. Baris invalid **tidak silently ignored** — user akan tau harus fix.
