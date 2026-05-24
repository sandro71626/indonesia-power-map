# Ekstraksi Gardu Induk Sulawesi — Log

**Tanggal:** 2026-05-26 — extraction perdana (Step 4)
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran C, Tabel C1–C6), OSM (Overpass API)
**Output:** `data/processed/substation_master_sulawesi.csv`, `data/processed/substations_sulawesi.geojson`
**Skrip:** `scripts/extract_sulawesi_substations.py`
**Overrides:** `data/overrides/substation_overrides.csv` (7 entries Sulawesi, shared dgn JAMALI, Sumatra & Kalimantan)

**Threshold matching identik:** 0.85 absolute, override prioritas pertama, fuzzy SequenceMatcher di bawahnya.

## Ringkasan

| Provinsi | Tabel | System | RUPTL | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------|--------|------:|-------------:|---------:|----------:|
| Sulawesi Utara | C1 | Sulutgo | 24 | 19 | 1 | 4 |
| Sulawesi Tengah | C2 | Sulteng | 15 | 14 | 0 | 1 |
| Gorontalo | C3 | Sulutgo | 7 | 6 | 1 | 0 |
| Sulawesi Selatan | C4 | Sulselrabar | 40 | 32 | 3 | 5 |
| Sulawesi Tenggara | C5 | Sulselrabar | 13 | 8 | 2 | 3 |
| Sulawesi Barat | C6 | Sulselrabar | 6 | 6 | 0 | 0 |
| **Total** | | | **105** | **85** | **7** | **13** |

Match rate: **87,6%** (92 / 105).

Breakdown per sistem listrik:

| System | Cakupan | Matched | Total | Rate |
|--------|---------|--------:|------:|-----:|
| Sulutgo | Sulawesi Utara + Gorontalo | 27 | 31 | 87.1% |
| Sulteng | Sulawesi Tengah | 14 | 15 | 93.3% |
| Sulselrabar | Sulawesi Selatan + Sulawesi Tenggara + Sulawesi Barat | 51 | 59 | 86.4% |

## Catatan ekstraksi

### Urutan tabel: terverifikasi di awal, tidak ada swap

RUPTL Lampiran A sudah dua kali memuat urutan provinsi yang tidak alfabetis (Sumatra A3–A8, Kalimantan A12↔A13). Untuk Sulawesi, urutan diverifikasi **sebelum** menulis extractor — `scripts/_probe_c_provinces.py` mengekstrak 8 nama GI pertama tiap tabel C dan mencocokkannya dengan kota/kabupaten:

| Tabel | Provinsi | Bukti nama GI |
|-------|----------|---------------|
| C1 | Sulawesi Utara | Ranomut, Sawangan, Tomohon, Bitung, Kema, Likupang |
| C2 | Sulawesi Tengah | Palu, Poso, Parigi, Tolitoli, Luwuk, Tentena |
| C3 | Gorontalo | Gorontalo, Marisa, Isimu, Botupingge, Paguat |
| C4 | Sulawesi Selatan | Panakkukang, Tello, Tallasa, Maros, Pangkep, Bone |
| C5 | Sulawesi Tenggara | Kendari, Unaaha, Kolaka, Bau-Bau, Lasusua |
| C6 | Sulawesi Barat | Mamuju, Polewali, Majene, Topoyo |

C1–C6 ternyata berurutan; tidak ada swap. Verifikasi nama tetap dilakukan karena urutan RUPTL tidak bisa diasumsikan.

### Struktur 3 sub-sistem

Region Sulawesi dibagi 3 sub-sistem listrik (field `system`):

- **Sulutgo** — Sulawesi Utara + Gorontalo. Sistem Minahasa, satu interkoneksi di lengan utara.
- **Sulteng** — Sulawesi Tengah. Sistem Palu, terhubung ke koridor tengah.
- **Sulselrabar** — Sulawesi Selatan + Sulawesi Tenggara + Sulawesi Barat. Sistem terbesar, backbone Makassar–Parepare–Palopo.

PLN sedang menyambungkan Sulbagsel (Sulselrabar) dan Sulbagut (Sulutgo + Sulteng) menjadi satu interkoneksi Sulawesi; label sub-sistem tetap dipakai karena masih relevan secara operasional dan dispatch.

### Sulselrabar mendominasi

59 dari 105 GI (56%) ada di Sulselrabar — konsisten dengan posisi Sulawesi Selatan sebagai pusat beban dan pembangkitan terbesar di Sulawesi. Sulteng paling kecil (15 GI) tapi punya match rate tertinggi (93,3%) karena GI-nya terkonsentrasi di koridor kota yang sudah ter-tag baik di OSM.

## 7 override yang di-apply

GI step-up yang ko-lokasi dengan pembangkit memakai centroid plant OSM; sisanya memakai OSM substation langsung yang tidak ter-fuzzy karena selisih penamaan.

