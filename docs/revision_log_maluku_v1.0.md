# MALUKU v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset Maluku (generator only)
**Sebelum:** 19 generator
**Sesudah:** 13 generator (-6)

## 1. Removed assets (6 entries)

Konsolidasi Weda Bay (5 sub-unit dipisah, primary GEN-MLK-0013 dipertahankan) dan kantor PLN.

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-MLK-0003 | PLN Desa Waci | Kantor PLN Halmahera |
| GEN-MLK-0012 | PLN Tehoru | Kantor PLN Seram |
| GEN-MLK-0016 | PLTU Weda Bay Unit 9-11 | Sub-unit, konsolidasi ke primary GEN-MLK-0013 |
| GEN-MLK-0017 | PLTU Weda Bay Unit 1-4 | Sub-unit, konsolidasi ke primary |
| GEN-MLK-0018 | PLTU Weda Bay Unit 5-8 | Sub-unit, konsolidasi ke primary |
| GEN-MLK-0019 | Gardu Induk Weda Bay Unit 3 | Substation mis-tagged sebagai plant, drop |

## 2. Renamed assets (4 entries) + capacity updates

| ID | Nama baru | Type | Capacity | Unit |
|----|-----------|------|---:|---|
| GEN-MLK-0010 | PLTMG Dullah | PLTMG | 20 | MW |
| GEN-MLK-0013 | PLTU Weda Bay | PLTU | **4.000 (4 GW)** | MW ⚠️ flagged |
| GEN-MLK-0014 | PLTS Daruba | PLTS | 0,600 | MWp |
| GEN-MLK-0015 | PLTS Terpusat Desa Posi-Posi | PLTS | 0,0005 (0,5 kWp) | MWp |

## 3. Capacity updates

| ID | Capacity | Catatan |
|----|---:|---------|
| GEN-MLK-0010 | 20 MW | PLTMG Dullah (Kei Kecil) |
| GEN-MLK-0013 | 4.000 MW (4 GW) | ⚠️ **review_flag: CAPACITY_FLAG_4GW_verify_multiunit** — kemungkinan multi-unit complex total bukan single asset |
| GEN-MLK-0014 | 0,600 MWp | PLTS Daruba (Morotai utara) |
| GEN-MLK-0015 | 0,0005 MWp | PLTS Terpusat Desa Posi-Posi (Morotai), konversi dari 0,5 kWp |

## 4. Capacity formatting

Kolom `capacity_unit` ditambahkan. Total **5 row PLTS** ber-`MWp`, sisanya `MW`.

## 5. Unresolved items (perlu manual review)

| Item | Issue | Saran |
|------|-------|-------|
| **GEN-MLK-0013 (PLTU Weda Bay 4 GW)** | Capacity 4.000 MW (4 GW) unusual besar untuk single plant entry; kemungkinan agregat multi-unit Weda Bay Industrial Park (sub-unit Weda Bay 1-4, 5-8, 9-11 sudah konsolidasi ke entry ini). | Verifikasi: apakah 4 GW = sum dari sub-unit fisik yang dikonsolidasikan, atau angka ini perlu pengecekan ulang dari press release IWIP/Tsingshan? `review_flag` di-set `CAPACITY_FLAG_4GW_verify_multiunit` untuk audit trail. Tidak dimodifikasi sampai verifikasi. |

## Files updated

- `data/processed/generator_master_maluku.csv` (13 rows, was 19; +1 kolom `capacity_unit`)
- `data/processed/generators_maluku.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (104 → 107 entries; +3 Maluku v1.0)
- `web/data_maluku.js` (re-bundled)

## Summary

- **Removed:** 6 entries (4 sub-unit Weda Bay konsolidasi + 1 GI mis-tagged + 2 kantor PLN)
- **Renamed:** 4 entries (PLTMG Dullah, PLTU Weda Bay, PLTS Daruba, PLTS Terpusat Desa Posi-Posi)
- **Capacity updates:** 4 entries (semua row yang di-rename)
- **Status changes:** none
- **Schema:** +1 kolom `capacity_unit` (5 PLTS ber-MWp)
- **Unresolved:** 1 entry (GEN-MLK-0013 PLTU Weda Bay 4 GW) flagged untuk verifikasi multi-unit complex
