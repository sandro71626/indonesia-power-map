# Ekstraksi Pembangkit Maluku & Papua — Log

**Tanggal:** 2026-05-27 — extraction perdana (Step 5 generators)
**Sumber utama:** OSM `power=plant` (Overpass) — sumber otoritatif, koord presisi
**Output:**
- `data/processed/generator_master_maluku.csv` + `generators_maluku.geojson`
- `data/processed/generator_master_papua.csv` + `generators_papua.geojson`

**Skrip:** `scripts/extract_maluku_papua_generators.py`
**Override:** TIDAK ADA (generators pakai OSM langsung; tidak ada fuzzy matching atau override koordinat, konsisten dengan pola Sulawesi/Kalimantan/Sumatra/JAMALI).

## Ringkasan

| Region | Provinsi | Plant | Plant w/ cap | Total MW (w/ cap) |
|--------|----------|------:|-------------:|------------------:|
| Maluku | Maluku Utara | 12 | 4 |  69,60 |
| Maluku | Maluku       |  7 | 4 |  50,18 |
| Papua  | Papua Barat  |  9 | 5 |  79,50 |
| Papua  | Papua        |  7 | 6 | 399,00 |
| **Total** | | **35** | **19** | **598,27** |

Per system:

| System | Plant | Total MW (yang ada cap) |
|--------|------:|------------------------:|
| Maluku | 19 | 119,77 |
| Papua  | 16 | 478,50 |

Per tipe (yang punya kapasitas):

| Type | Maluku (n / MW) | Papua (n / MW) |
|------|-----------------:|----------------:|
| PLTU  | 2 / 44,0 | 2 / 279,0 |
| PLTMG | 2 / 50,0 | 5 / 170,0 |
| PLTD  | 1 / 25,0 | 1 / 7,5 |
| PLTA  | 0 / 0    | 1 / 20,0 |
| PLTS  | 3 / 0,77 | 2 / 2,0 |

## Catatan ekstraksi

### Region & sistem listrik

Maluku & Papua **tidak punya grid interkoneksi** — keduanya kumpulan sistem pulau yang terisolasi. Field `system` cuma dua makro-grup (`Maluku` / `Papua`), konsisten dengan substations Maluku/Papua. Provinsi tetap jadi field tersendiri.

  - `Maluku`  = Maluku + Maluku Utara → ID prefix `GEN-MLK-XXXX`
  - `Papua`   = Papua + Papua Barat   → ID prefix `GEN-PAP-XXXX`

### Bbox revisi vs substations

Substations Maluku/Papua memakai bbox longgar (`Maluku Utara lon_min 123.90`) karena matching pakai nama RUPTL — plant Sulut tidak akan ter-match dengan nama GI Maluku. **Generators tidak punya filter nama**, jadi bbox longgar akan **bocor**: probe awal menemukan PLTP Lahendong I & II / III & IV (Sulawesi Utara, lon ~124.83) ter-include ke Maluku Utara.

Solusi (bbox lebih ketat, lihat `PROVINCES` di script):

| Provinsi | lon_min | Alasan |
|----------|---------|--------|
| Maluku Utara | **125.30** (vs 123.90) | Exclude Lahendong (lon 124.83) & plant Sulut lainnya. Sula Islands tepi paling barat (lon ~125.3-126.1) tetap masuk. |
| Maluku       | **125.50** (vs 125.00) | Exclude potensi plant Sulteng timur (Banggai Islands lon ~123-125). |
| Papua Barat  | 129.00 (sama) | Tidak overlap dgn provinsi non-Maluku/Papua. |
| Papua        | 134.00 (sama) | Tidak overlap dgn provinsi non-Maluku/Papua. |

