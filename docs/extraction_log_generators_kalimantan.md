# Ekstraksi Pembangkit (Generators) Kalimantan — Log

**Tanggal:** 2026-05-23 — extraction perdana
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_plants.geojson`
**Output:** `data/processed/generator_master_kalimantan.csv`, `data/processed/generators_kalimantan.geojson`
**Skrip:** `scripts/extract_kalimantan_generators.py`

## Metodologi

Sama dengan extractor generator JAMALI & Sumatra: OSM `power=plant` adalah
sumber otoritatif (punya koordinat presisi). Extractor hanya mengkategorikan
tipe PLT dan meng-assign provinsi + sistem berdasarkan bbox + centroid
tiebreak. Tidak ada fuzzy matching atau override.

## Ringkasan

**66 pembangkit** ter-extract di region Kalimantan (dari ~600 plant OSM
se-Indonesia). **39 punya data kapasitas**, total **2.943 MW**.

### Per sistem listrik

| System | Cakupan | Plant (berkapasitas) | Total MW |
|--------|---------|---------------------:|---------:|
| Khatulistiwa | Kalimantan Barat | 9 | 694 |
| Kalselteng | Kalimantan Tengah + Selatan | 13 | 881 |
| Mahakam | Kalimantan Timur + Utara | 17 | 1.368 |
| **Total** | | **39** | **2.943** |

### Per jenis pembangkit (semua sistem)

| Jenis | Count | Total MW |
|-------|------:|---------:|
| PLTU (batubara) | 16 | 2.018 |
| PLTD (diesel) | 13 | 341 |
| PLTGU (gas combined cycle) | 2 | 177 |
| PLTMG (mesin gas) | 2 | 170 |
| PLTG (gas open cycle) | 2 | 140 |
| PLTS (surya) | 3 | 67 |
| PLTA (hidro besar) | 1 | 30 |

PLTU mendominasi total — **69% kapasitas (2.018 dari 2.943 MW)**. Konsisten
dengan profil Kalimantan yang sangat batubara-heavy (PLTU mulut tambang).
PLTA hampir tidak ada (cuma PLTA Riam Kanan di Kalsel) — Kalimantan minim
potensi hidro besar dibanding Sumatra.

### Per provinsi (plant berkapasitas)

| Provinsi | Count | Total MW |
|----------|------:|---------:|
| Kalimantan Timur | 15 | 1.343 |
| Kalimantan Selatan | 11 | 751 |
| Kalimantan Barat | 9 | 694 |
| Kalimantan Tengah | 2 | 130 |
| Kalimantan Utara | 2 | 25 |

## Assignment provinsi: bbox + centroid tiebreak

Seperti extractor Sumatra, OSM plant tidak punya tag provinsi — extractor
meng-assign dari koordinat. Bbox provinsi overlap di perbatasan; kalau sebuah
plant masuk >1 bbox, dipilih provinsi dengan centroid terdekat.

**Penyesuaian centroid Kalteng.** Iterasi pertama menempatkan centroid
Kalimantan Tengah di tengah-geometris provinsi (lat −1,5). Akibatnya plant
Kalteng yang terkonsentrasi di **bagian selatan** provinsi (Palangka Raya,
Pulang Pisau, Sampit) ke-tiebreak ke Kalsel. Fix: centroid Kalteng digeser
ke selatan (−2,2; 113,4), ke pusat-massa pembangkitnya yang sebenarnya.
Kalimantan Tengah memang punya pembangkit sendiri yang sedikit — banyak
disuplai lewat interkoneksi Kalselteng dari pusat pembangkitan Kalsel.

**Penyempitan bbox timur.** bbox Kaltim semula `lon_max = 119,10` —
kelewat jauh ke timur, menyebrang Selat Makassar dan menangkap pembangkit
Sulawesi Barat (area Mamuju). Setelah `lon_max` diperketat ke 118,50,
**4 PLTS kecil Sulawesi Barat yang sebelumnya bocor sebagai "Kaltim"
dikeluarkan** (70 → 66 plant). Total kapasitas praktis tidak berubah
(plant yang dikeluarkan berukuran sangat kecil).

Catatan: assignment **sistem** (Khatulistiwa / Kalselteng / Mahakam) lebih
robust daripada provinsi. Kalteng & Kalsel dua-duanya sistem Kalselteng,
jadi pergeseran province-level tidak mengubah total per-sistem.

## Review flags

| Flag | Jumlah | Arti |
|------|-------:|------|
| `NO_NAME` | 17 | Plant tanpa tag `name` di OSM |
| `NO_CAPACITY` | 27 | Plant tanpa tag `plant:output:electricity` (41%) |
| `NO_TYPE` | 3 | Tipe PLT tidak bisa diturunkan |

41% plant tanpa data kapasitas — lebih tinggi dari Sumatra (24%). Coverage
tag OSM di Kalimantan lebih tipis, terutama PLTD diesel tersebar di
pedalaman. Total 2.943 MW hanya mencakup 39 plant berkapasitas; kapasitas
sistem Kalimantan sesungguhnya lebih tinggi.

## Limitasi & batasan

- **Kapasitas dari tag OSM**, bukan sumber resmi PLN. Belum divalidasi
  silang dengan agregat RUPTL.
- **27 plant (41%) tanpa kapasitas** — total MW di atas under-estimate.
- **Assignment provinsi via bbox + centroid** — akurat untuk mayoritas, tapi
  plant sangat dekat perbatasan bisa meleset. Assignment sistem robust.
- **Coverage OSM** Kalimantan lebih tipis dari Jawa/Sumatra; pembangkit
  kecil & captive power industri tambang banyak yang belum ter-map.

## Struktur kolom CSV

Identik dengan generator JAMALI/Sumatra:

```
id              GEN-KLM-XXXX
name            nama pembangkit dari OSM ('(unnamed)' jika tidak ada)
type            PLTU / PLTGU / PLTG / PLTMG / PLTA / PLTM / PLTMH / PLTP /
                PLTS / PLTD / PLTSa / Unknown
capacity_mw     kapasitas MW (kosong jika tidak ada tag OSM)
province        provinsi (ejaan resmi BPS)
system          Khatulistiwa / Kalselteng / Mahakam
status          'existing'
operator        operator dari tag OSM
method          plant:method dari OSM
lat, lon        koordinat WGS84 (dari OSM)
osm_id          OSM way/relation/node ID
osm_source      plant:source dari OSM
review_flag     NO_NAME / NO_CAPACITY / NO_TYPE
source_id       'OSM-overpass'
```

## Kandidat iterasi berikutnya

1. Validasi silang agregat RUPTL untuk kuantifikasi gap coverage OSM.
2. Isi `capacity_mw` yang kosong (27 plant) via RUPTL / PLN Annual Report / GEM.
3. Resolve `NO_TYPE` (3 plant).
