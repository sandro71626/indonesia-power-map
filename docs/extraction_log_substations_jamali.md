# Ekstraksi Gardu Induk Jamali — Log

**Tanggal:** 2026-05-10
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran B), OSM (Overpass API)
**Output:** `data/processed/substation_master_jamali.csv`, `data/processed/substations_jamali.geojson`
**Skrip:** `scripts/extract_jamali_substations.py`

## Ringkasan

| Provinsi | Tabel sumber | RUPTL | OSM (bbox) | Matched | Unmatched | Low score |
|----------|-------------|------:|-----------:|--------:|----------:|----------:|
| DKI Jakarta | Tabel B1.4 | 81 | 1.352 | 79 | 2 | 4 |
| Banten | Tabel B2.4 | 58 | 829 | 52 | 6 | 1 |
| Jawa Barat | Tabel B3.4 | 135 | 1.528 | 132 | 3 | 2 |
| Jawa Tengah | Tabel B4.4 | 81 | 104 | 76 | 5 | 3 |
| DIY | Tabel B5.3 | 8 | 16 | 8 | 0 | 0 |
| Jawa Timur | Tabel B6.4 | 138 | 157 | 135 | 3 | 2 |
| Bali | Tabel B7.4 | 19 | 21 | 18 | 1 | 0 |
| **Total** | | **520** | | **500** | **20** | **12** |

Match rate: **96,2%** (500 / 520).

## Catatan format tabel

Dua provinsi pakai numbering tabel berbeda dari B1–B4 dan B6:

- **B5 (DIY):** tabel GI ada di **Tabel B5.3** (bukan B5.4) karena rekap pembangkit eksisting tidak diberi nomor terpisah.
- **B7 (Bali):** heading tabel **"Tabel B7.4 Kapasitas Gardu Induk Eksisting"** (tanpa kata "Realisasi"), beda dari provinsi lain.

Extractor sekarang fleksibel — cari pola heading apapun yang mengandung "Gardu Induk Eksisting" lalu ambil yang pertama dalam range halaman provinsi.

## Item yang butuh review manual

### Unmatched (20 GI tanpa koordinat OSM)

GI besar dan penting yang tidak ke-match:

- **Suralaya** dan **Suralaya 500/150** (Banten) — PLTU & GITET utama Jawa Barat, kemungkinan ada di OSM dengan nama berbeda atau tag berbeda.
- **Muaratawar** (Jawa Barat, 500/150) — PLTGU besar.
- **Pedan** dan **Pedan 500/150** (Jawa Tengah) — gardu interkoneksi.
- **Wayang Windu** (Jawa Barat, 150/70) — terkait PLTP.
- **Karangkates, Sengguruh** (Jawa Timur, 70/20) — terkait PLTA.
- **Tambaklorok III** (Jawa Tengah).

GI lain yang unmatched: JGC, Sunter (DKI); Kramatwatu, Modern, Salira Indah, Sindang Jaya (Banten); Braga (Jabar); Kalibakal, Srondol (Jateng); Tanjungawarawar (Jatim); Celukan Bawang (Bali).

### Low-score matches (12, kemungkinan false positive)

Cek manual karena score < 0.85:

| RUPTL | OSM | Score | Catatan |
|-------|-----|-------|---------|
| Cawang Baru (DKI) | Mampang Baru | 0.78 | False positive — beda lokasi |
| Karet Baru (DKI) | Karet Lama | 0.70 | Mungkin sama (kembar) atau beda — verify |
| Ketapang (DKI) | Kemang | 0.71 | False positive |
| Mampang Dua (DKI) | Mampang Baru | 0.78 | Mungkin sama site |
| Suralaya Baru (Banten) | Muara Karang Baru | 0.67 | False positive |
| Kamojang (Jabar) | Kemang | 0.71 | False positive |
| Katulampa (Jabar) | Karet Lama | 0.74 | False positive |
| Kalasan (Jateng) | Kalisari | 0.67 | False positive |
| Semen Indonesia (Jateng) | Semen Gresik | 0.67 | False positive |
| Tarub (Jateng) | Caruban | 0.67 | False positive |
| Selorejo (Jatim) | Sukorejo | 0.75 | False positive |
| Siman (Jatim) | GIS Simpang | 0.83 | Verify |

Action: di iterasi berikutnya, naikan threshold ke 0.85 + manual override CSV untuk pasangan yang benar.

## Struktur kolom CSV

```
id              GI-JMB-XXXX (unique ID)
name            nama GI dari RUPTL
voltage         tegangan trafo (X/Y kV format)
trafo_count     jumlah trafo
capacity_mva    total kapasitas MVA
province        provinsi (DKI Jakarta / Banten / Jabar / Jateng / DIY / Jatim / Bali)
system          'Jamali'
osm_id          OSM way/node ID (jika ke-match)
osm_name        nama di OSM
lat, lon        koordinat (kosong jika belum ke-match)
match_score     0.0–1.0 (1.0 = exact match)
review_flag     'UNMATCHED' / 'LOW_SCORE' / '' (untuk filter review)
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
- **Koordinat dari OSM**, bukan dari sumber resmi PLN. Akurasi tergantung kualitas tag OSM. GI terkenal/besar biasanya akurat; GI baru atau kecil bisa missing.
- **Match nama berbasis fuzzy string**, bukan otoritatif. Item dengan score < 0.85 wajib direview.
- **PLTD Senayan** dan beberapa entri lain berfungsi sebagai pembangkit tapi terdaftar di tabel GI; ini ke-match ke OSM substation entry.