Centroid tiebreak ditangani via `assign_province()` — kalau titik masuk >1 bbox (overlap Maluku ↔ Papua Barat di lat -4.5..-2.65 / lon 129-135; Papua ↔ Papua Barat di lat -4.5..0.7 / lon 134-135.2), pilih bbox dengan centroid provinsi terdekat (Maluku=Ambon, Papua Barat=Bird's Head, Papua=tengah Papua timur).

### Cluster dedup dua-pass

Dataset OSM Maluku/Papua punya pola tagging cluster yang menggandakan plant fisik tunggal. Contoh paling jelas: **PLTD Fakfak** ter-tag **6x** di OSM (2 bernama "PLTD Fakfak" + 4 unnamed) dengan koordinat dalam radius 30 m — semua sebenarnya 1 kompleks PLTD.

Round-4-desimal (~11 m) yang dipakai region lain TIDAK menangkap cluster ini karena koord aslinya beda di desimal ke-5+. Solusi: **second-pass cluster dedup** (round-3-desimal, ~111 m) dengan aturan:

- Cluster 1 entri → keep.
- Cluster >1 entri & punya entri bernama + entri (unnamed) → **drop (unnamed)**.
- Cluster >1 entri dengan nama identik → keep yang punya capacity, fallback ke entri pertama.
- Cluster >1 entri dengan nama-nama BERBEDA (mis. Weda Bay 1-4 vs 5-8 vs 9-11) → keep semua (unit terpisah valid).

Hasil pass kedua: **5 entri ter-drop** (4 unnamed PLTD Fakfak + 1 dup "PLTD Fakfak"). NO_NAME total: 7 → 3.

### Weda Bay cluster (Maluku Utara) — 4 unit terpisah, KEPT

Weda Bay Industrial Park (Halmahera Tengah, smelter nickel Tsingshan-IWIP) punya pembangkit captive PLTU multi-unit. OSM ter-tag dengan nama Mandarin; sudah di-override ke nama Indonesia via `data/overrides/generator_name_overrides.csv` (2026-05-27). Original OSM name di-preserve di field `osm_name`.

| ID | Display name (override) | OSM original | Koord | Type |
|----|-------------------------|--------------|-------|------|
| GEN-MLK-0013 | **PLTU Weda Bay** | PLTU Weda Bay Power Plant（韦达贝燃煤发电厂） | 0.477, 128.001 | PLTU |
| GEN-MLK-0016 | **PLTU Weda Bay Unit 9-11** | 电厂(9-11) | 0.476, 128.008 | Unknown (source kosong) |
| GEN-MLK-0017 | **PLTU Weda Bay Unit 1-4** | 电厂（1-4） | 0.476, 127.999 | PLTU |
| GEN-MLK-0018 | **PLTU Weda Bay Unit 5-8** | 电厂（5-8） | 0.476, 127.995 | PLTU |
| GEN-MLK-0019 | **Gardu Induk Weda Bay Unit 3** | 3号变电站 | 0.482, 127.989 | Unknown — **lihat catatan** |

Cluster 3-desimal: 4 entri (`PLTU Weda Bay` + 3 unit) berada di koord 3-desimal BERBEDA satu sama lain → tidak ter-merge. Memang unit terpisah (1-4, 5-8, 9-11, dan PLTU induk yang ter-tag overall plant boundary).

**GEN-MLK-0019 (OSM "3号变电站" = "Substation 3")** sebenarnya substation, bukan plant — OSM mis-tagged `power=plant`. Display name "Gardu Induk Weda Bay Unit 3" mencerminkan fungsi sebenarnya. Bisa di-skip dari output plant di iterasi berikutnya via `PROVINCE_OVERRIDE` value `None`.

### Name overrides mechanism (5 entries Maluku)

Plant non-Indonesia di OSM (Mandarin/English deskriptif) di-normalisasi ke nama Indonesia via shared CSV `data/overrides/generator_name_overrides.csv`. Mekanisme:

1. Extractor load mapping `osm_id → override_name`.
2. Saat write row: kalau `osm_id` ada di overrides, set `name = override_name`; original disimpan di kolom baru `osm_name`.
3. CSV master sekarang punya 13 kolom (sebelumnya 12) — tambah `osm_name` setelah `name`.

5 entries Maluku Utara semua di kompleks Weda Bay (di-list di tabel di atas). Mekanisme yang sama dipakai oleh `extract_sulawesi_generators.py` untuk 6 plant English deskriptif di Morowali-Konawe-Bitung area.

### Catatan per provinsi

**Maluku Utara (12 plant):** Backbone Ternate-Tidore (PLTU Tidore, PLTMG Ternate, PLTD Kayu Merah) + Weda Bay cluster (5 entri termasuk "3号变电站") + PLN Desa Waci (Halmahera) + 2 PLTS Morotai unnamed + PLTS Morotai bernama. Total 69,6 MW yang punya kapasitas (Weda Bay = `yes` di OSM, tidak terbaca sebagai angka).

**Maluku (7 plant):** PLTU Waai (Ambon 30 MW), PLTMG Seram, PLTMG Dullah (Kei Kecil), PLTS Pulau Tiga, PLTS Tahalupu, plus 2 entri PLN-tagged "MIN 4 Maluku Tengah" + "PLN Tehoru" tanpa source (kemungkinan PLTD distribusi).

**Papua Barat (9 plant):** Bird's Head — PLTD Sorong, PLTMG Sorong (50 MW), PLTD Fakfak (post-dedup), PLTMG MPP Manokwari (20 MW), PLTD Sanggeng (Manokwari 7,5 MW), PLTS Arfai + Reremi (Manokwari 1 MW masing-masing), PLTS Werua + Sara (Fakfak area selatan, ~lat -3,5). Total 79,5 MW.

**Papua (7 plant):** Plant terbesar di region — PLTU Amamapare (Freeport Timika **255 MW** = single largest), PLTMG MPP Jayapura 50 MW, PLTMG Jayapura 40 MW, PLTU Holtekamp 24 MW, PLTA Orya Genyem 20 MW, PLTMG Timika 10 MW, 1 unnamed di pegunungan tengah Papua (lat -4,11 lon 138,93). Total 399 MW dominan dari Amamapare.

## Review flags

| Flag | Count | Catatan |
|------|------:|---------|
| NO_NAME     | 3 | 2 PLTS Morotai unnamed + 1 unnamed Papua tengah (lat -4.11, lon 138.93). Valid OSM data minimal. |
| NO_CAPACITY | 16 | OSM Maluku/Papua banyak plant tanpa tag `plant:output:electricity` (Weda Bay = `yes`, PLN distribusi units, dll). |
| NO_TYPE     | 6 | Source kosong di OSM → derive_type return `Unknown` (mis. "PLN Desa Waci", "MIN 4 Maluku Tengah", "3号变电站"). |

Untuk MVP peta, review_flag dipakai untuk styling (mis. titik abu-abu untuk Unknown). Cleanup OSM-side bisa dilakukan terpisah via OSM editor.

## Total Mappable Capacity (preliminary)

Indikator kasar (hanya dari plant dengan capacity ter-parse):

- **Maluku region:** 19 plant, ~120 MW. **Catatan: Weda Bay PLTU (3-4 unit × ~380 MW) tidak terhitung karena cap=`yes` di OSM.** Kalau dilengkapi referensi non-OSM (RUPTL Lampiran D atau press release IWIP), kapasitas riil Maluku Utara bisa naik signifikan ke ~1.500+ MW.
- **Papua region:** 16 plant, ~478 MW (dominan Amamapare 255 MW Freeport, plus cluster Jayapura ~115 MW).

Total Maluku/Papua riil di RUPTL kemungkinan lebih besar — untuk iterasi berikutnya, cross-check ke RUPTL Lampiran D (D7-D10) atau PLN Annual Report Maluku/Papua.

## Limitasi & batasan

- **OSM-only.** Tidak ada cross-check ke RUPTL Lampiran D dalam extraction ini (beda dengan substations yang cross-check ke Lampiran C). Risiko: plant baru pasca-2024 yang sudah di RUPTL tapi belum di-tag OSM akan terlewat.
- **Capacity coverage 54%** (19/35 plant punya capacity). Untuk Weda Bay (cap=`yes`) sumber referensi non-OSM diperlukan.
- **3号变电站** ter-include sebagai plant karena OSM mis-tag. Tidak di-skip otomatis; tag manual di iterasi berikutnya.
- **Sub-system label sederhana** (`Maluku` / `Papua`) — tidak detail per-pulau (mis. Sistem Ambon, Sistem Ternate, Sistem Jayapura). Cukup untuk MVP peta makro.
- **Papua Barat Daya** (provinsi pemekaran 2022) belum dipisahkan; OSM data Bird's Head masih kategoris Papua Barat. RUPTL 2025 juga belum split → konsisten.

## Reusability untuk Nusa Tenggara (Step 6 generators)

Pola sama dapat dipakai untuk NTB + NTT:

1. Probe `indonesia_plants.geojson` untuk plant di bbox NTB (lat -10..-8, lon 115.7..120) dan NTT (lat -11..-8, lon 119..125).
2. Copy `extract_maluku_papua_generators.py`, ganti PROVINCES + ID prefix (`GEN-NTB`, `GEN-NTT`).
3. Cluster dedup 3-desimal sudah generic; biarkan apa adanya.
4. Run, sanity-check, dokumentasikan.

Sub-sistem NTT mirip Maluku/Papua — kumpulan pulau terisolasi (Sistem Flores, Sistem Sumba, Sistem Timor); NTB punya interkoneksi Sumbawa-Lombok parsial. Tetap pakai dua makro-grup (`NTB` / `NTT`) atau pisah per-pulau kalau granularitas dibutuhkan.

## Sources

- [generator_master_maluku.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/generator_master_maluku.csv)
- [generator_master_papua.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/generator_master_papua.csv)
- [extract_maluku_papua_generators.py](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/scripts/extract_maluku_papua_generators.py)
