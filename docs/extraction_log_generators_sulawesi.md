# Ekstraksi Pembangkit (Generators) Sulawesi — Log

**Tanggal:** 2026-05-26 — extraction perdana (Step 4)
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_plants.geojson`
**Output:** `data/processed/generator_master_sulawesi.csv`, `data/processed/generators_sulawesi.geojson`
**Skrip:** `scripts/extract_sulawesi_generators.py`

## Metodologi

Sama dengan extractor generator JAMALI, Sumatra & Kalimantan: OSM `power=plant`
adalah sumber otoritatif (punya koordinat presisi). Extractor mengkategorikan
tipe PLT dan meng-assign provinsi + sistem berdasarkan bbox + centroid
tiebreak. Tidak ada fuzzy matching atau override koordinat.

Beda dengan Kalimantan: geografi Sulawesi (huruf "K", empat semenanjung)
membuat bbox provinsi banyak yang overlap. Lihat bagian "Assignment provinsi"
di bawah.

## Ringkasan

**101 pembangkit** ter-extract di region Sulawesi (dari ~600 plant OSM
se-Indonesia). **55 punya data kapasitas**, total **3.795 MW**.

### Per sistem listrik

| System | Cakupan | Plant (berkapasitas) | Total MW |
|--------|---------|---------------------:|---------:|
| Sulutgo | Sulawesi Utara + Gorontalo | 19 | 840 |
| Sulteng | Sulawesi Tengah | 4 | 895 |
| Sulselrabar | Sulsel + Sultra + Sulbar | 32 | 2.059 |
| **Total** | | **55** | **3.795** |

### Per jenis pembangkit (semua sistem)

| Jenis | Count | Total MW |
|-------|------:|---------:|
| PLTU (batubara) | 16 | 1.784 |
| PLTA (hidro besar) | 12 | 1.296 |
| PLTGU (gas combined cycle) | 1 | 180 |
| PLTB (bayu/angin) | 2 | 147 |
| PLTP (panas bumi) | 3 | 120 |
| PLTD (diesel) | 5 | 102 |
| PLTG (gas open cycle) | 1 | 100 |
| PLTS (surya) | 14 | 35 |
| PLTMG (mesin gas) | 1 | 30 |

PLTU tetap jenis terbesar (**47% kapasitas, 1.784 dari 3.795 MW**), tapi
profil Sulawesi jauh lebih beragam dari Kalimantan. **PLTA menyumbang 34%**
(1.296 MW) — kontras tajam dengan Kalimantan yang nyaris tanpa hidro:
Sulawesi punya PLTA Poso (Sulteng) dan kompleks PLTA Vale di Luwu Timur
(Sulsel). Sulawesi juga punya **PLTP** (panas bumi — PLTP Lahendong di
Sulawesi Utara) dan **PLTB** (kebun angin — PLTB Sidrap/Tolo di Sulsel),
dua jenis yang absen di Kalimantan.

### Per provinsi (plant berkapasitas)

| Provinsi | Count | Total MW |
|----------|------:|---------:|
| Sulawesi Selatan | 18 | 1.804 |
| Sulawesi Tengah | 4 | 895 |
| Gorontalo | 7 | 466 |
| Sulawesi Utara | 12 | 374 |
| Sulawesi Tenggara | 9 | 205 |
| Sulawesi Barat | 5 | 51 |

Sulawesi Selatan mendominasi (1.804 MW) — konsisten dengan posisinya
sebagai pusat beban terbesar. Sulawesi Tengah hanya 4 plant berkapasitas
tapi 895 MW: hanya berisi pembangkit besar — PLTA Poso (±515 MW dalam 2
entri OSM) dan 2 PLTU. Sulawesi Barat paling kecil (51 MW) — sistem yang
sebagian besar disuplai lewat interkoneksi Sulselrabar.

## Assignment provinsi: bbox + centroid tiebreak

OSM plant tidak punya tag provinsi — extractor meng-assign dari koordinat.
Bbox provinsi overlap di perbatasan; kalau sebuah plant masuk >1 bbox,
dipilih bbox dengan centroid terdekat.

**Centroid per-bbox (bukan per-provinsi).** Berbeda dari extractor
Kalimantan, di Sulawesi tiap entri bbox punya centroid sendiri — jadi satu
provinsi boleh punya beberapa bbox dengan centroid berbeda. Ini perlu
karena tiga wilayah di **zona tripoint Sulsel/Sulteng/Sultra** berada di
latitude yang sama dan tidak bisa dipisahkan oleh satu centroid per
provinsi:

| Lobe bbox | Provinsi | Alasan |
|-----------|----------|--------|
| Lobe Morowali | Sulawesi Tengah | Morowali menjorok ke tenggara; IMIP/Bungku selatitude dengan Sultra |
| Lobe Luwu Timur | Sulawesi Selatan | Sorowako/Malili (kompleks PLTA Vale) selatitude dengan Morowali |
| Strip Kolaka Utara | Sulawesi Tenggara | Kolaka Utara menjorok ke utara di pantai barat |

**Koreksi run pertama — kompleks PLTA Vale.** Run pertama meng-assign
PLTA Larona, Karebbe, Balambano (kompleks hidro PT Vale Indonesia) ke
Sulawesi Tenggara. Ketiganya sebenarnya di **Luwu Timur, Sulawesi
Selatan** — strip Kolaka Utara semula terlalu lebar ke timur (lon_max
121,45) dan menangkapnya. Fix: strip Kolaka Utara dipersempit ke
lon_max 121,13 (berhenti sebelum kompleks Vela di lon ≈121,18+) dan
ditambah lobe Luwu Timur khusus untuk Sulsel. Setelah fix: 5 plant
(3 PLTA Vale + 2 plant tak-bernama di sekitar Sorowako) pindah dari
Sulawesi Tenggara ke Sulawesi Selatan; 4 plant kawasan Morowali
(Labota, IMIP, Wanxiang, PLTU Ambunu) tetap benar di Sulawesi Tengah.

Catatan: assignment **sistem** lebih robust daripada provinsi. Sulsel,
Sultra, dan Sulbar semuanya sistem Sulselrabar — jadi koreksi Vela di
atas memperbaiki label provinsi tapi tidak mengubah total per-sistem.

**PROVINCE_OVERRIDE.** Extractor menyediakan dict `osm_id -> (provinsi,
sistem)` sebagai cadangan kalau lobe-bbox pun masih salah. Saat ini
kosong — tiga lobe-bbox sudah cukup; mekanisme disimpan untuk kasus baru
bila OSM di-pull ulang.

## Review flags

| Flag | Jumlah | Arti |
|------|-------:|------|
| `NO_NAME` | 19 | Plant tanpa tag `name` di OSM |
| `NO_CAPACITY` | 46 | Plant tanpa tag `plant:output:electricity` (46%) |
| `NO_TYPE` | 15 | Tipe PLT tidak bisa diturunkan |

**46% plant tanpa data kapasitas** — lebih tinggi dari Kalimantan (41%)
dan Sumatra (24%). Banyak plant tak-bernama/tanpa-kapasitas adalah captive
power kawasan industri tambang nikel (Morowali, Konawe) yang ter-map di OSM
sebagai poligon `power=plant` tanpa atribut lengkap. Total **3.795 MW hanya
mencakup 55 plant berkapasitas** — kapasitas terpasang Sulawesi yang
sesungguhnya lebih tinggi.

## Limitasi & batasan

- **Kapasitas dari tag OSM**, bukan sumber resmi PLN. Belum divalidasi
  silang dengan agregat RUPTL.
- **46 plant (46%) tanpa kapasitas** — total MW di atas under-estimate;
  paling kentara untuk captive power smelter nikel.
- **PLTA Poso** muncul sebagai 2 entri OSM (±515 MW) — kemungkinan
  pemisahan unit/bendung; tidak digabung agar konsisten dengan geometri OSM.
- **Assignment provinsi via bbox + centroid** — akurat untuk mayoritas;
  zona tripoint Sulsel/Sulteng/Sultra ditangani lewat 3 lobe-bbox. Plant
  baru sangat dekat perbatasan tetap perlu dicek. Assignment sistem robust.
- **Coverage OSM** Sulawesi tipis di luar koridor kota; PLTD pedesaan dan
  PLTM/PLTMH banyak yang belum ter-map.

## Struktur kolom CSV

Identik dengan generator JAMALI/Sumatra/Kalimantan:

```
id              GEN-SLW-XXXX
name            nama pembangkit dari OSM ('(unnamed)' jika tidak ada)
type            PLTU / PLTGU / PLTG / PLTMG / PLTA / PLTM / PLTMH / PLTP /
                PLTS / PLTB / PLTD / PLTSa / Unknown
capacity_mw     kapasitas MW (kosong jika tidak ada tag OSM)
province        provinsi (ejaan resmi BPS)
system          Sulutgo / Sulteng / Sulselrabar
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
2. Isi `capacity_mw` yang kosong (46 plant) via RUPTL / PLN Annual Report / GEM.
3. Resolve `NO_TYPE` (15 plant) — sebagian captive power smelter nikel.
4. Cek apakah 2 entri PLTA Poso perlu digabung jadi satu fasilitas.
