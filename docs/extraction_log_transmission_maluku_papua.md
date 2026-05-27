# Ekstraksi Transmisi Maluku & Papua — Log

**Tanggal:** 2026-05-27 — extraction perdana (Step 5 transmission)
**Sumber utama:** OSM `power=line` (Overpass) — sumber otoritatif, geometri LineString presisi
**Output:**
- `data/processed/transmission_master_maluku.csv` + `transmission_maluku.geojson`
- `data/processed/transmission_master_papua.csv` + `transmission_papua.geojson`

**Skrip:** `scripts/extract_maluku_papua_transmission.py`
**Override:** TIDAK ADA (transmission pakai OSM langsung, konsisten dengan pola Sulawesi/Kalimantan/Sumatra/JAMALI).
**Filter tegangan:** >= 70 kV (exclude distribusi <70 kV).

## Ringkasan

| Region | Provinsi | Lines | Length (km) |
|--------|----------|------:|------------:|
| Maluku | Maluku       | 38 | 272,8 |
| Maluku | Maluku Utara | 23 | 200,0 |
| Papua  | Papua Barat  |  7 |  49,4 |
| Papua  | Papua        | 29 | 235,5 |
| **Total** | | **97** | **757,7** |

Per voltage class:

| Class | Lines | Length (km) | % Length |
|-------|------:|------------:|---------:|
| 150 kV | 82 | 580,7 | 77% |
| 70 kV  | 15 | 177,0 | 23% |
| 275 kV |  0 |   0   |  0% |
| 500 kV |  0 |   0   |  0% |

Per region:

| Region | Lines | Length (km) |
|--------|------:|------------:|
| Maluku | 61 | 472,8 |
| Papua  | 36 | 284,9 |

## Catatan ekstraksi

### Region & sistem listrik

Sama dengan generators Maluku/Papua: tidak ada grid interkoneksi region, jadi field `system` = makro-grup (`Maluku` / `Papua`). Field `province` di-assign per garis via centroid garis.

  - `Maluku`  region → ID prefix `TRM-MLK-XXXX`
  - `Papua`   region → ID prefix `TRM-PAP-XXXX`

### Bbox & assignment

Identik dengan generators (lihat `PROVINCES` di script). Centroid tiebreak untuk overlap Maluku ↔ Papua Barat dan Papua ↔ Papua Barat. Bbox lebih ketat dari substations (Maluku Utara lon_min 125.30 vs 123.90) untuk exclude line Sulawesi Utara (Lahendong interconnect, dll).

Sanity-check: tidak ada line yang centroid-nya bocor ke Sulut/Sulteng setelah bbox revisi (terjauh lon di Maluku Utara: 129,xx area Halmahera).

### Backbone 150 kV — pola koridor

**Maluku Utara (23 lines / 200 km):** Backbone Ternate-Tidore + interkoneksi Halmahera bagian utara (kemungkinan Sofifi-Tobelo-Weda). Beberapa line di Weda Bay industrial complex (smelter Tsingshan-IWIP) yang punya jaringan 150 kV captive.

**Maluku (38 lines / 273 km):** Sistem Ambon (paling padat) + Seram + Buru. Mayoritas line pendek 2-15 km koridor dalam kota. Beberapa line cross-channel ke Pulau Seram. Kei Islands area (PLTMG Dullah) belum punya backbone 150 kV ter-tag (kemungkinan distribusi 20 kV).

**Papua (29 lines / 236 km):** Sistem Jayapura (kompleks PLTMG-PLTU-PLTA Orya Genyem) + line ke Holtekamp. Sistem Timika juga ada beberapa line. Wamena & pegunungan tengah tidak ter-cover di OSM (kemungkinan sistem isolated diesel saja, atau distribusi MV).

**Papua Barat (7 lines / 49 km):** Paling tipis — hanya 7 line di Bird's Head area (Sorong-Manokwari koridor). Line Sorong-Bintuni kemungkinan belum ter-tag.

