# Ekstraksi Gardu Induk Nusa Tenggara — Log

**Tanggal:** 2026-05-27 — extraction perdana (Step 6 substations)
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran C, Tabel C11–C12), OSM (Overpass API)
**Output:**
- `data/processed/substation_master_ntb.csv` + `substations_ntb.geojson`
- `data/processed/substation_master_ntt.csv` + `substations_ntt.geojson`

**Skrip:** `scripts/extract_nusa_tenggara_substations.py`
**Overrides:** `data/overrides/substation_overrides.csv` (3 entries Nusa Tenggara, shared dgn region lain)
**Threshold matching identik:** 0.85 absolute, override prioritas pertama, fuzzy SequenceMatcher di bawahnya.

## Ringkasan

| Provinsi | Tabel | Region | RUPTL | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------|--------|------:|-------------:|---------:|----------:|
| Nusa Tenggara Barat | C11 | ntb | 26 | 20 | 1 |  5 |
| Nusa Tenggara Timur | C12 | ntt | 19 | 14 | 2 |  3 |
| **Total** | | | **45** | **34** | **3** | **8** |

Match rate: **82,2%** (37 / 45). **Di bawah target standar 85% tipis** — dibahas di bagian UNMATCHED di bawah.

Breakdown per region:

| Region | Provinsi | Matched | Total | Rate |
|--------|----------|--------:|------:|-----:|
| ntb    | NTB      | 21 | 26 | 80,8% |
| ntt    | NTT      | 16 | 19 | 84,2% |

## Catatan ekstraksi

### Urutan tabel diverifikasi

`scripts/_probe_c_provinces.py` mengonfirmasi C11=NTB (Ampenan, Jeranjang, Sengkol, Mantang, Selong, Kuta — semua Lombok area) dan C12=NTT (Panaf, Tenau, Bolok, Maulafa, Naibonat, Nonohonis — semua Kupang/Timor). Tidak ada swap.

### Tabel pendek, parser auto-stop di heading berikutnya

C11.4 mulai p1153 dan heading C11.5 ("Realisasi Fisik Sistem Distribusi") muncul di p1153 juga — tabel C11.4 hanya ~1 halaman. Sama untuk C12.4 di p1170, C12.5 di p1171. Shared parser (`substation_table_parser.py`) auto-stop di heading C{n}.5 berikutnya, jadi page range boleh longgar (`1153-1169` untuk C11, `1170-1172` untuk C12) tanpa over-extraction.

### Region & sistem

Sama pola Maluku/Papua: 2 region terpisah karena NTB & NTT tidak interkoneksi total. Field `system` makro per provinsi:

  - `ntb` (Nusa Tenggara Barat) → ID prefix `GI-NTB-XXXX`, system `NTB`
  - `ntt` (Nusa Tenggara Timur) → ID prefix `GI-NTT-XXXX`, system `NTT`

Catatan operasional: **NTB punya interkoneksi parsial Lombok-Sumbawa** (kabel laut 150 kV Selat Alas — Sengkol/Mantang ↔ Empang). Bima/Sumbawa Timur masih semi-isolated. **NTT** kumpulan sistem pulau yang tidak interkoneksi (Sistem Flores, Sumba, Timor, Alor, Lembata). Untuk MVP cukup label makro; sub-system per-pulau bisa ditambah di iterasi berikutnya.

### Bbox

Selat Lombok (lon ~115.7) jadi pemisah dgn Bali. NTB `lon_min 115.75` exclude semua plant Bali (Celukan Bawang lon 114.7, Pemaron lon 115.1) tapi include Lombok Barat. NTT `lon_min 119.10` overlap minimal dengan Bima/NTB Timur — Labuan Bajo (Flores Barat, lon 119.88) tetap masuk NTT.

## 3 override yang di-apply

| RUPTL name | Provinsi | Sumber koordinat | Catatan |
|------------|----------|------------------|---------|
| Sumbawa | NTB | OSM substation Gardu Induk Seketeng (way/707531067) | Seketeng adalah lokasi GI di kota Sumbawa Besar |
| Ruteng | NTT | OSM substation Gardu Induk Bahong (way/937059869) | Bahong adalah sub-area Ruteng/Cancar (Manggarai); OSM pakai nama desa, RUPTL pakai nama kota |
| PLTMG Flores / Rangko | NTT | OSM plant PLTMG Flores centroid (way/937059866) | GI step-up ko-lokasi dengan PLTMG di Rangko (utara Labuan Bajo) |

## 8 GI yang masih UNMATCHED

Sebagian besar GI distribusi atau town feeder di sub-pulau / kota rural yang **belum ter-tag di OSM substations dataset**. Tidak ada padanan plant ko-lokasi yang cukup confident untuk override.

### NTB (5)

