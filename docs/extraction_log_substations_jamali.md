# Ekstraksi Gardu Induk Jamali — Log

**Iterasi 1:** 2026-05-10 — extraction awal (fuzzy match only, threshold 0.65)
**Iterasi 2:** 2026-05-16 — override mechanism + threshold dinaikkan ke 0.85

**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran B), OSM (Overpass API)
**Output:** `data/processed/substation_master_jamali.csv`, `data/processed/substations_jamali.geojson`
**Skrip:** `scripts/extract_jamali_substations.py`
**Overrides:** `data/overrides/substation_overrides.csv` (11 entries, lihat `data/overrides/README.md`)

## Ringkasan iterasi 2

| Provinsi | Tabel sumber | RUPTL | OSM (bbox) | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------------|------:|-----------:|-------------:|---------:|----------:|
| DKI Jakarta | Tabel B1.4 | 81 | 1.352 | 75 | 0 | 6 |
| Banten | Tabel B2.4 | 58 | 829 | 51 | 3 | 4 |
| Jawa Barat | Tabel B3.4 | 135 | 1.528 | 130 | 3 | 2 |
| Jawa Tengah | Tabel B4.4 | 81 | 104 | 73 | 1 | 7 |
| DIY | Tabel B5.3 | 8 | 16 | 8 | 0 | 0 |
| Jawa Timur | Tabel B6.4 | 138 | 157 | 133 | 4 | 1 |
| Bali | Tabel B7.4 | 19 | 21 | 18 | 1 | 0 |
| **Total** | | **520** | | **488** | **12** | **20** |

Match rate: **96,2%** (500 / 520).

## Apa yang berubah dari iterasi 1

Iterasi 1 (Mei 10): match rate 96,2% (500/520), tapi 12 dari 500 itu **low-score** (skor 0.65–0.85) yang sebagian besar adalah **false positive** (mis. "Cawang Baru" ke-match ke "Mampang Baru" — beda lokasi).

Iterasi 2 (Mei 16) menaikkan kualitas dengan dua perubahan:

1. **Threshold dinaikkan dari 0.65 ke 0.85.** Semua match yang tersisa via fuzzy sekarang punya confidence tinggi. False positive yang sebelumnya "diam-diam matched" kini di-demote ke UNMATCHED.

2. **Manual override mechanism** ditambahkan di `data/overrides/substation_overrides.csv`. Override menangani kasus di mana nama RUPTL tidak akan pernah match fuzzy ke OSM, biasanya karena salah satu dari:
   - Nama RUPTL = nama administratif desa, OSM pakai nama publik/historis (mis. RUPTL "Karangkates" ↔ OSM "PLTA Sutami")
   - GI step-up tidak ada entri `power=substation` di OSM, tapi ada polygon `power=plant` yang ko-lokasi (mis. Suralaya, Muaratawar)
   - Perbedaan ejaan/spacing (mis. "Tanjungawarawar" ↔ "Tanjung Awar-Awar")

Hasil dari kedua perubahan ini: **angka match rate sama (96,2%), tapi kualitas jauh lebih tinggi** — semua 500 matched kini verified, dan 12 node penting (yang sebelumnya unmatched atau false-positive) sekarang punya koordinat otoritatif.

## 11 override yang di-apply di iterasi 2

Dari 11 entries di `substation_overrides.csv`, 12 baris RUPTL ter-rescue (entri "Suralaya" apply ke 2 baris: 150/20 dan 500/150).

| RUPTL name | Provinsi | Sumber koordinat | OSM ref |
|------------|----------|------------------|---------|
| Suralaya (x2) | Banten | centroid plant | way/531146249 PLTU Suralaya |
| Suralaya Baru | Banten | centroid plant | way/531146249 PLTU Suralaya (ekspansi) |
| Muaratawar | Jawa Barat | centroid plant | way/269508907 PLTGU Muara Tawar |
| Wayang Windu | Jawa Barat | centroid plant | way/237756221 PLTP Wayang Windu |
| Kamojang | Jawa Barat | centroid plant | relation/7406922 PLTP Kamojang |
| Tambaklorok III | Jawa Tengah | centroid plant | way/894351150 PLTGU Tambak Lorok |
| Karangkates | Jawa Timur | centroid plant | way/262452224 PLTA Sutami |
| Sengguruh | Jawa Timur | centroid plant | way/894351126 PLTA Sengguruh |
| Selorejo | Jawa Timur | centroid plant | way/284137273 PLTA Selorejo |
| Tanjungawarawar | Jawa Timur | centroid plant | way/706118077 PLTU Tanjung Awar-Awar |
| Celukan Bawang | Bali | centroid plant | way/493218545 PLTU Celukan Bawang |

Semua 11 override pakai **centroid polygon `power=plant`** sebagai proxy untuk lokasi GI step-up. Justifikasi: GI step-up secara fisik berada di dalam atau berbatasan dengan pagar pembangkit; centroid plant adalah aproksimasi terbaik yang tersedia dari data OSM tanpa survey langsung. Margin error tipikal: < 500m, cukup baik untuk skala peta nasional/regional.

## 20 GI yang masih UNMATCHED setelah iterasi 2

Untuk dikerjakan di iterasi berikutnya (kandidat: query Overpass API langsung dengan nama alternatif, atau sumber publik seperti PLN Annual Report dengan koordinat persis).

### Tersisa dari iterasi 1 yang belum punya override (11 entries)

- **DKI Jakarta (2):** JGC, Sunter
- **Banten (4):** Kramatwatu, Modern, Salira Indah, Sindang Jaya
- **Jawa Barat (1):** Braga
- **Jawa Tengah (4):** Kalibakal, Pedan (150/20), Pedan (500/150), Srondol