| RUPTL name | Provinsi | Sumber koordinat |
|------------|----------|------------------|
| Amurang | Sulawesi Utara | centroid PLTU Amurang (way/943309157) |
| Anggrek (PLTU Gorontalo) | Gorontalo | centroid PLTU Anggrek (way/942620063) |
| Tello | Sulawesi Selatan | centroid kompleks pembangkit Tello (way/109924603) |
| Sengkang | Sulawesi Selatan | centroid PLTGU Sengkang (way/367586568) |
| Punagaya | Sulawesi Selatan | centroid PLTU Jeneponto/Punagaya (way/905955777) |
| Nii Tanasa | Sulawesi Tenggara | centroid PLTU Nii Tanasa (way/943189957) |
| Kendari 150 kV | Sulawesi Tenggara | OSM Gardu Induk New Kendari (way/943189956) |

Catatan: "Anggrek (PLTU Gorontalo)" dan "Punagaya" adalah contoh GI yang RUPTL namai mengikuti pembangkit ko-lokasi — Anggrek = PLTU Gorontalo Utara, Punagaya = PLTU Jeneponto. "Kendari 150 kV" di RUPTL dipetakan ke OSM "Gardu Induk New Kendari" (GI baru, beda generasi dari GI Kendari lama).

## 13 GI yang masih UNMATCHED

Mayoritas GI distribusi atau town feeder kecil yang belum ada di OSM substations dataset dan tidak punya padanan pembangkit. Untuk iterasi berikutnya: PLN Annual Report atau Overpass API direct query.

| RUPTL name | Provinsi | Catatan |
|------------|----------|---------|
| Buroko | Sulawesi Utara | Bolaang Mongondow Utara, area Kotamobagu |
| GIS Sario | Sulawesi Utara | GIS (gas-insulated) dalam kota Manado — belum di-tag di OSM |
| GI Tutuyuan | Sulawesi Utara | Bolaang Mongondow Timur |
| GI Bintauna (Town Feeder) | Sulawesi Utara | Town feeder Bintauna, Bolaang Mongondow Utara |
| Palu Baru | Sulawesi Tengah | Kemungkinan GI baru pasca-rekonstruksi Palu; tidak di-override (konservatif, padanan belum dipastikan) |
| Bontoala | Sulawesi Selatan | GI dalam kota Makassar |
| *(baris nama kosong)* | Sulawesi Selatan | Artefak parsing tabel C4 — baris tanpa nama GI; di-flag UNMATCHED, perlu dibersihkan di iterasi berikut |
| Borongloe | Sulawesi Selatan | Gowa, area Malino |
| Balusu | Sulawesi Selatan | Barru; ada kandidat OSM tapi tidak dipastikan — tidak di-override (konservatif) |
| Belopa | Sulawesi Selatan | Ibu kota Luwu |
| Moramo TFT | Sulawesi Tenggara | Town feeder transformer Moramo, Konawe Selatan |
| Wolo | Sulawesi Tenggara | Kolaka |
| Kasi Pute | Sulawesi Tenggara | Kasipute, Bombana |

Catatan baris kosong: parser tabel C4 menangkap satu baris tanpa nama GI (kemungkinan baris lanjutan/sub-total di PDF). Dipertahankan sebagai UNMATCHED dan bukan dihapus diam-diam agar hitungan RUPTL (105) tetap transparan; akan dirapikan saat extractor C-tables di-refine untuk Step 5.

## Struktur kolom CSV

Identik dengan JAMALI/Sumatra/Kalimantan. Highlights:

- `id` — prefix `GI-SLW-XXXX`
- `system` — `Sulutgo` / `Sulteng` / `Sulselrabar`
- `match_source` — `osm_fuzzy` / `override:osm_plant` / `override:osm_substation`
- `review_flag` — `UNMATCHED` atau kosong
- `source_table` — `Tabel C1.4` … `Tabel C6.4`

CSV memuat seluruh 105 baris RUPTL (termasuk 13 UNMATCHED tanpa koordinat); GeoJSON hanya memuat **92 fitur** yang ter-match dan punya koordinat.

## Limitasi & batasan

- **Hanya GI eksisting** (Tabel Cx.4), tidak termasuk yang masih tahap rencana.
- **Coverage OSM** Sulawesi lebih tipis dari Jawa; banyak town feeder kecil dan GIS dalam kota belum di-tag.
- **Baris kosong C4** — artefak parsing, di-flag UNMATCHED; perlu pembersihan parser tabel C di Step 5.
- **Bbox per provinsi** overlap di perbatasan; ditangani via name match dalam konteks tabel per-provinsi.
- **Palu Baru & Balusu** sengaja tidak di-override walau ada kandidat — padanan belum cukup pasti; lebih baik UNMATCHED yang jujur daripada koordinat keliru.

## Reusability untuk Maluku-Papua & Nusa Tenggara

Probe `scripts/_probe_c_provinces.py` sudah memetakan seluruh Lampiran C: C1–C6 Sulawesi, **C7 Maluku, C8 Maluku Utara, C9 Papua, C10 Papua Barat** (Step 5), **C11 NTB, C12 NTT** (Step 6). Pola tetap sama:

1. Page range sudah diketahui (lihat `_probe_c_provinces.py`); tetap verifikasi urutan via nama GI.
2. Copy `extract_sulawesi_substations.py`, ganti PROVINCES + ID prefix + path output.
3. Run, cross-check nama kota, populate override, iterate sampai 85%+.
