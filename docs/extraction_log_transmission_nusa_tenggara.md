# Ekstraksi Transmisi Nusa Tenggara — Log

**Tanggal:** 2026-05-27 — extraction perdana (Step 6 transmission)
**Sumber utama:** OSM `power=line` (Overpass) — sumber otoritatif, geometri LineString
**Output:**
- `data/processed/transmission_master_ntb.csv` + `transmission_ntb.geojson`
- `data/processed/transmission_master_ntt.csv` + `transmission_ntt.geojson`

**Skrip:** `scripts/extract_nusa_tenggara_transmission.py`
**Override:** TIDAK ADA (transmission pakai OSM langsung, konsisten dgn pola Maluku-Papua / Sulawesi / Kalimantan / Sumatra / JAMALI).
**Filter tegangan:** >= 70 kV.

## Ringkasan

| Region | Provinsi | Lines | Length (km) |
|--------|----------|------:|------------:|
| NTB | Nusa Tenggara Barat | 31 |   654,5 |
| NTT | Nusa Tenggara Timur | 51 |   758,3 |
| **Total** | | **82** | **1.412,8** |

Per voltage class:

| Class | Lines | Length (km) | % Length |
|-------|------:|------------:|---------:|
| 150 kV | 51 |   576,3 | 41% |
| 70 kV  | 31 |   836,5 | 59% |
| 275 kV |  0 |     0   |  0% |
| 500 kV |  0 |     0   |  0% |

Per region (length-weighted):

| Region | Lines | Length (km) | Pattern voltage |
|--------|------:|------------:|------------------|
| NTB | 31 | 654,5 | Dominan 150 kV (backbone Lombok) |
| NTT | 51 | 758,3 | Mix 150/70 kV (sistem pulau) |

## Catatan ekstraksi

### Region & sistem

Sama pola generators & substations: 2 region terpisah, sistem makro `NTB` / `NTT`.

  - `NTB` region → ID prefix `TRM-NTB-XXXX`
  - `NTT` region → ID prefix `TRM-NTT-XXXX`

### Bbox & sanity

Identik dgn generators (lihat `PROVINCES`). Centroid garis di-assign via bbox + centroid tiebreak. Sanity verified:

- **No Bali leak.** Sub-probe `min_lon < 115.6` di centroid-in-NTB → 0 hits. Line backbone Bali Selatan (Pesanggaran-Kapal-Negara) tidak nyangkut ke bbox NTB.
- **No bocor ke Sumbawa Timur dari NTT.** Bbox NTB extends ke lon 119.30 (cover Sape, Bima), NTT mulai lon 119.10 — overlap 0.20° ditangani via centroid tiebreak (NTB centroid -8.50,117.50 ↔ NTT centroid -9.00,122.00).

### Pattern jaringan NTB (31 lines / 655 km)

**Lombok backbone 150 kV (dominan):**
- Mataram-Ampenan + Selong + Sambelia + Sengkol + Kuta — backbone interkoneksi 150 kV Lombok.
- Beberapa line panjang: TRM-NTB-0013 (79 km 150 kV) dan TRM-NTB-0016 (77 km 150 kV) — kemungkinan koridor utara-selatan Lombok atau sub-marine Lombok-Sumbawa segments.

**Sumbawa 70 kV (sub-koridor):**
- 6 line 70 kV — backbone sistem Bima/Sumbawa Timur (Empang-Dompu-Bima-Sape) yang masih semi-isolated.
- TRM-NTB-0011 71,9 km 70 kV — kemungkinan koridor Dompu-Bima.
- TRM-NTB-0017 50,6 km 70 kV.

### Pattern jaringan NTT (51 lines / 758 km)

**Sistem Timor 150/70 kV:**
- Backbone Kupang (Tenau-Bolok-Maulafa) → Naibonat → Nonohonis → Kefamenanu → Atambua → Atapupu — full coverage Timor barat dari Kupang ke perbatasan Timor Leste.
- Mix 150 kV (Tenau-Naibonat) dan 70 kV (lanjutan ke utara/timur).

