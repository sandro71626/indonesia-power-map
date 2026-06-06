# SUMATRA v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset Sumatra (generator only)
**Sebelum:** 133 generator
**Sesudah:** 120 generator (-13)

## Catatan re-run protocol

Sama dengan JAMALI v1.0: revisi ini diterapkan via skrip one-shot ke master
CSV dan GeoJSON, plus append name renames ke
`data/overrides/generator_name_overrides.csv` (38 → 55 entries; +8 Sumatra
v1.0). Penghapusan, koreksi tipe/kapasitas/operator/status, dan merge
multi-unit belum punya mekanisme override otomatis. Jika
`extract_sumatra_generators.py` di-run ulang, revisi tersebut perlu
diterapkan kembali.

---

## 1. Removed assets (11 entries)

Non-pembangkit (kantor PLN, fasilitas non-generator) dan PLTS / GI yang
salah-klasifikasi.

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-SMT-0009 | KANTOR | Kantor PLN Aceh |
| GEN-SMT-0027 | Bendungan Pembangkit Listrik Mikro | Bendungan generic, bukan PLT spesifik |
| GEN-SMT-0034 | Booster PAM | Booster pump PDAM Sumsel |
| GEN-SMT-0044 | PLN | Aset PLN non-pembangkit Riau |
| GEN-SMT-0056 | (unnamed) PLTS Aceh | Plant kecil tidak terverifikasi |
| GEN-SMT-0057 | (unnamed) PLTS Aceh | Plant kecil tidak terverifikasi |
| GEN-SMT-0081 | PLTG Arun Aceh LNG | Tidak operasional / over-tagged |
| GEN-SMT-0106 | (unnamed) Lampung | Tidak teridentifikasi |
| GEN-SMT-0125 | (unnamed) PLTS Riau | Plant kecil tidak terverifikasi |
| GEN-SMT-0128 | (unnamed) Aceh | Tidak teridentifikasi |
| GEN-SMT-0133 | PLN ranting Pagar Alam | Kantor cabang PLN |

## 2. Renamed assets (9 entries)

Semua append ke `generator_name_overrides.csv` untuk persistence.

| ID | Nama lama | Nama baru |
|----|-----------|-----------|
| GEN-SMT-0017 | PLTD Lueng Bata Banda Aceh | PLTD Lueng |
| GEN-SMT-0129 | (unnamed) | PLTD Rema |
| GEN-SMT-0099 | MV Karadeniz Powership Onur Sultan | PLTG Kapal MV Karadeniz Powership Onur Sultan |
| GEN-SMT-0101 | Pembangkit Riau MRPR | PLTGU Tenayan MRPR |
| GEN-SMT-0040 | Pusat Listrik Sei Gelam | PLTMG Sei Gelam |
| GEN-SMT-0077 | PLTG Borang | PLTG Borang (capacity update only) |
| GEN-SMT-0082 | PLTU Sinar Mas Lontar Jambi | PLTU Sinar Mas Lontar Jambi (operator + cap update) |
| GEN-SMT-0100 | PLTU Semaran | PLTU Semaran (operator + cap update) |
| GEN-SMT-0001 | PLTU Indah Kiat Perawang | PLTU Indah Kiat (multi-unit) Perawang (merge label) |

## 3. Merged assets (3 → 1)

Konsolidasi unit-unit Perawang Indah Kiat / APP yang sebelumnya muncul
sebagai 3 row terpisah karena OSM tagging multi-relation.

| Asset yang di-drop | Konsolidasi ke |
|---|---|
| GEN-SMT-0058 (way/914010995, Unit 2) | GEN-SMT-0001 |
| GEN-SMT-0059 (way/914011000, Unit 3) | GEN-SMT-0001 |
| **Entry tersisa** | **GEN-SMT-0001** dengan nama `PLTU Indah Kiat (multi-unit) Perawang`, type PLTU, kapasitas 755 MW total, status existing |

Catatan: entry override untuk way/914010995 dan way/914011000 di
`generator_name_overrides.csv` masih ada (Unit 2, Unit 3) sebagai
historical record. Mereka tidak akan ter-aplikasikan ke output karena row
sudah dihapus dari master CSV.

## 4. Type / capacity / operator corrections (12 entries)

### Type (4 entries)

