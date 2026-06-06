# JAMALI v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset JAMALI (generator + substation + transmission)
**Sebelum:** 196 generator, 520 GI, 2.358 transmisi
**Sesudah:** 174 generator (-22), 522 GI (+2), 2.357 transmisi (-1; pindah ke Sumatra)

## Catatan re-run protocol

Revisi ini diterapkan manual ke master CSV dan GeoJSON via skrip one-shot
(`_apply_jamali_v1_revisions.py`, sudah dihapus). Sebagian besar perubahan
nama persistent melalui `data/overrides/generator_name_overrides.csv`
(append 9 entries baru). Penghapusan, koreksi tipe/kapasitas/provinsi,
reklasifikasi ke GI, serta pemindahan transmisi belum punya mekanisme
override otomatis. Jika `extract_jamali_generators.py` dan
`extract_jamali_substations.py` di-run ulang, revisi tersebut perlu
diterapkan kembali.

---

## 1. Removed assets (22 entries)

### Non-generator (14 entries)

Kantor PLN, fasilitas non-pembangkit, dan asset salah-klasifikasi.

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-JMB-0003 | PLN Area Pasuruan | Kantor wilayah PLN |
| GEN-JMB-0005 | (unnamed) | relation/17194068 |
| GEN-JMB-0006 | (unnamed) | relation/17285692 |
| GEN-JMB-0007 | PT. Cassava Buana Wira Jatim | Pabrik singkong, bukan pembangkit |
| GEN-JMB-0008 | (unnamed) | relation/17367092 |
| GEN-JMB-0046 | PT PLN | Aset PLN non-pembangkit |
| GEN-JMB-0049 | PT PLN Penyaluran dan Pusat Pengatur Beban Jawa - | Kantor P3B |
| GEN-JMB-0051 | PLN Cabangbungin | Kantor cabang |
| GEN-JMB-0053 | The National Electricity Company Property | Aset PLN non-pembangkit |
| GEN-JMB-0054 | GARDU PLN | Gardu distribusi (bukan GI) |
| GEN-JMB-0060 | Genset | Genset kecil non-utility |
| GEN-JMB-0078 | Kantor TPSA Desa Babakan | Kantor desa |
| GEN-JMB-0084 | pln corporate university | Pusat pendidikan |
| GEN-JMB-0108 | Incinerator | Insinerator RS, bukan PLTSa utility |

### Transmission tower (6 entries)

Cluster `way/...` di Tuban (lat -6.88, lon 112.03) yang ter-tag `power=plant`
di OSM tapi sebenarnya transmission tower / komponen koridor.

| ID |
|----|
| GEN-JMB-0112 |
| GEN-JMB-0113 |
| GEN-JMB-0114 |
| GEN-JMB-0141 |
| GEN-JMB-0170 |
| GEN-JMB-0013 |

### Reclassified to GI (2 entries)

| Gen ID (dihapus) | Substation ID baru | Nama |
|---|---|---|
| GEN-JMB-0086 | GI-JMB-0521 | Gardu Induk Ujungberung |
| GEN-JMB-0111 | GI-JMB-0522 | Gardu Induk Tuban |

---

## 2. Renamed assets (11 entries)

Semua append ke `data/overrides/generator_name_overrides.csv` untuk
persistence saat extractor re-run.

| ID | Nama lama | Nama baru |
|----|-----------|-----------|
| GEN-JMB-0012 | Pembangkit Listrik Tenaga Air Lodoyo | PLTA Lodoyo |
| GEN-JMB-0014 | Pembangkit Listrik Tenaga Air Jatigede | PLTA Jatigede |
| GEN-JMB-0018 | Star Energy Geothermal Salak | PLTP Star Energy Salak |
| GEN-JMB-0038 | Star Energy Geothermal Darajat | PLTP Star Energy Darajat |
| GEN-JMB-0048 | PEMBANGKIT LISTRIK TENAGA ANGIN | PLTB (lokasi pending) |
| GEN-JMB-0077 | Pembangkit Listrik Tata Jabar | PLTG Tata |
| GEN-JMB-0116 | SPPBE PT. Bitcom Asri Energi | PLTG Bitcom Asri Energi |
| GEN-JMB-0124 | PLTU DSS Energi Serang | PLTU Indah Kiat Serang |
| GEN-JMB-0134 | (unnamed) | PLTS ITN Malang |
| GI-JMB-0273 | Ujungberung | Gardu Induk New Ujungberung-2 |
| GI-JMB-0404 | Tuban | Gardu Induk Tuban 3 |

## 3. Type / capacity / province corrections (16 entries)

### Type changes (6)

| ID | Lama | Baru |
|----|------|------|
| GEN-JMB-0048 | Unknown | PLTB |
| GEN-JMB-0056 | Unknown | PLTD |
| GEN-JMB-0106 | Unknown | PLTGU |
| GEN-JMB-0124 | Unknown | PLTU |
| GEN-JMB-0125 | Unknown | PLTU |
| GEN-JMB-0077 | (sudah PLTG) | PLTG (konfirmasi) |

### Capacity additions (2)

| ID | Lama | Baru | Unit |
|----|------|------|------|
| GEN-JMB-0124 (PLTU Indah Kiat Serang) | (kosong) | 175.0 | MW |
| GEN-JMB-0134 (PLTS ITN Malang) | (kosong) | 0.5 | MWp |

