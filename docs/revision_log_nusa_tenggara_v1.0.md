# NUSA TENGGARA (NTB & NTT) v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset NTB & NTT (generator only)
**Sebelum:** 18 NTB + 41 NTT = 59 generator
**Sesudah:** 18 NTB + 39 NTT = 57 generator (−2 net)

---

## NTB

### 1. Renamed / updated assets (2 entries)

| ID | Nama baru | Type | Capacity (MW) |
|----|-----------|:---:|---:|
| GEN-NTB-0017 | PLTD Ampenan | PLTD | **55** |
| GEN-NTB-0001 | PLTD Dompu | PLTD | **1,8** |

GEN-NTB-0017 nama sudah `PLTD Ampenan` di current state (revisi sebelumnya:
typo "PTLD" → "PLTD" via name override). User confirm + tambah capacity 55 MW.

GEN-NTB-0001 sebelumnya `(unnamed)` dari OSM way/119783797 di Dompu area;
rename ke PLTD Dompu + cap 1,8 MW.

1 name override baru ditambahkan untuk GEN-NTB-0001 (Ampenan override
sudah ada dari revisi sebelumnya).

### NTB summary

- **Removed:** 0
- **Renamed/updated:** 2 entries (kedua-duanya PLTD)
- **Capacity updates:** 2 entries
- **Unresolved:** none

---

## NTT

### 1. Removed assets (3 entries)

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-NTT-0003 | PLN Cabang Magepanda | Kantor cabang PLN, bukan pembangkit |
| GEN-NTT-0005 | (unnamed) | way/527176121 — tidak teridentifikasi |
| GEN-NTT-0006 | PLTA-MH | Generic / duplikat fungsional dengan PLTMH Wae Garit (cluster Manggarai Timur) |

### 2. Reklasifikasi tipe (2 entries)

| ID | Tipe lama | Tipe baru | Nama baru |
|----|:---:|:---:|---|
| GEN-NTT-0011 | PLTA | **PLTMH** | PLTMH Sita (Manggarai Timur, cap 1 MW) |
| GEN-NTT-0016 | PLTG | **PLTP** | PLTP Ulumbu (Manggarai Flores, panas bumi, cap 10 MW yang sudah ter-record) |

Catatan: PLTP Ulumbu adalah PLTP geothermal Flores yang sebelumnya
ter-misclassified sebagai PLTG karena tag `plant:source=geothermal` pada
OSM tidak ter-mapping ke PLTP di derive_type extractor. Sekarang
diperbaiki manual.

### 3. PLTS corrections (5 entries)

| ID | Nama baru | Capacity (MWp) | Catatan |
|----|-----------|---:|---------|
| GEN-NTT-0039 | PLTS Koja Besar | 0,150 | Normalisasi capitalization "PLTS Koja besar" |
| GEN-NTT-0040 | PLTS Parumaan | 0,420 | Cap update |
| GEN-NTT-0041 | PLTS Desa Pulau Buaya | 0,250 | Normalisasi capitalization "DESA PULAU BUAYA" |
| GEN-NTT-0004 | PLTS Hambapraing | (preserve 1 MW) | OSM "Pembangkit Listrik Tenaga Surya" generic → rename |
| GEN-NTT-0038 | PLTS Kabuna | **0,00286 MWp** (2860 Wp = 2,86 kWp) | User konfirmasi capacity definitif 30 Mei 2026; sebelumnya ter-flag manual review |

### 4. PLTU correction (1 entry)

| ID | Nama | Type | Capacity (MW) |
|----|------|:---:|---:|
| GEN-NTT-0008 | PLTU Atapupu | PLTU | **24** |

PLTU Atapupu (Belu, perbatasan Timor Leste) sebelumnya tidak punya
capacity record di OSM; sekarang ter-record 24 MW.

### 5. Newly added assets (1 entry)

| ID | Nama | Type | Capacity (MW) | Koord | Status |
|----|------|:---:|---:|-------|--------|
| GEN-NTT-0042 | PLTMH Wae Nampe | PLTMH | 0,05 | −8,5638; 120,6347 | existing |

Manual-add (`review_flag=MANUAL_ADD_v1.0`, `source_id=manual_revision_v1.0`,
`osm_id=(kosong)`). Lokasi di koridor Manggarai Flores.

### NTT summary

- **Removed:** 3 entries (kantor PLN Magepanda + 2 unnamed/generic)
- **Renamed/reklasifikasi:** 7 entries (PLTMH Sita reclass, PLTP Ulumbu reclass, 5 PLTS standardisasi)
- **Capacity updates:** 6 entries
- **Newly added:** 1 entry (PLTMH Wae Nampe 0,05 MW)
- **Status changes:** none
- **Unresolved:** 0 entry (GEN-NTT-0038 PLTS Kabuna resolved via user konfirmasi 2860 Wp / 0,00286 MWp)

## Capacity formatting

Kolom `capacity_unit` ditambahkan di kedua master CSV.
- **NTB:** 8 PLTS ber-`MWp` (existing) + sisanya `MW`
- **NTT:** **26 PLTS ber-`MWp`** + sisanya `MW`

## Unresolved items (perlu manual review)

**Tidak ada unresolved item.** GEN-NTT-0038 (PLTS Kabuna) sebelumnya
ter-flag pending verifikasi kapasitas total komunal; user konfirmasi
30 Mei 2026 bahwa kapasitas terpasang sistem adalah **2860 Wp = 2,86 kWp
= 0,00286 MWp**. `review_flag` di-clear, capacity_mw di-set 0,00286 MWp.

## Files updated

- `data/processed/generator_master_ntb.csv` (18 rows, was 18; +1 kolom `capacity_unit`)
- `data/processed/generators_ntb.geojson` (re-built)
- `data/processed/generator_master_ntt.csv` (39 rows, was 41; +1 kolom `capacity_unit`)
- `data/processed/generators_ntt.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (111 → 120 entries; +1 NTB + +8 NTT v1.0)
- `web/data_ntb.js` (re-bundled)
- `web/data_ntt.js` (re-bundled)

## Summary gabungan NTB + NTT

- **Removed:** 3 entries (semua NTT)
- **Renamed:** 9 entries (2 NTB + 7 NTT)
- **Reklasifikasi:** 2 entries (NTT: PLTA→PLTMH Sita, PLTG→PLTP Ulumbu)
- **Newly added:** 1 entry (NTT: PLTMH Wae Nampe)
- **Capacity updates:** 8 entries (2 NTB + 6 NTT)
- **Status changes:** none
- **Schema:** +1 kolom `capacity_unit` di kedua master (8 NTB + 26 NTT PLTS ber-MWp)
- **Unresolved:** 0 entry (GEN-NTT-0038 PLTS Kabuna resolved via user konfirmasi 0,00286 MWp)