### Anomali length

Inspect line terpanjang & terpendek:

**Terpanjang per region:**

| ID | Provinsi | Class | Length | OSM ID | Catatan |
|----|----------|-------|-------:|--------|---------|
| TRM-MLK-0052 | Maluku Utara | 150 kV | 67,3 km | way/1318790044 | Wajar — kemungkinan koridor cross-island Halmahera |
| TRM-MLK-0021 | Maluku       | 150 kV | 54,4 km | way/1313323066 | Backbone Seram/Ambon |
| TRM-MLK-0017 | Maluku       | 70 kV  | 47,3 km | way/1313305450 | Sub-koridor |
| TRM-PAP-0004 | Papua        | 70 kV  | 87,3 km | way/692489062 | Terpanjang region — backbone Jayapura-pedalaman |
| TRM-PAP-0001 | Papua        | 150 kV | 57,7 km | way/544403432 | Koridor utama Jayapura |
| TRM-PAP-0003 | Papua        | 150 kV | 26,4 km | way/614955991 | Local interconnect |

Semua wajar — tidak ada line >100 km yang biasa indikasi mis-tagging (mis. garis lurus antar provinsi tanpa segmen).

**Terpendek per region:** 19-31 m. Itu line connector dalam kompleks GI atau bay line yang ter-tag terpisah di OSM. Standar OSM, tidak bermasalah.

### Tidak ada 275 / 500 kV

Sesuai ekspektasi — Maluku & Papua belum punya backbone tegangan ekstra tinggi. RUPTL 2025-2034 memang merencanakan beberapa proyek 150 kV baru (mis. interkoneksi Halmahera-Sulut submarine?), tetapi belum eksisting.

## Limitasi & batasan

- **OSM-only.** Tidak cross-check ke RUPTL Lampiran B (transmission planning). Risiko: line existing yang belum ter-tag OSM (terutama Papua Barat & Wamena pegunungan) akan terlewat. Probe awal 4 line untuk Papua Barat terlihat sangat sedikit untuk provinsi seluas Bird's Head — high likelihood under-coverage.
- **Distribusi tidak di-include** (<70 kV). Banyak sistem pulau kecil Maluku/Papua dispatch via 20 kV distribusi langsung dari PLTD — itu tidak masuk dataset transmission ini.
- **Length absolute** dihitung haversine; cukup akurat untuk MVP peta. Untuk perhitungan loss engineering pakai geodesic.
- **Voltage_kv_all** memuat semua tegangan di tag OSM (`275000;150000` → `275;150`). Untuk klasifikasi pakai `voltage_kv_max`.
- **Cross-region line** (mis. submarine cable Halmahera-Sulut kalau ada): assignment ke region tergantung centroid; kalau centroid di tengah laut antara region, hasilnya ambigu. Saat ini tidak ada line seperti itu di data.

## Reusability untuk Nusa Tenggara (Step 6 transmission)

Pola sama untuk NTB + NTT:

1. Copy script, ganti PROVINCES + ID prefix (`TRM-NTB`, `TRM-NTT`).
2. Bbox NTB: lat (-9.5,-8), lon (115.7,120); NTT: lat (-11,-8), lon (119,125).
3. Centroid tiebreak otomatis menangani overlap antar pulau.
4. Verifikasi NTB sub-marine cable Lombok-Bali (lon ~115.7) tidak bocor ke Bali (lon_min Bali ~114-115.7).

NTT mirip Maluku/Papua: kumpulan pulau, backbone 70/150 kV per-pulau (Sistem Flores, Sumba, Timor). NTB punya interkoneksi Lombok-Sumbawa parsial.

## Sources

- [transmission_master_maluku.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/transmission_master_maluku.csv)
- [transmission_master_papua.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/transmission_master_papua.csv)
- [extract_maluku_papua_transmission.py](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/scripts/extract_maluku_papua_transmission.py)
