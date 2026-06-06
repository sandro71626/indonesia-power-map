# SULAWESI v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset Sulawesi (generator only)
**Sebelum:** 101 generator
**Sesudah:** 87 generator (−14 net: −15 removed + 1 split-new)

## Catatan re-run protocol

Sama pola JAMALI/Sumatra/Kalimantan v1.0. Renames di-persist via
`generator_name_overrides.csv` (75 → 104 entries; +29 Sulawesi v1.0).
Penghapusan, type/capacity/status updates, split asset, dan manual add
PLTMG Kendari belum punya mekanisme override otomatis. Re-run
`extract_sulawesi_generators.py` akan menghapus revisi non-name.

---

## 1. Removed assets (15 entries)

Non-pembangkit, duplikat, atau aset salah-klasifikasi.

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-SLW-0026 | Listrik | Generic / non-spesifik |
| GEN-SLW-0019 | (unnamed) | way/942620063 — tidak teridentifikasi |
| GEN-SLW-0027 | (unnamed) PLTA | way/943309157 — tidak verifikasi |
| GEN-SLW-0054 | (unnamed) | way/1118436419 — tidak teridentifikasi |
| GEN-SLW-0015 | (unnamed) | way/892013127 — tidak teridentifikasi |
| GEN-SLW-0014 | PLTU Majene | Mis-tagged / tidak operasional |
| GEN-SLW-0002 | Pembangkit Listrik Tenaga Air Bakaru | Duplikat dgn GEN-SLW-0010 (rename → PLTA Bakaru) |
| GEN-SLW-0022 | KAWASAN | Generic / non-pembangkit |
| GEN-SLW-0008 | PLN Parepare | Kantor PLN cabang |
| GEN-SLW-0100 | (unnamed) | Tidak teridentifikasi |
| GEN-SLW-0101 | (unnamed) | Tidak teridentifikasi |
| GEN-SLW-0094 | (unnamed) PLTA | Tidak verifikasi |
| GEN-SLW-0017 | (unnamed) | way/892013129 |
| GEN-SLW-0016 | (unnamed) | way/892013128 |
| GEN-SLW-0030 | PLN Tomia | Kantor PLN ranting |

## 2. Renamed assets (29 entries)

Semua persist via `generator_name_overrides.csv`.

### PLTS utility & medium (7)

| ID | Nama baru | Capacity (MWp) |
|----|-----------|---:|
| GEN-SLW-0024 | PLTS Likupang | 21,0 |
| GEN-SLW-0023 | PLTS Bunaken | 0,335 |
| GEN-SLW-0096 | PLTS Makalehi | 0,260 |
| GEN-SLW-0097 | PLTS Pulau Kondingareng | 0,260 |
| GEN-SLW-0099 | PLTS Kayuadi | 1,01 |
| GEN-SLW-0086 | PLTS Terpusat Pasimarannu | 1,4 |
| GEN-SLW-0029 | PLTS Tomia | 0,800 |

### PLTS small (11)

| ID | Nama baru | Capacity (MWp) |
|----|-----------|---:|
| GEN-SLW-0056 | PLTS Terpusat Desa Perjuangan | 0,030 |
| GEN-SLW-0090 | PLTS Menara Indah | 0,040 |
| GEN-SLW-0035 | PLTS Tanete | 0,030 |
| GEN-SLW-0093 | PLTS Latondu | 0,075 |
| GEN-SLW-0091 | PLTS Pulau Panjang | 0,15389 |
| GEN-SLW-0092 | PLTS Pasitallu Tangnga | 0,050 |
| GEN-SLW-0089 | PLTS Sambali | 0,030 |
| GEN-SLW-0088 | PLTS Batu Bingkung | 0,040 |
| GEN-SLW-0087 | PLTS Bonea | 0,040 |
| GEN-SLW-0095 | PLTS Terpusat Batuatas Barat | 0,035 |
| GEN-SLW-0085 | PLTS Terpusat Kepulauan Sabalana (Sabalana I & II) | 0,060 per communal unit |

### Thermal — Coal (5 PLTU)

| ID | Nama baru | Type | Capacity (MW) |
|----|-----------|:---:|---:|
| GEN-SLW-0058 | PLTU IMIP Morowali (drop "(Sulawesi Mining)" suffix) | PLTU | 2.080 (2,08 GW) |
| GEN-SLW-0070 | PLTU Labota (drop "(IMIP Morowali)" suffix) | PLTU | 3.360 (3,36 GW) |
| GEN-SLW-0061 | PLTU Delong Nickel Phase II | PLTU | 1.840 |
| GEN-SLW-0083 | PLTU Wanxiang Nickel Indonesia | PLTU | 130 |
| GEN-SLW-0009 | PLTU PT Semen Tonasa Indonesia | PLTU | 120 |