| RUPTL name | Catatan |
|------------|---------|
| Selong | Ibu kota Lombok Timur. OSM punya GI Paokmotong (Masbagik) & GI Pringgabaya (Pringgabaya) di Lombok Timur, tapi tidak ada GI Selong eksplisit. Selong (kota) lat ~-8.66, lon 116.55 — area itu belum ter-tag di OSM substations. |
| Labuhan | Kemungkinan **Labuhan Badas** (port Sumbawa Besar) atau **Labuhan Lombok** (port Lombok Timur). Tidak ada padanan di OSM untuk salah satu. |
| Labuhan IBT | Inter-Bus Transformer di lokasi Labuhan yang sama. UNMATCHED bersama dgn Labuhan. |
| Bonto | Desa di Bima/Madapangga. Tidak ada GI Bonto di OSM; kandidat unnamed terdekat (way/151888915) di lat -8.42, lon 118.60 lebih dekat ke Bolo/Donggo — confidence rendah. |
| PLTU Sumbawa | Ambigu — bisa PLTU Lab. Badas, PLTU Sumbawa Barat (Taliwang, way/707043779), atau Komplek PLTMG Sumbawa (way/937059862). OSM tidak punya kandidat PLTU yang clearly named "PLTU Sumbawa". Tidak di-override (konservatif). |

### NTT (3)

| RUPTL name | Catatan |
|------------|---------|
| Panaf | RUPTL No 1 NTT, 150/20 kV 1 trafo 30 MVA. Nama tidak biasa — kemungkinan singkatan / abbreviation lokal. Tidak ada padanan di OSM. |
| Aesesa | Mbay (Nagekeo, Flores). Tidak ada GI Aesesa di OSM. Mungkin GI baru pasca-2024 yang belum ter-tag. |
| Borong | Manggarai Timur, Flores. Ada hydro plant unnamed (way/845393015) di area Borong, tapi itu PLTM (Wae Garit/Kondoratu) — beda lokasi/peran dari GI distribusi. Tidak di-override (konservatif). |

## Catatan tentang target 85%

Region sebelumnya menargetkan **>= 85% match rate** sebagai baseline kualitas. NTB/NTT mencapai **82,2%** — sedikit di bawah target karena:

1. **OSM coverage substations NTB/NTT tipis** untuk kota rural — Lombok Timur (Selong area), Sumbawa pesisir (Labuhan), Bima (Bonto), Flores (Aesesa, Borong) belum ter-tag dengan rapat.
2. **GI baru pasca-2024** kemungkinan masuk RUPTL 2025-2034 tapi belum ada di OSM Overpass snapshot — tidak bisa di-match.
3. **Override konservatif** — untuk 5 UNMATCHED yang punya kandidat dengan confidence menengah-rendah, lebih baik tetap UNMATCHED (transparan) daripada false-positive koordinat keliru.

Diterima sebagai trade-off: **akurasi koordinat lebih penting dari rate**. 8 UNMATCHED ter-dokumentasi jelas; sisanya 37 GI punya koord ter-verifikasi. Iterasi berikutnya bisa menaikkan rate via Overpass direct query (cari OSM unnamed substation di koord spesifik) atau PLN Annual Report.

## Struktur kolom CSV

Identik dengan region lain. Highlights:

- `id` — prefix `GI-NTB-XXXX` / `GI-NTT-XXXX`
- `system` — `NTB` / `NTT`
- `match_source` — `osm_fuzzy` / `override:osm_substation` / `override:osm_plant`
- `review_flag` — `UNMATCHED` atau kosong
- `source_table` — `Tabel C11.4` / `Tabel C12.4`

CSV memuat seluruh baris RUPTL (termasuk UNMATCHED tanpa koordinat); GeoJSON hanya memuat fitur yang ter-match.

## Limitasi & batasan

- **Hanya GI eksisting** (Tabel C11.4 & C12.4), tidak termasuk yang masih tahap rencana.
- **Coverage OSM** Nusa Tenggara tipis untuk sub-pulau (Sumbawa Timur, Bima rural, Flores barat-tengah, sub-pulau NTT seperti Alor/Adonara/Lembata).
- **Naming convention** PLN vs OSM kadang beda — RUPTL pakai nama kota, OSM pakai nama desa/sub-area (Ruteng vs Bahong, Sumbawa vs Seketeng). Override-able tapi perlu riset case-by-case.
- **Sub-sistem operasional** (Sistem Lombok, Sistem Sumbawa, Sistem Flores, Sistem Timor) tidak di-label per-baris; cukup makro `NTB`/`NTT` untuk MVP.

## Sources

- [substation_master_ntb.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/substation_master_ntb.csv)
- [substation_master_ntt.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/substation_master_ntt.csv)
- [extract_nusa_tenggara_substations.py](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/scripts/extract_nusa_tenggara_substations.py)