### Province corrections (8)

| ID | Lama | Baru |
|----|------|------|
| GEN-JMB-0056 (PLTD Pulau Panggang) | Other Jamali | DKI Jakarta |
| GEN-JMB-0021 (PLTP Banten?) | Banten | Jawa Barat |
| GEN-JMB-0096 (PLTP Gunung Salak) | Banten | Jawa Barat |
| GEN-JMB-0105 (PLTA Kracak) | Banten | Jawa Barat |
| GEN-JMB-0123 (PLTSa Bantargebang) | DKI Jakarta | Jawa Barat |
| GEN-JMB-0146 (PLTD Legon Bajak) | Other Jamali | Jawa Tengah |
| GEN-JMB-0147 (PLTS Pulau Nyamuk) | Other Jamali | Jawa Tengah |
| GEN-JMB-0148 (PLTS Pulau Parang) | Other Jamali | Jawa Tengah |
| GEN-JMB-0149 (PLTS Pulau Genting) | Other Jamali | Jawa Tengah |

## 4. Reclassified assets (3 entries)

### Generator → Substation (2 baru di sub master)

| Old gen ID | New sub ID | Nama |
|---|---|---|
| GEN-JMB-0086 | GI-JMB-0521 | Gardu Induk Ujungberung (Jawa Barat) |
| GEN-JMB-0111 | GI-JMB-0522 | Gardu Induk Tuban (Jawa Timur) |

### Transmission JAMALI → Sumatra (1 entries)

| Old ID | New ID | Detail |
|---|---|---|
| TRM-JMB-1097 | TRM-SMT-0795 | 150 kV, 20.015 km, osm_id way/957141001 |

## 5. Capacity formatting rule (skema)

Tambah kolom baru `capacity_unit` di `generator_master_jamali.csv`. Default
`MW`, untuk semua row dengan `type=PLTS` di-set `MWp`. Total 17 row PLTS
ter-update ke `MWp`. Untuk konsistensi cross-region, kolom ini bisa
di-propagate ke 7 region lain di iterasi berikutnya.

## 6. New GI addition (UNRESOLVED)

GI Indorama 70 kV tidak ditambahkan karena koordinat user
(`-6.555048, 170.410101`) memiliki longitude 170.4 yang berada di Pacific
Ocean (jauh di luar Indonesia). Asumsi: typo dari `107.410101`, mengacu
ke lokasi PLTU Indorama Purwakarta di lat -6.554, lon 107.414. **Perlu
konfirmasi user** sebelum di-add ke `substation_master_jamali.csv`.

## 7. Unresolved items (perlu manual review)

| ID | Masalah | Saran |
|----|---------|-------|
| GEN-JMB-0061 (PLTU TIGA) | "Reportedly not yet existing" — perlu verifikasi apakah masih di tahap rencana | Cek RUPTL Lampiran B.5 (rencana pembangkit) atau status PLN; kalau memang belum existing, set `status=planned` atau remove dari master eksisting |
| GEN-JMB-0120 (Bekas PLTA Sigelap) | Nama menyiratkan plant non-operasional ("bekas") | Verifikasi: kalau memang dekomisioning, set `status=decommissioned`; kalau heritage site, remove dari master |
| New GI Indorama 70 kV | Koordinat user di luar Indonesia | Konfirmasi koordinat aktual; saran lon 107.41 berdasar lokasi PLTU Indorama Purwakarta |
| GEN-JMB-0048 (PLTB) | Nama spesifik lokasi belum jelas | OSM hanya tag "PEMBANGKIT LISTRIK TENAGA ANGIN"; lokasi lat -5.94 lon 107.10 (Indramayu/Pantura) — verifikasi PLTB Sidrap-style spec |

## Files updated

- `data/processed/generator_master_jamali.csv` (174 rows, was 196; +1 kolom `capacity_unit`)
- `data/processed/generators_jamali.geojson` (re-built dari CSV baru)
- `data/processed/substation_master_jamali.csv` (522 rows, was 520; +2 reclassified, 2 renames)
- `data/processed/substations_jamali.geojson` (re-built)
- `data/processed/transmission_master_jamali.csv` (2.357 rows, was 2.358; -1 row pindah ke Sumatra)
- `data/processed/transmission_master_sumatra.csv` (795 rows, was 794; +1 row dari JAMALI)
- `data/processed/transmission_{jamali,sumatra}.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (38 → 47 entries; +9 JAMALI v1.0 renames)
- `web/data_jamali.js` (re-bundled)
- `web/data_sumatra.js` (re-bundled)

## Summary

- **Removed:** 22 generator entries (14 non-generator, 6 transmission tower, 2 reclassified ke GI)
- **Renamed:** 9 generator + 2 substation = 11 total
- **Reclassified:** 2 generator → substation, 1 transmission JAMALI → Sumatra
- **Type/capacity/province corrections:** 16 entries
- **Schema:** +1 kolom `capacity_unit` di generator master (PLTS = MWp, others = MW)
- **Unresolved (manual review):** 4 entries (PLTU TIGA validity, Bekas PLTA Sigelap status, GI Indorama coordinate, PLTB naming)