### Thermal — Diesel (3 PLTD)

| ID | Nama baru | Capacity (MW) |
|----|-----------|---:|
| GEN-SLW-0067 | PLTD Telaga | 39,86 |
| GEN-SLW-0036 | PLTD Tallo Lama | 20 |
| GEN-SLW-0006 | PLTD Bau-Bau | 8 |

### Hydro (2)

| ID | Nama baru | Type | Capacity |
|----|-----------|:---:|---:|
| GEN-SLW-0010 | PLTA Bakaru | PLTA | 126 MW (preserve dari OSM) |
| GEN-SLW-0025 | PLTMH Bungin 1 | PLTMH | 0,09 MW |

### Split (1 row → 2)

| ID | Nama baru | Type | Capacity (MW) | Catatan |
|----|-----------|:---:|---:|---|
| GEN-SLW-0042 | PLTU Nii Tanasa | PLTU | 20 | Sebelumnya nama gabungan "PLTU Nii Tanasa (20 MW) & PLTMG Kendari (...)"; di-split |
| **GEN-SLW-0102** (baru) | PLTMG Kendari | PLTMG | 58 | Manual-add, koord = sama dgn primary (nearby) |

## 3. Split mixed asset (1)

GEN-SLW-0042 OSM-tagged sebagai satu polygon namun fisiknya dua fasilitas
terpisah di Kendari area (lat −3,895, lon 122,537):

| Result | Detail |
|--------|--------|
| **GEN-SLW-0042** (primary preserved) | PLTU Nii Tanasa, PLTU, 20 MW |
| **GEN-SLW-0102** (new entry) | PLTMG Kendari, PLTMG, 58 MW, `review_flag=MANUAL_ADD_v1.0`, koord nearby = same as primary |

Total capacity site-level: 78 MW.

## 4. Capacity updates summary

24 entries dengan capacity baru:

| Type | Count | Range capacity |
|------|------:|---|
| PLTU (coal) | 5 | 120 - 3.360 MW |
| PLTD | 3 | 8 - 39,86 MW |
| PLTMG (new) | 1 | 58 MW (split) |
| PLTMH | 1 | 0,09 MW |
| PLTS utility (≥0,2 MWp) | 7 | 0,260 - 21 MWp |
| PLTS small (<0,2 MWp) | 11 | 0,030 - 0,15389 MWp |

Total kapasitas baru yang ter-record (sum of caps yang diupdate):
~10.745 MW + ~26 MWp PLTS (utama Morowali smelter cluster dominasi:
2.080 + 3.360 + 1.840 + 130 = **7.410 MW** captive nickel/aluminium di
Sulawesi Tenggara/Tengah).

## 5. Capacity formatting rule

Kolom `capacity_unit` ditambahkan. Total **32 row PLTS** ber-`MWp` di
Sulawesi. Sisanya `MW`.

## 6. Files updated

- `data/processed/generator_master_sulawesi.csv` (87 rows, was 101; +1 kolom `capacity_unit`)
- `data/processed/generators_sulawesi.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (75 → 104 entries; +29 Sulawesi v1.0)
- `web/data_sulawesi.js` (re-bundled)

## 7. Unresolved items (perlu manual review)

Tidak ada unresolved dari user spec. Catatan asumsi:

- **GEN-SLW-0102** (PLTMG Kendari, split-new): koord asumsi sama dengan
  primary GEN-SLW-0042 (user spec "nearby coordinates"). Apabila tersedia
  koord eksplisit PLTMG Kendari, perlu update manual.

## Summary

- **Removed:** 15 entries (kantor PLN, duplikat Bakaru, unverified PLTS/PLTA, etc.)
- **Renamed:** 29 entries (18 PLTS standardisasi + 5 PLTU coal + 3 PLTD + 2 hydro + 1 split rename)
- **Split:** 1 → 2 (GEN-SLW-0042 → PLTU Nii Tanasa 20 MW + PLTMG Kendari 58 MW di GEN-SLW-0102 baru)
- **Capacity updates:** 24 entries (utamanya Morowali smelter cluster dengan total 7,4 GW captive)
- **Status changes:** none (semua tetap default `existing`)
- **Schema:** +1 kolom `capacity_unit` (32 PLTS ber-MWp)
- **Unresolved:** none (1 asumsi koord PLTMG Kendari)
