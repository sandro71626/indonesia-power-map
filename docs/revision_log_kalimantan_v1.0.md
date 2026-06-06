# KALIMANTAN v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset Kalimantan (generator) + legend update (disclaimer modal, global)
**Sebelum:** 66 generator
**Sesudah:** 68 generator (+2 net: -2 remove, -3 merged-drop, +7 added)

## Catatan re-run protocol

Sama pola JAMALI/Sumatra v1.0: revisi diterapkan via skrip one-shot ke master
CSV dan GeoJSON. Name renames di-append ke
`data/overrides/generator_name_overrides.csv` (55 → 75 entries; +20
Kalimantan v1.0). 7 entries baru ditambahkan **tanpa OSM source** (manual
add, `review_flag=MANUAL_ADD_v1.0`, `source_id=manual_revision_v1.0`).
Penghapusan, koreksi tipe/kapasitas/status, merge, dan add manual belum
punya mekanisme override otomatis di extractor; re-run
`extract_kalimantan_generators.py` akan menghapus revisi (kecuali rename
yang persistent via override CSV).

---

## 1. Removed assets (2 entries)

| ID | Nama OSM | Catatan |
|----|----------|---------|
| GEN-KLM-0019 | (unnamed) | way/695724354 — tidak teridentifikasi |
| GEN-KLM-0044 | EQUATORIAL BUMI PERSADA | way/1211621343 — aset non-pembangkit |

## 2. Renamed assets (20 entries)

Semua append ke `generator_name_overrides.csv` untuk persistence.

### Coal plants (4 entries)

| ID | Lama → Baru | Capacity |
|----|---|---|
| GEN-KLM-0045 | PLTU WHW Ketapang (rename + cap) | 20 MW (2 × 10 MW) |
| GEN-KLM-0032 | PLTU Kalselteng-1 Pulang Pisau | 200 MW |
| GEN-KLM-0043 | PLTU Kaltim (rename) | - |
| GEN-KLM-0051 | PLTU Lati (koreksi typo "PTLU" → "PLTU") | 28 MW |

### Solar plants (16 entries) — semua satuan MWp

| ID | Nama baru | Capacity |
|----|-----------|---------:|
| GEN-KLM-0058 | PLTS Temajuk | 0,371 MWp |
| GEN-KLM-0036 | PLTS Tower BTS Desa Long Apari | 0,0054 MWp |
| GEN-KLM-0035 | PLTS Terpusat Long Penaneh | 0,0608 MWp |
| GEN-KLM-0042 | PLTS Long Pahangai | 0,120 MWp |
| GEN-KLM-0039 | PLTS Long Nawang | 0,100 MWp |
| GEN-KLM-0066 | PLTS Terpusat Long Sului | 0,04149 MWp |
| GEN-KLM-0059 | PLTS Derawan | 0,080 MWp |
| GEN-KLM-0062 | PLTS Long Belaka Pitau | 0,075 MWp |
| GEN-KLM-0065 | PLTS Terpusat Desa Long Jalan | unknown, **status planned** |
| GEN-KLM-0055 | PLTS Terpusat Long Pada | 0,030 MWp |
| GEN-KLM-0037 | PLTS Terpusat Long Layu | 0,050 MWp |
| GEN-KLM-0056 | PLTS Klaster Suka Maju | 0,086 MWp |
| GEN-KLM-0057 | PLTS Terpusat Sumentobol | unknown, status existing |
| GEN-KLM-0064 | PLTS Terpusat Desa Tepian | 0,075 MWp |
| GEN-KLM-0063 | PLTS Terpusat Pos Pamtas GABMA | 0,0125 MWp (midpoint dari range 10–15 kWp) |

## 3. Merged assets (4 → 1)

Konsolidasi PLTS Badak LNG yang sebelumnya tersebar 4 row terpisah di
koordinat cluster Bontang (0.107–0.109, 117.475–117.477).

| Drop | Konsolidasi ke |
|---|---|
| GEN-KLM-0047 (way/1231910574) | GEN-KLM-0046 |
| GEN-KLM-0048 (way/1231910575) | GEN-KLM-0046 |
| GEN-KLM-0049 (way/1231910576) | GEN-KLM-0046 |
| **Entry tersisa** | **GEN-KLM-0046** = `PLTS Badak LNG`, PLTS, **4 MWp**, status existing |

## 4. New assets (7 entries)

`review_flag=MANUAL_ADD_v1.0`, `source_id=manual_revision_v1.0`,
`osm_id=(kosong)`.

### Diesel (3 entries)

| ID | Nama | Capacity (MW) | Status | Koord |
|----|------|---:|--------|------|
| GEN-KLM-0067 | PLTD Long Apari | 0,48 | existing | 0,774872, 114,271540 |
| GEN-KLM-0068 | PLTD Long Pahangai | 0,24 | existing | (sama dgn PLTS Long Pahangai: 0,886, 114,690) |
| GEN-KLM-0069 | PLTD Long Nawang | 2,0 | existing | (sama dgn PLTS Long Nawang: 1,783, 114,905) |

### Solar (4 entries, MWp)

