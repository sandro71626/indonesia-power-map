# Ekstraksi Pembangkit Nusa Tenggara — Log

**Tanggal:** 2026-05-27 — extraction perdana (Step 6 generators)
**Sumber utama:** OSM `power=plant` (Overpass) — sumber otoritatif, koord presisi
**Output:**
- `data/processed/generator_master_ntb.csv` + `generators_ntb.geojson`
- `data/processed/generator_master_ntt.csv` + `generators_ntt.geojson`

**Skrip:** `scripts/extract_nusa_tenggara_generators.py`
**Override:** TIDAK ADA (generators pakai OSM langsung; konsisten dgn pola Maluku-Papua / Sulawesi / Kalimantan / Sumatra / JAMALI).

## Ringkasan

| Region | Provinsi | Plant | Plant w/ cap | Total MW (w/ cap) |
|--------|----------|------:|-------------:|------------------:|
| NTB | Nusa Tenggara Barat | 18 | 16 | 679,62 |
| NTT | Nusa Tenggara Timur | 41 | 32 | 287,56 |
| **Total** | | **59** | **48** | **967,18** |

Per system:

| System | Plant | Total MW (w/ cap) |
|--------|------:|------------------:|
| NTB | 18 | 679,62 |
| NTT | 41 | 287,56 |

Per tipe (yang punya kapasitas):

| Type | NTB (n / MW) | NTT (n / MW) |
|------|-------------:|-------------:|
| PLTU  | 5 / 366,00 | 3 / 147,00 |
| PLTG  | 1 / 136,00 | 1 /  10,00 |
| PLTMG | 2 / 130,00 | 3 / 100,00 |
| PLTS  | 8 /  47,62 | 22 / 13,16 |
| PLTD  | 0 /   0    | 2 /   9,40 |
| PLTP  | 0 /   0    | 1 /   8,00 |
| PLTA  | 0 /   0    | 0 /   0    |

(PLTA NTT: 2 entri tagged hydro tapi tanpa capacity — tidak masuk total MW.)

## Catatan ekstraksi

### Region & sistem listrik

Sama pola Maluku/Papua: NTB & NTT region terpisah karena tidak interkoneksi total.

  - `NTB` = Nusa Tenggara Barat → ID prefix `GEN-NTB-XXXX`
  - `NTT` = Nusa Tenggara Timur → ID prefix `GEN-NTT-XXXX`

Catatan operasional: **NTB punya interkoneksi parsial Lombok-Sumbawa via kabel laut 150 kV Selat Alas**. Sistem Bima/Sumbawa Timur masih semi-isolated. **NTT** kumpulan sistem pulau isolated (Flores, Sumba, Timor, Alor, Lembata, Adonara, Solor, Pulau Buaya, dst).

### Bbox revisi vs Bali

NTB `lon_min 115.75` adalah pilihan kritikal — exclude PLTU Celukan Bawang (Bali, lon 114.85), PLTG/PLTDG Pesanggaran (Bali, lon 115.21), PLTG Pemaron (Bali, lon 115.06). Pulau Lombok bagian terbarat (Mataram-Ampenan lon ~116.07) tetap masuk. Verifikasi pass: 4 plant Bali yang dicari `_probe` semuanya `in_ntb_bbox=False`.

NTT `lon_min 119.10` overlap minimal dgn NTB Timur (Bima lon ~118.7, Sape lon ~118.96). Plant terbarat NTT = PLTS Papagarang (lon 119.71) — aman di dalam bbox. Centroid tiebreak menangani overlap minor.

### Cluster dedup dua-pass — 0 entri drop

Dataset OSM NTB/NTT relatif bersih — tidak ada cluster ber-nama duplikat seperti PLTD Fakfak (Maluku/Papua) atau Weda Bay. Pass-1 (4-desimal) dan pass-2 (3-desimal) keduanya `skipped: 0`. Mekanisme tetap di-include (warisan template Maluku/Papua) sebagai defensive measure.

### NTB highlights (18 plant, 680 MW)

**Lombok backbone (interkoneksi 150 kV):**