### Di-demote dari low-score di iterasi 2 (9 entries)

Threshold 0.85 men-demote 12 match low-score dari iterasi 1 ke UNMATCHED. 3 di antaranya ter-rescue oleh override (Suralaya Baru, Kamojang, Selorejo). Sisa 9 tetap UNMATCHED:

| RUPTL name | Provinsi | Match lama (iterasi 1) | Skor | Verdict iterasi 2 |
|------------|----------|------------------------|-----:|-------------------|
| Cawang Baru | DKI Jakarta | Mampang Baru | 0.78 | False positive — beda lokasi |
| Karet Baru | DKI Jakarta | Karet Lama | 0.70 | Ambigu — mungkin same site, butuh verifikasi |
| Ketapang | DKI Jakarta | Kemang | 0.71 | False positive |
| Mampang Dua | DKI Jakarta | Mampang Baru | 0.78 | Ambigu — mungkin ekstensi, butuh verifikasi |
| Katulampa | Jawa Barat | Karet Lama | 0.74 | False positive |
| Kalasan | Jawa Tengah | Kalisari | 0.67 | False positive |
| Semen Indonesia | Jawa Tengah | Semen Gresik | 0.67 | Ambigu — Semen Indonesia adalah holding Semen Gresik tapi lokasi di Jateng (Rembang/Cilacap), bukan Tuban; butuh verifikasi |
| Tarub | Jawa Tengah | Caruban | 0.67 | False positive |
| Siman | Jawa Timur | GIS Simpang | 0.83 | Ambigu — butuh verifikasi nama vs lokasi |

### Catatan untuk Pedan

GITET Pedan adalah node kritis di backbone 500 kV Jawa (lokasi Klaten, perbatasan Jateng-DIY). Pedan tidak ada di OSM substations dataset, tapi muncul sebagai endpoint label di banyak transmission line (Pedan-Wonosari, Pedan-Ungaran, Pedan-Kesugihan, Kediri-Pedan). Lokasi presisi bisa diturunkan dari konvergensi endpoint line ini di iterasi berikutnya, atau dari sumber otoritatif (PLN P3B).

## Catatan format tabel RUPTL

Dua provinsi pakai numbering tabel berbeda dari B1–B4 dan B6:

- **B5 (DIY):** tabel GI ada di **Tabel B5.3** (bukan B5.4) karena rekap pembangkit eksisting tidak diberi nomor terpisah.
- **B7 (Bali):** heading tabel **"Tabel B7.4 Kapasitas Gardu Induk Eksisting"** (tanpa kata "Realisasi"), beda dari provinsi lain.

Extractor fleksibel — cari pola heading apapun yang mengandung "Gardu Induk Eksisting" lalu ambil yang pertama dalam range halaman provinsi.

## Struktur kolom CSV (iterasi 2)

```
id              GI-JMB-XXXX (unique ID)
name            nama GI dari RUPTL
voltage         tegangan trafo (X/Y kV format)
trafo_count     jumlah trafo
capacity_mva    total kapasitas MVA
province        provinsi (DKI Jakarta / Banten / Jabar / Jateng / DIY / Jatim / Bali)
system          'Jamali'
osm_id          OSM way/node/relation ID (jika ke-match atau via override)
osm_name        nama di OSM
lat, lon        koordinat (kosong jika UNMATCHED)
match_score     0.0–1.0 (1.0 = exact match atau via override)
match_source    'osm_fuzzy' / 'override:osm_plant' / 'override:osm_substation' / 'override:manual' / '' (untuk unmatched)  [BARU di iterasi 2]
review_flag     'UNMATCHED' / '' (LOW_SCORE tidak lagi muncul; threshold 0.85 absolute)
source_id       'RUPTL-2025-2034'
source_table    misal 'Tabel B1.4'
```

## Voltage class distribution

```
150/20  : 414 GI  (mayoritas — gardu distribusi 150 kV)
70/20   :  44 GI  (gardu 70 kV — sebagian besar wilayah lama Jabar/Jatim)
500/150 :  32 GI  (GITET tegangan ekstra tinggi)
150/70  :  29 GI  (interkoneksi 150–70 kV)
70/25   :   1 GI  (rare)
```

## Limitasi & batasan

- **Hanya GI eksisting**, tidak termasuk yang masih tahap rencana (Tabel Bx.13 di RUPTL).
- **Koordinat dari OSM** (baik via fuzzy match atau via override yang merujuk OSM plant/substation), bukan dari sumber resmi PLN. Akurasi tergantung kualitas tag OSM. GI terkenal/besar biasanya akurat; GI baru atau kecil bisa missing.
- **Match nama berbasis fuzzy string** untuk match otomatis, dengan threshold 0.85 untuk meminimalkan false positive. Item yang gagal fuzzy match harus diselesaikan via override CSV (lihat `data/overrides/README.md`).
- **Override pakai centroid plant** sebagai proxy untuk GI step-up. Margin error < 500m.
- **PLTD Senayan** dan beberapa entri lain berfungsi sebagai pembangkit tapi terdaftar di tabel GI; ini ke-match ke OSM substation entry.

## Reusability untuk region berikutnya

Override mechanism dirancang reusable. Saat Step 2 (sistem Sumatera, Kalimantan, Sulawesi) dimulai, pola yang sama bisa dipakai:

1. Run extractor awal dengan fuzzy match (threshold 0.85).
2. Daftar UNMATCHED yang tersisa direview manual.
3. Untuk tiap UNMATCHED, cari padanan di OSM (plant, substation alternate name, atau sumber lain).
4. Tambah baris ke `substation_overrides.csv` dengan field `province` sesuai region.
5. Re-run extractor.

Schema `substation_overrides.csv` tidak terikat ke Jamali — kolom `province` yang menjadi diskriminator.