**Sistem Flores 70 kV:**
- Backbone Labuan Bajo (PLTMG Flores) → Ulumbu → Bahong (Ruteng) → Ende → Ropa → Maumere — koridor panjang yang menyusur Flores barat-timur.
- TRM-NTT-0004 **109,2 km 70 kV** — terpanjang di Nusa Tenggara. Kemungkinan section Ende-Maumere atau Labuan Bajo-Ruteng yang melewati pegunungan tengah.
- TRM-NTT-0015 89 km 70 kV, TRM-NTT-0012 75,6 km, TRM-NTT-0002 75,4 km — koridor Flores lainnya.

**Sub-pulau sistem isolated:** Beberapa line di Solor/Adonara/Lembata (PLTS-fed grid), tapi mayoritas pulau kecil NTT mengandalkan distribusi 20 kV langsung dari PLTD lokal — tidak masuk dataset transmission.

### Anomali length

**Terpanjang per region:**

| ID | Region | Class | Length | OSM ID | Konteks |
|----|--------|-------|-------:|--------|---------|
| TRM-NTB-0013 | NTB | 150 kV | 79,3 km | way/707531068 | Backbone Lombok atau Lombok-Sumbawa |
| TRM-NTB-0016 | NTB | 150 kV | 77,4 km | way/707533373 | Idem |
| TRM-NTB-0011 | NTB | 70 kV  | 71,9 km | way/707531065 | Sumbawa Tengah-Timur |
| TRM-NTT-0004 | NTT | 70 kV  | **109,2 km** | way/614243450 | Flores backbone (Ende-Maumere area) — terpanjang Nusa Tenggara |
| TRM-NTT-0015 | NTT | 70 kV  | 89,0 km | way/937059872 | Flores backbone |
| TRM-NTT-0012 | NTT | 70 kV  | 75,6 km | way/937059864 | Flores backbone |
| TRM-NTT-0002 | NTT | 70 kV  | 75,4 km | way/611789539 | Timor (Naibonat-Nonohonis-Kefamenanu) |

Semua wajar — backbone Flores via pegunungan tengah dan Timor cross-island memang panjang. Tidak ada line >150 km yang biasa indikasi mis-tagging.

**Terpendek:** 31-34 m. Connector dalam kompleks GI / bay line. Standar OSM, tidak bermasalah.

### Tidak ada 275 / 500 kV

Sesuai status grid Indonesia Timur — NTB & NTT belum punya backbone tegangan ekstra tinggi. RUPTL 2025-2034 merencanakan beberapa upgrade 150 kV (terutama interkoneksi sub-marine NTT) tapi belum eksisten.

## Limitasi & batasan

- **OSM-only.** Tidak cross-check ke RUPTL Lampiran B (transmission planning).
- **Distribusi tidak ter-include** (<70 kV). Sebagian besar pulau kecil NTT dispatch via 20 kV langsung dari PLTD — itu tidak masuk dataset transmission.
- **Submarine cable Lombok-Sumbawa Selat Alas** — di RUPTL terdaftar; di OSM kemungkinan ter-tag sebagai line dengan length panjang. Verifikasi visual perlu untuk memastikan ini ter-tag dengan benar.
- **NTT sub-pulau coverage tipis** — Alor, Lembata, Adonara, Solor mostly distribution 20 kV, tidak masuk filter 70+ kV.
- **Length pakai haversine.** Cukup untuk MVP; engineering analysis perlu geodesic.

## Step 6 closeout — Nusa Tenggara complete

Dengan ini Step 6 (Nusa Tenggara) selesai untuk **data extraction 3 layer**:

| Layer | Output | Skala |
|-------|--------|------:|
| Substations | 4 file (CSV+GeoJSON × NTB, NTT) | 45 GI (82,2% match), 3 override |
| Generators  | 4 file | 59 plant, 967 MW |
| Transmission | 4 file | 82 lines, 1.413 km |

**Cakupan Indonesia setelah Step 6:** JAMALI, Sumatra, Kalimantan, Sulawesi, Maluku, Papua, NTB, NTT — **8 region, 30+ provinsi**, full coverage data eksisten.

Layer berikutnya: integrasi NTB/NTT ke `preview_indonesia.html` (bundle `data_ntb.js` + `data_ntt.js`) untuk peta gabungan final → `v0.6.0` release.

## Sources

- [transmission_master_ntb.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/transmission_master_ntb.csv)
- [transmission_master_ntt.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/transmission_master_ntt.csv)
- [extract_nusa_tenggara_transmission.py](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/scripts/extract_nusa_tenggara_transmission.py)
