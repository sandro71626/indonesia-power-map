# Peta Ketenagalistrikan Indonesia

> Indonesia Power Map — peta digital sistem tenaga listrik Indonesia berbasis data publik, untuk edukasi, eksplorasi, dan analisis umum.

**Status:** Alpha (Step 1, cakupan Jawa-Madura-Bali) · **Versi:** v0.1 · **Diinisiasi:** 2026

---

## Visi

Membangun peta digital ketenagalistrikan Indonesia yang mengubah informasi teknis tersebar — terutama dari RUPTL, laporan PLN, dan sumber publik lain — menjadi visualisasi sistem tenaga yang mudah dipahami, dieksplorasi, dan dikembangkan.

Targetnya bukan dashboard operasi atau SCADA publik, melainkan **"knowledge map" sistem kelistrikan Indonesia** yang bisa dipakai mahasiswa, peneliti, analis kebijakan, media, dan publik teknis.

Konsep lengkap ada di [`docs/concept/`](docs/concept/).

## Status & cakupan saat ini

| Sistem | Pembangkit | Gardu Induk | Transmisi |
|--------|-----------:|------------:|----------:|
| Jamali (Jawa-Madura-Bali) | 196 | 520 | 2.358 garis |
| Sumatera | _belum_ | _belum_ | _belum_ |
| Kalimantan | _belum_ | _belum_ | _belum_ |
| Sulawesi | _belum_ | _belum_ | _belum_ |
| Maluku-Papua-Nusra | _belum_ | _belum_ | _belum_ |

Step 1 (peta visual statis) untuk Jamali sudah complete. Step 2 (interactive explorer) dan ekspansi ke sistem lain di roadmap.

## Preview

Buka [`web/preview_jamali.html`](web/preview_jamali.html) di browser. Self-contained, tidak butuh server — semua data ter-inline.

Atau lihat live demo (akan ditambahkan setelah deploy ke GitHub Pages).

## Sumber data

Semua data berasal dari sumber publik:

- **RUPTL PLN 2025–2034** (Keputusan Menteri ESDM 188.K/TL.03/MEM.L/2025) — daftar gardu induk + agregat pembangkit per provinsi. [Source: PLN](https://web.pln.co.id/).
- **OpenStreetMap** (© OSM contributors, ODbL) — koordinat infrastruktur, daftar pembangkit, jaringan transmisi. Diakses via Overpass API.
- **Statistik PLN 2024 & 2025**, **Annual Report PLN 2024**, **Handbook of Energy & Economic Statistics of Indonesia 2024 (ESDM)** — validasi agregat dan kontekstualisasi.
- **Carto Basemaps** (© CARTO) — peta dasar visualisasi.

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
│   └── extraction_log_*.md            # Log per pipeline ekstraksi
├── scripts/                           # Pipeline ekstraksi & transformasi
│   ├── extract_jamali_substations.py
│   ├── extract_jamali_generators.py
│   └── extract_jamali_transmission.py
├── data/
│   ├── raw/sources/                   # Sumber PDF (TIDAK di-commit, lihat README)
│   ├── geojson/                       # Data OSM mentah (Overpass exports)
│   └── processed/                     # Output: CSV + GeoJSON master
└── web/                               # Preview HTML interaktif
    └── preview_jamali.html
```

## Cara reproduce

```bash
# 1. Clone repo
git clone https://github.com/<username>/indonesia-power-map.git
cd indonesia-power-map

# 2. Download sumber PDF (lihat data/raw/sources/README.md untuk URL)
#    Letakkan di data/raw/sources/

# 3. Re-run pipeline ekstraksi (opsional, output sudah ada di data/processed/)
python3 scripts/extract_jamali_substations.py
python3 scripts/extract_jamali_generators.py
python3 scripts/extract_jamali_transmission.py

# 4. Buka preview
open web/preview_jamali.html   # macOS
xdg-open web/preview_jamali.html   # Linux
```

Dependency: Python 3.10+, `pdftotext` (poppler-utils). Tidak butuh package eksternal.

## Roadmap

- **Step 1** — Static Visual Knowledge Map: ✅ Jamali done
- **Step 2** — Interactive Grid Explorer (filter, search, popup detail): 🔄 Next
- **Step 3** — System Intelligence Layer (generation mix, load center, supply-demand): planned
- **Step 4** — Temporal Expansion (existing → 2025 → 2030 → 2035): planned
- **Step 5** — Approximate Power Flow (DC PF educational simulation): planned

Lihat [`docs/concept/`](docs/concept/) untuk detail roadmap.

## Disclaimer

- Peta ini **bukan** alat operasi sistem tenaga, **bukan** dashboard dispatch realtime, dan **tidak** merepresentasikan informasi rahasia atau internal institusi mana pun.
- Data koordinat berasal dari OpenStreetMap dan **perlu verifikasi independen** sebelum dipakai untuk keputusan operasional, teknis, atau hukum.
- Untuk edukasi, eksplorasi, dan analisis umum.

## Author

Diinisiasi dan dikembangkan oleh **Sandro Agassi** (2026). Kontak: `sandroagassi71@gmail.com`.

Untuk daftar lengkap kontributor (kalau ada), lihat history commit Git.

## Sitasi

Kalau lo pakai data atau analisis dari repo ini di publikasi/laporan, mohon cite:

```
Agassi, S. (2026). Peta Ketenagalistrikan Indonesia (Indonesia Power Map).
Version v0.1. https://github.com/<username>/indonesia-power-map
```

Format BibTeX dan format lain otomatis di-generate via tombol "Cite this repository" di sidebar GitHub (didukung oleh [`CITATION.cff`](CITATION.cff)).

## Lisensi

- **Kode** (`scripts/`, `web/*.html`, `web/*.js`): **Apache License 2.0** — bebas dipakai komersial maupun non-komersial dengan atribusi. Lihat [`LICENSE`](LICENSE).
- **Data & dokumen** (`data/processed/`, `docs/`, file Markdown): **CC-BY-SA 4.0** — bebas dipakai dan dimodifikasi dengan atribusi + share-alike. Lihat [`LICENSE-DATA`](LICENSE-DATA).
- **Data turunan** dari OpenStreetMap tunduk juga pada **ODbL** (Open Database License).
- **Data dari RUPTL/PLN/ESDM** adalah dokumen publik; redistribusi melalui repo ini hanya berbentuk turunan/agregat sesuai fair use untuk tujuan edukasi.

## Kontribusi

Project ini terbuka untuk kontribusi. Sebelum membuka pull request:
1. Buka issue dulu untuk diskusi.
2. Pertahankan prinsip **public-data only** — tidak menerima data dari sumber rahasia/internal.
3. Setiap data baru harus punya `source_id` yang terdokumentasi.
4. Atribusi original kontributor wajib dipertahankan.