| ID | Nama | Capacity (MWp) | Status | Koord |
|----|------|---:|--------|------|
| GEN-KLM-0070 | PLTS Kampung Teluk Semanting | 0,040 | existing | 2,187761, 117,955244 |
| GEN-KLM-0071 | PLTS Desa Pegat Batumpuk | 0,04045 | existing | 2,06742, 117,30345 |
| GEN-KLM-0072 | PLTS Desa Patal | 0,074 | planned | 4,129278, 116,251278 |
| GEN-KLM-0073 | PLTS Desa Sedalit | 0,0528 | existing | 4,264722, 116,146389 |

## 5. Status changes (3 entries)

| ID | Lama → Baru |
|----|---|
| GEN-KLM-0065 (PLTS Terpusat Desa Long Jalan) | existing → **planned** |
| GEN-KLM-0057 (PLTS Terpusat Sumentobol) | existing → existing (eksplisit konfirmasi) |
| GEN-KLM-0063 (PLTS Pos Pamtas GABMA) | existing → existing (eksplisit konfirmasi) |
| GEN-KLM-0072 (PLTS Desa Patal — new) | — → planned |

## 6. Capacity formatting rule

Kolom `capacity_unit` ditambahkan. Default `MW`, untuk semua row dengan
`type=PLTS` di-set `MWp`. Total **23 row PLTS** ber-`MWp` di Kalimantan
(termasuk 4 PLTS baru yang manual-added). Untuk PLTS dengan capacity
< 100 kWp dan tanpa note "planned/proposed", default status = `existing`
(aturan user).

## 7. Legend update (global, semua sistem)

Disclaimer modal section "Konvensi simbol" diperbarui supaya label
singkatan jenis pembangkit dijabarkan lengkap, dengan penekanan pada:

- **MG = Mesin Gas (PLTMG)**
- **BM = Biomassa**

Selain itu juga ditambahkan Bg = Biogas (mengakomodasi kategori PLTBg
yang diperkenalkan di Sumatra v1.0).

Versi baru:
```
Lingkaran menandai pembangkit (generator). Label di dalam lingkaran
menyatakan jenis pembangkit: U=Uap, GU=Gas&Uap, G=Gas, MG=Mesin Gas
(PLTMG), A=Air, M=Mini-hidro, P=Panas Bumi, S=Surya, B=Bayu,
BM=Biomassa, Bg=Biogas, D=Diesel, Sa=Sampah.
```

## 8. Cleanup

Stray reference `"Sumatra hapus aja"` di-search di seluruh repo (`.csv`,
`.md`, `.html`, `.py`) — **0 hits**. Tidak ada artefak editing yang
perlu dihapus.

## 9. Unresolved items (perlu manual review)

Tidak ada unresolved item dari user spec untuk Kalimantan v1.0. Semua
instruksi sudah ter-aplikasikan. Catatan tambahan:

- **GEN-KLM-0063** (PLTS Pos Pamtas GABMA): capacity user di-spec sebagai
  range "0,010–0,015 MWp"; saya pakai midpoint 0,0125 MWp untuk nilai
  numerik tunggal. Apabila prefer endpoint tertentu (10 atau 15 kWp),
  perlu eksplisit user instruction.
- **GEN-KLM-0068** (PLTD Long Pahangai) & **GEN-KLM-0069** (PLTD Long
  Nawang): koordinat asumsi sama dengan PLTS counterpart karena user
  hanya menyebutkan "use same location" untuk Pahangai, dan tidak
  memberi koord eksplisit untuk Nawang.

## Files updated

- `data/processed/generator_master_kalimantan.csv` (68 rows, was 66; +1 kolom `capacity_unit`)
- `data/processed/generators_kalimantan.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (55 → 75 entries; +20 Kalimantan v1.0)
- `web/data_kalimantan.js` (re-bundled)
- `web/preview_indonesia.html` (legend di disclaimer modal updated dengan MG/BM/Bg expansion)

## Summary

- **Removed:** 2 entries (EQUATORIAL BUMI PERSADA + 1 unnamed)
- **Renamed:** 20 entries (4 coal + 16 solar; standardisasi nama PLTU/PLTS Terpusat/Klaster)
- **Merged:** 4 → 1 (PLTS Badak LNG, 4 MWp)
- **Added:** 7 entries (3 PLTD: Long Apari, Long Pahangai, Long Nawang + 4 PLTS: Teluk Semanting, Pegat Batumpuk, Patal, Sedalit)
- **Status changes:** 1 ke `planned` (GEN-KLM-0065), 1 PLTS baru `planned` (GEN-KLM-0072), 2 eksplisit `existing` konfirmasi
- **Schema:** +1 kolom `capacity_unit` (23 PLTS ber-`MWp`)
- **Legend update:** Modal disclaimer "Konvensi simbol" diperbarui dengan MG=Mesin Gas, BM=Biomassa, Bg=Biogas
- **Cleanup:** stray "Sumatra hapus aja" tidak ditemukan (0 hits di repo); skip
- **Unresolved:** none (semua instruksi user ter-apply; 2 catatan asumsi: range capacity midpoint & koord PLTD pakai PLTS counterpart)
