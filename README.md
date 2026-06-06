# Peta Ketenagalistrikan Indonesia

> Indonesia Power Map adalah peta digital sistem tenaga listrik Indonesia berbasis data publik, ditujukan untuk edukasi, eksplorasi, dan analisis umum.

**Status:** Beta · **Versi:** v1.0.0-beta · **Pembaruan terakhir:** 30 Mei 2026 · **Diinisiasi:** 2026

[![DOI](https://zenodo.org/badge/1236669929.svg)](https://doi.org/10.5281/zenodo.20208412)
---

## Visi

Membangun peta digital ketenagalistrikan Indonesia yang mengubah informasi teknis yang tersebar di RUPTL, laporan PLN, dan sumber publik lain menjadi visualisasi sistem tenaga yang mudah dipahami, dieksplorasi, dan dikembangkan.

Targetnya bukan dashboard operasi atau SCADA publik, melainkan **"knowledge map" sistem kelistrikan Indonesia** yang dapat dimanfaatkan oleh mahasiswa, peneliti, analis kebijakan, media, dan publik dengan latar belakang teknis.

Konsep lengkap ada di [`docs/concept/`](docs/concept/).

## Status & cakupan saat ini

Cakupan tersedia secara nasional dari Sabang sampai Merauke, dengan tingkat kelengkapan data yang bervariasi antar wilayah. Backbone di Jawa, Sumatra, dan Sulawesi tergolong padat, sementara Indonesia Timur (Maluku, Papua, dan sub-pulau NTT) masih lebih tipis seiring keterbatasan cakupan OSM. Rincian per layer dan region:

| Region | Pembangkit | Gardu Induk (RUPTL / ter-koord) | Transmisi |
|--------|-----------:|--------------------------------:|----------:|
| JAMALI (Jawa-Madura-Bali)   | 196 | 520 / 500 | 2.358 |
| Sumatra                     | 133 | 214 / 195 |   794 |
| Kalimantan                  |  66 | 100 /  85 |   332 |
| Sulawesi                    | 101 | 106 /  94 |   390 |
| Maluku                      |  19 |  12 /  12 |    61 |
| Papua                       |  16 |   8 /   8 |    36 |
| Nusa Tenggara Barat (NTB)   |  18 |  26 /  21 |    31 |
| Nusa Tenggara Timur (NTT)   |  41 |  19 /  16 |    51 |
| **Total** | **590** | **1.005 / 931** | **4.053** |

Catatan: kolom "Gardu Induk" memuat jumlah baris RUPTL Lampiran A sampai C (`x`) dan jumlah yang terkoordinat di OSM atau melalui override (`y`). Match rate global mencapai ~94%, dengan Nusa Tenggara terendah pada 82% akibat keterbatasan cakupan OSM di wilayah rural. Detail per region tersedia di [`docs/extraction_log_*.md`](docs/). Secara total, peta interaktif memuat 5.577 fitur.

Step 1 sampai 6 (extraction dan integrasi peta gabungan 8 region) telah selesai. Step 7 dan seterusnya berada di roadmap.

## Preview

Buka [`web/preview_indonesia.html`](web/preview_indonesia.html) di browser. Peta ini menampilkan 8 region sekaligus dengan fasilitas filter, search, dan detail panel. File bersifat self-contained sehingga tidak memerlukan server; seluruh data ter-bundle pada `web/data_<region>.js`.

Preview per region (legacy, tetap dapat dipakai untuk eksplorasi terpisah): [`preview_jamali.html`](web/preview_jamali.html) dan [`preview_sumatra.html`](web/preview_sumatra.html).

Atau lihat live demo (akan ditambahkan setelah deploy ke GitHub Pages).

## Sumber data

Semua data berasal dari sumber publik:

- **RUPTL PLN 2025–2034** (Keputusan Menteri ESDM 188.K/TL.03/MEM.L/2025): daftar gardu induk dan agregat pembangkit per provinsi. [Source: PLN](https://web.pln.co.id/).
- **OpenStreetMap** (© OSM contributors, ODbL): koordinat infrastruktur, daftar pembangkit, dan jaringan transmisi. Diakses melalui Overpass API.
- **Statistik PLN 2024 & 2025**, **Annual Report PLN 2024**, **Handbook of Energy & Economic Statistics of Indonesia 2024 (ESDM)**: validasi agregat dan kontekstualisasi.
- **Carto Basemaps** (© CARTO): peta dasar visualisasi.

Daftar lengkap dan URL download di [`data/raw/sources/README.md`](data/raw/sources/README.md).

## Struktur repo

```
indonesia-power-map/
├── README.md                          # File ini
├── LICENSE                            # Apache 2.0 (untuk kode)
├── LICENSE-DATA                       # CC-BY-SA 4.0 (untuk data & dokumen)
├── NOTICE                             # Attribution wajib
├── CITATION.cff                       # Cara mengutip proyek ini
├── docs/
│   ├── concept/                       # Dokumen konsep awal proyek
│   ├── design_decisions.md            # Keputusan visual & UX
│   ├── naming_conventions.md          # Konvensi PLT-X, GITET, dll
│   └── extraction_log_*.md            # Log ekstraksi per region × per layer
├── scripts/                           # Pipeline ekstraksi & transformasi
│   ├── substation_table_parser.py     # Shared parser RUPTL Lampiran A–C
│   ├── extract_{region}_substations.py    # 6 file: jamali/sumatra/kalimantan/
│   ├── extract_{region}_generators.py     #         sulawesi/maluku_papua/
│   ├── extract_{region}_transmission.py   #         nusa_tenggara
│   └── bundle_web_data.py             # GeoJSON → JS bundle untuk web/
├── data/
│   ├── raw/sources/                   # Sumber PDF (TIDAK di-commit, lihat README)
│   ├── geojson/                       # Data OSM mentah (Overpass exports)
│   ├── processed/                     # Output: CSV + GeoJSON master per region × layer
│   └── overrides/                     # Manual overrides koordinat + nama plant
│       ├── substation_overrides.csv         # 49 entries (GI step-up, naming mismatch)
│       └── generator_name_overrides.csv     # 37 entries (Mandarin/English → Indonesia)
└── web/                               # Preview HTML interaktif
    ├── preview_indonesia.html         # Peta gabungan 8 region (entry point utama)
    ├── preview_{region}.html          # Preview per-region (legacy)
    └── data_{region}.js               # Bundle GeoJSON per region
```

## Cara reproduce

```bash
# 1. Clone repo
git clone https://github.com/sandro71626/indonesia-power-map.git
cd indonesia-power-map

# 2. Download sumber PDF (lihat data/raw/sources/README.md untuk URL)
#    Letakkan di data/raw/sources/

# 3. Re-run pipeline ekstraksi (opsional, output sudah ada di data/processed/).
#    Tiap region punya 3 extractor (substations + generators + transmission):
for region in jamali sumatra kalimantan sulawesi maluku_papua nusa_tenggara; do
  python3 scripts/extract_${region}_substations.py
  python3 scripts/extract_${region}_generators.py
  python3 scripts/extract_${region}_transmission.py
done

# 4. Bundle ulang data web (kalau ada perubahan CSV/GeoJSON):
for r in jamali sumatra kalimantan sulawesi maluku papua ntb ntt; do
  python3 scripts/bundle_web_data.py $r
done

# 5. Buka peta gabungan
open web/preview_indonesia.html   # macOS
xdg-open web/preview_indonesia.html   # Linux
```

Dependency: Python 3.10+, `pdftotext` (poppler-utils). Tidak butuh package eksternal.

## Roadmap

Data extraction + integration peta interaktif (Step 1–6) sudah selesai. Selanjutnya:

- **Step 1** Static Visual Knowledge Map (JAMALI): ✅ done
- **Step 2** Ekstensi ke Sumatra dan Interactive Grid Explorer (filter, search, popup detail): ✅ done
- **Step 3** Ekstensi ke Kalimantan dan integrasi peta gabungan: ✅ done
- **Step 4** Ekstensi ke Sulawesi: ✅ done
- **Step 5** Ekstensi ke Maluku dan Papua: ✅ done
- **Step 6** Ekstensi ke Nusa Tenggara (NTB dan NTT) serta integrasi 8 region: ✅ done
- **Step 7** System Intelligence Layer (generation mix per region, load center indicator, konteks supply-demand): 🔄 planned
- **Step 8** Temporal Expansion (existing menuju 2025, 2030, dan 2035 berdasar RUPTL Tabel x.5 dan seterusnya): planned
- **Step 9** Approximate Power Flow (DC PF educational simulation): planned
- **Step 10** Deployment publik ke GitHub Pages atau Cloudflare Pages, dengan automated OSM refresh: planned

Lihat [`docs/concept/`](docs/concept/) untuk detail roadmap.

## Disclaimer

- Peta ini **bukan** alat operasi sistem tenaga, **bukan** dashboard dispatch realtime, dan **tidak** merepresentasikan informasi rahasia atau internal institusi mana pun.
- Data koordinat berasal dari OpenStreetMap dan **perlu verifikasi independen** sebelum dipakai untuk keputusan operasional, teknis, atau hukum.
- Untuk edukasi, eksplorasi, dan analisis umum.

## Metodologi Singkat

Data pembangkit, gardu induk, dan transmisi dikompilasi dari kombinasi dokumen publik (RUPTL PLN 2025–2034) dan OpenStreetMap. Pipeline pemrosesan mencakup ekstraksi otomatis, pencocokan nama dengan fuzzy match (threshold 0,85), validasi silang antar sumber, serta override manual untuk meningkatkan akurasi koordinat dan representasi sistem. Detail lengkap per region terdokumentasi di [`docs/extraction_log_*.md`](docs/).

Beberapa nama pembangkit non-Indonesia pada OSM (nama Mandarin di kompleks Weda Bay Industrial Park, nama deskriptif berbahasa Inggris di smelter Morowali/Konawe/Bitung, serta sejumlah pembangkit captive industrial di JAMALI, Sumatra, Kalimantan, dan NTB) telah dinormalisasi ke nama Indonesia melalui [`data/overrides/generator_name_overrides.csv`](data/overrides/generator_name_overrides.csv). Nama asli dari OSM tetap dipertahankan pada kolom `osm_name` untuk keperluan audit trail.

## Author

Diinisiasi dan dikembangkan oleh **Sandro Agassi Sitompul, Ph.D.** (2026) sebagai inisiatif teknis independen untuk membantu pemahaman publik terhadap sistem ketenagalistrikan Indonesia.

Daftar lengkap kontributor (apabila ada) dapat dilihat melalui history commit Git.

## Feedback & Kontak

Masukan, koreksi data, maupun saran pengembangan sangat diterima.

- **Email:** [contact@indonesiapowermap.com](mailto:contact@indonesiapowermap.com)
- **LinkedIn:** [linkedin.com/in/sandro-sitompul-a7a490107](https://www.linkedin.com/in/sandro-sitompul-a7a490107)
- **GitHub:** [github.com/sandro71626/indonesia-power-map](https://github.com/sandro71626/indonesia-power-map)

## Sitasi

Apabila data atau analisis dari repositori ini digunakan dalam publikasi atau laporan, mohon disitasi sebagai berikut:

```
Sitompul, S. A. (2026). Peta Ketenagalistrikan Indonesia (Indonesia Power Map).
Version v1.0.0-beta. https://github.com/sandro71626/indonesia-power-map
```

Format BibTeX dan format sitasi lain dapat dihasilkan otomatis melalui tombol "Cite this repository" pada sidebar GitHub (didukung oleh [`CITATION.cff`](CITATION.cff)).

## Lisensi

- **Kode** (`scripts/`, `web/*.html`, `web/*.js`) memakai **Apache License 2.0**, bebas dipakai komersial maupun non-komersial dengan atribusi. Lihat [`LICENSE`](LICENSE).
- **Data dan dokumen** (`data/processed/`, `docs/`, dan file Markdown) memakai **CC-BY-SA 4.0**, bebas dipakai dan dimodifikasi dengan atribusi serta share-alike. Lihat [`LICENSE-DATA`](LICENSE-DATA).
- **Data turunan** dari OpenStreetMap tunduk juga pada **ODbL** (Open Database License).
- **Data dari RUPTL/PLN/ESDM** adalah dokumen publik; redistribusi melalui repo ini hanya berbentuk turunan/agregat sesuai fair use untuk tujuan edukasi.

## Kontribusi

Project ini terbuka untuk kontribusi. Sebelum membuka pull request:
1. Buka issue dulu untuk diskusi.
2. Pertahankan prinsip **public-data only**, yaitu tidak menerima data dari sumber rahasia atau internal.
3. Setiap data baru harus punya `source_id` yang terdokumentasi.
4. Atribusi original kontributor wajib dipertahankan.