- **Lombok New Peaker** (Ampenan-Tanjung Karang) — **136 MW** PLTG, plant terbesar di NTB. Terhubung ke sistem 150 kV Lombok.
- **PLTU Jeranjang** (Lombok Barat) — 90 MW PLTU, base load Lombok.
- **PLTU Lombok Timur** (Pijot/Sambelia) — 50 MW.
- **PLTU Sambelia** — 100 MW di Sambelia (Lombok Timur, lat -8.42).
- **PLTS** rural ber-skala 5 MW: Selong, Pringgabaya, Sambelia, Sengkol. Plus PLTS Gili (Trawangan, Air, Meno) di pulau wisata utara Lombok.
- **PTLD Ampenan Power Station** — typo OSM ("PTLD" bukan "PLTD"), dikoreksi via fallback source=diesel → PLTD. Capacity unknown.

**Sumbawa system (semi-isolated, sebagian terhubung 150 kV ke Lombok via Selat Alas):**

- **PLTU Batu Hijau** — 112 MW di Sumbawa Barat (Maluk), kemungkinan captive Newmont/AMNT mining.
- **Komplek PLTMG Sumbawa 1, 2, dan 3** — 80 MW total di Sumbawa Besar (lat -8.45, lon 117.34). Source OSM "diesel;gas" multi-source — derive_type sebelumnya keluarkan "Unknown" karena prefix nama "Komplek" mendahului token "PLTMG". **Diperbaiki**: derive_type sekarang juga search anywhere-in-name untuk pattern PLT-X (lihat catatan teknis di bawah).
- **PLTU Sumbawa Barat** (Taliwang) — 14 MW.
- **PLTMG Bima** — 50 MW di Bima Timur.
- **PLTS Sumbawa** (Pototano) — 26,8 MW PV.
- **(unnamed)** way/119783797 di Dompu area (lat -8.544, lon 118.444) — tidak ada source/cap/nama. UNMATCHED secara identitas tapi koordinat valid. Akan ter-skip dari analisis kapasitas.

### NTT highlights (41 plant, 288 MW)

**Sistem Timor (Kupang & sekitar):**

- **PLTU Timor-1** — 100 MW PLTU coal di Bolok/Kupang.
- **PLTU Bolok** — 33 MW (terkait/sub-unit PLTU Timor-1).
- **PLTMG Kupang** — 40 MW.
- **PLTD Tenau** — 6,4 MW (cold reserve).
- **PLTS Oelpuah** — 5 MW PV (Kupang).
- **PLTU Atapupu** (Belu) — capacity tidak ditag.

**Sistem Flores (kumpulan sistem sub-pulau, tidak interkoneksi total):**

- **PLTMG Maumere** — 40 MW + **PLTU Ropa** 14 MW + **PLTS Maumere** 2 MW + **PLTD Wolomarang** 3 MW.
- **PLTMG Flores** (Rangko, Labuan Bajo) — 20 MW.
- **PLTG Ulumbu** — 10 MW geothermal (Manggarai).
- **PLTP Sokoria** (Ende) — 8 MW geothermal.
- **PLN Cabang Magepanda** & **PLTA-MH** (unknown name) — capacity tidak ditag.

**Sub-pulau (sistem isolated PLTS dominan):**

- 22 PLTS rural di Flores selatan (Mbakung, Wontong, Longos, Golo Munde, Nuca Molas, Nangabere, Solor Barat), Alor (Treweng, Tribur, Ternate, Nule, Pura), Sumba (Praimbana, Raijua, Nembrala), Adonara/Lembata. Skala 100-760 kW (0,1-0,76 MW). Total ~13 MW.

### Anomali kecil terobservasi

| Item | Catatan |
|------|---------|
| GEN-NTB-0001 (unnamed) | way/119783797 (Dompu) — tidak ada source/cap/nama, koordinat valid. Skip dari kalkulasi kapasitas. |
| GEN-NTB-0014 "Komplek PLTMG Sumbawa 1, 2, dan 3" | source="diesel;gas" multi-source; derive_type awalnya keluarkan "Unknown". Diperbaiki via tambahan `re.search` di derive_type. Sekarang ter-categorize PLTMG dengan 80 MW. |
| GEN-NTB-0017 "PTLD Ampenan Power Station" | Typo OSM ("PTLD" instead of "PLTD"). Regex prefix fail → fallback ke source=diesel → PLTD. OK. |
| GEN-NTT-0003 "PLN Cabang Magepanda" | Source kosong → derive_type=Unknown. Kemungkinan PLTD distribusi atau gardu rural mis-tagged. |
| GEN-NTT-0006 "PLTA-MH" | Source kosong, capacity tidak ada. Nama generik (PLTA Mikro Hidro?). Derive PLTA via name prefix match. |
| 2 entri (unnamed) hydro di NTT | way/527176121 (lat -9.674, lon 120.228 Sumba) & way/845393015 (lat -8.760, lon 120.570 Manggarai Timur). Source kosong/hydro tag tapi tanpa cap. |