| ID | Lama | Baru |
|----|------|------|
| GEN-SMT-0017 | Unknown | PLTD |
| GEN-SMT-0111 | PLTD (sudah benar; capacity baru) | PLTD |
| GEN-SMT-0099 | PLTG | PLTG (capacity baru) |
| GEN-SMT-0101 | Unknown | PLTGU |
| GEN-SMT-0040 | PLTG | PLTMG |
| GEN-SMT-0082 | Unknown | PLTU |
| GEN-SMT-0110 | Unknown | **PLTBg** (kategori baru) |
| GEN-SMT-0107 | PLT Biomas | **PLT Biomass** (standardisasi ke spelling Inggris) |

### Capacity (8 entries)

| ID | Capacity (MW) | Asset |
|----|---:|---|
| GEN-SMT-0017 | 58.5 | PLTD Lueng |
| GEN-SMT-0129 | 3.0 | PLTD Rema |
| GEN-SMT-0111 | 120.0 | PLTD PT Berkat Bima Sentana |
| GEN-SMT-0099 | 240.0 | PLTG Kapal MV Karadeniz Powership Onur Sultan |
| GEN-SMT-0101 | 296.2 | PLTGU Tenayan MRPR |
| GEN-SMT-0040 | 12.0 | PLTMG Sei Gelam |
| GEN-SMT-0077 | 100.0 | PLTG Borang |
| GEN-SMT-0082 | 211.0 | PLTU Sinar Mas Lontar Jambi |
| GEN-SMT-0100 | 14.0 | PLTU Semaran |
| GEN-SMT-0001 (merged) | 755.0 | PLTU Indah Kiat (multi-unit) Perawang |

### Operator (3 entries)

| ID | Operator |
|----|----------|
| GEN-SMT-0040 | PT PLN (Persero) |
| GEN-SMT-0082 | PT Lontar Papyrus Pulp & Paper Mill |
| GEN-SMT-0100 | PT Permata Prima Elektrindo |

## 5. Status correction (1 entry)

| ID | Lama | Baru | Catatan |
|----|------|------|---------|
| GEN-SMT-0075 (PLTU Koto Ringin) | existing | **stalled** | Effectively non-operational / mangkrak / belum operasi |

## 6. New generator category

**PLTBg (Biogas)** — kategori baru ditambahkan ke dataset (sebelumnya
hanya ada PLT Biomas/Biomass). Saat ini hanya 1 entry:

- GEN-SMT-0110 (PLTBg Sei Mangkei, Sumut, way/1224794317, capacity 2.4 MW,
  source OSM `plant:source=biogas`)

Di iterasi berikutnya, `extract_*_generators.py` `SOURCE_MAP` dapat
di-update untuk auto-map `biogas → PLTBg` supaya konsisten. Saat ini
kategori di-set manual via revisi.

## 7. Capacity formatting rule

Tambah kolom `capacity_unit` di `generator_master_sumatra.csv`. Default
`MW`, untuk semua row dengan `type=PLTS` di-set `MWp`. Total **7 row
PLTS** ter-update ke `MWp`.

## 8. Unresolved items (perlu manual review)

Tidak ada unresolved item dari user spec untuk Sumatra v1.0. Semua
instruksi sudah ter-aplikasikan.

## Files updated

- `data/processed/generator_master_sumatra.csv` (120 rows, was 133; +1 kolom `capacity_unit`)
- `data/processed/generators_sumatra.geojson` (re-built dari CSV baru)
- `data/overrides/generator_name_overrides.csv` (47 → 55 entries; +8 Sumatra v1.0)
- `web/data_sumatra.js` (re-bundled)

## Summary

- **Removed:** 11 entries (kantor PLN, booster pump, PLTS unverified, GI mis-tagged, dll)
- **Renamed:** 9 entries (standardisasi PLTD/PLTG/PLTGU/PLTMG/PLTU naming + merge label)
- **Merged:** 3 → 1 entry (PLTU Indah Kiat Perawang multi-unit, 755 MW total)
- **Type/cap/operator:** 12 entries (3 type changes, 10 capacity additions, 3 operator additions)
- **Status:** 1 entry (PLTU Koto Ringin → stalled)
- **New category:** PLTBg (Biogas) — 1 row PLTBg Sei Mangkei
- **Schema:** +1 kolom `capacity_unit` (7 PLTS ber-MWp)
- **Unresolved:** none