### Patch derive_type — anywhere-in-name match

Setelah run pertama, "Komplek PLTMG Sumbawa" ter-detect sebagai "Unknown" karena regex prefix `^(PLT\w+)\b` tidak match (token "Komplek" mendahului). Patch sederhana: kalau prefix match gagal, lanjut `re.search` untuk PLT-token di mana saja di nama:

```python
m = re.match(r'^(PLT...)\b', name, re.I)
if m: return m.group(1).upper()
# NTB/NTT: tangani prefix "Komplek PLTMG ..." atau "Unit PLTU ..."
m = re.search(r'\b(PLT...)\b', name, re.I)
if m: return m.group(1).upper()
```

Trade-off: bisa false-positive kalau ada nama plant yang memuat PLT-token di tengah dengan konteks beda. Risiko rendah untuk Indonesia (PLT-acronym hampir pasti merujuk ke tipe pembangkit). Patch ini hanya di NTB/NTT script — region sebelumnya tidak perlu (tidak ada kasus "Komplek X" yang menyebabkan Unknown). Bisa di-backport ke template Maluku/Papua kalau ada kasus serupa muncul.

## Review flags

| Flag | Count | Catatan |
|------|------:|---------|
| NO_NAME     | 4 | 1 NTB (Dompu unnamed) + 3 NTT (1 unnamed Sumba, 2 unnamed hydro/solar) |
| NO_CAPACITY | 11 | 2 NTB (Dompu unnamed, PTLD Ampenan) + 9 NTT (mostly PLTS sub-pulau yang cap di OSM = `yes`) |
| NO_TYPE     | 3 | 1 NTB (Dompu unnamed, source kosong) + 2 NTT (PLN Cabang Magepanda, unnamed Sumba) |

PLTS sub-pulau NTT yang cap=`yes` (Koja besar, Parumaan, DESA PULAU BUAYA, dll) — sumber referensi non-OSM (PLN news release / RUPTL Lampiran D) bisa melengkapi nilai numerik di iterasi berikutnya.

## Total Mappable Capacity (preliminary)

- **NTB:** 16 plant ter-parse cap, **680 MW**. Plant terbesar PLTU Sambelia (100 MW) + PLTU Batu Hijau (112 MW captive). Backbone 150 kV Lombok-Sumbawa.
- **NTT:** 32 plant ter-parse cap, **288 MW**. Plant terbesar PLTU Timor-1 (100 MW). Dominasi PLTS rural di sub-pulau kecil.

Total NTB+NTT = **967 MW** untuk plant yang punya capacity ter-parse. Cap riil sedikit lebih tinggi karena ~11 entri NO_CAPACITY (mostly PLTS skala kecil + PLTU Atapupu).

## Limitasi & batasan

- **OSM-only.** Tidak ada cross-check ke RUPTL Lampiran D. Risiko plant baru pasca-2024 yang belum di-tag OSM akan terlewat.
- **Capacity coverage 81%** (48/59 plant punya capacity). Higher than Maluku/Papua (54%) — dataset OSM NTB/NTT lebih bersih.
- **Sub-system label sederhana** (`NTB` / `NTT`) — tidak detail per-pulau. Sistem Lombok, Sumbawa, Flores, Sumba, Timor, Alor bisa di-label di iterasi berikutnya kalau diperlukan untuk analisis dispatch.
- **"PTLD Ampenan" typo** — OSM-side cleanup recommended (edit OSM langsung).
- **Captive plants** (PLTU Batu Hijau Newmont, mungkin PLTU Atapupu) tidak terdiferensiasi dari grid plants. Field `operator` di OSM kosong untuk sebagian besar.

## Sources

- [generator_master_ntb.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/generator_master_ntb.csv)
- [generator_master_ntt.csv](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/data/processed/generator_master_ntt.csv)
- [extract_nusa_tenggara_generators.py](computer:///Users/sandrositompul/Documents/Claude/Projects/Indonesia Power Map/scripts/extract_nusa_tenggara_generators.py)
