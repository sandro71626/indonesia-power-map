# Naming Conventions

Single source of truth untuk konvensi penamaan di repo. Tujuan: konsistensi
antara file/folder/code/data, sekaligus respect terhadap nama administratif
resmi Indonesia.

## Prinsip

1. **Island & system labels: pakai ejaan Inggris internasional** (sesuai ISO,
   Wikipedia, jurnal internasional, dan koheren dengan nama proyek yang juga
   English: "Indonesia Power Map").
2. **Nama administratif provinsi: pakai ejaan resmi Bahasa Indonesia**
   (sesuai BPS, Kemendagri, RUPTL).
3. **Quote dari sumber asli (RUPTL, dokumen resmi)**: pakai persis seperti
   di sumber. Kalau ada ambiguitas, dokumentasikan di extraction log.

## Mapping pulau / region (English label)

| Internal label | Yang dimaksud | Indonesian variant (kalau muncul di sumber) |
|----------------|---------------|---------------------------------------------|
| `Sumatra` | Pulau Sumatra dan sistem listriknya | "Sumatera" |
| `Java` | Pulau Jawa (kalau dipakai sebagai region) | "Jawa" |
| `Borneo` / `Kalimantan` | Pulau Kalimantan — gua prefer **Kalimantan** karena di Indonesia konteksnya selalu Kalimantan (Borneo terlalu maritime/colonial). | "Kalimantan" |
| `Sulawesi` | Pulau Sulawesi | "Sulawesi" (sudah English-friendly) |
| `Bali` | Pulau Bali | "Bali" |
| `Madura` | Pulau Madura | "Madura" |
| `Lombok` | Pulau Lombok | "Lombok" |
| `Papua` | Pulau Papua (region) | "Papua" |

## Sistem listrik (system field di CSV)

Field `system` di CSV berisi label sistem listrik, BUKAN provinsi. Pakai
label English / Indonesian acronym sesuai konvensi industri PLN:

| `system` value | Maksudnya |
|----------------|-----------|
| `Jamali` | Jawa–Madura–Bali interkoneksi (Lampiran B RUPTL) |
| `Sumatra` | Sumatra interkoneksi mainland (8 provinsi) |
| `Batam` | Sistem Batam–Bintan (Kepulauan Riau), isolated dari Sumatra |
| `Babel` | Sistem Bangka & Belitung, isolated |
| `Kalimantan` | (Pending Step 3) — akan terbagi lagi: `Kalbar`, `Kalseltengtim`, dst. |
| `Sulawesi` | (Pending Step 4) — akan terbagi `Sulutgo`, `Sulselrabar`, dst. |

Catatan: `Jamali` adalah singkatan PLN yang umum, jadi tetap pakai. Untuk
sistem lain, pakai nama umum yang dipakai di industri/RUPTL.

## Provinsi (province field di CSV) — pakai ejaan resmi Bahasa Indonesia

Nama administratif resmi (per BPS/Kemendagri/RUPTL):

| Sumatra region | Jamali region | (region lain) |
|----------------|---------------|----------------|
| Aceh | DKI Jakarta | Kalimantan Barat |
| Sumatera Utara | Banten | Kalimantan Tengah |
| Sumatera Barat | Jawa Barat | Kalimantan Selatan |
| Riau | Jawa Tengah | Kalimantan Timur |
| Kepulauan Riau | DIY | Kalimantan Utara |
| Kepulauan Bangka Belitung | Jawa Timur | Sulawesi Utara |
| Jambi | Bali | Sulawesi Tengah |
| Sumatera Selatan | | Sulawesi Selatan |
| Bengkulu | | Sulawesi Barat |
| Lampung | | Sulawesi Tenggara |
| | | Gorontalo |

**Catat khusus:** "Sumatera Utara" (provinsi) ≠ "Sumatra Utara". Provinsi
tetap pakai "Sumatera" (ejaan Indonesia). Region/sistem pakai "Sumatra".

Sama untuk "Jawa Barat" (provinsi) ≠ "Java Barat" (gak ada). Provinsi
tetap "Jawa Barat".

## File naming

| Konvensi | Pakai | Jangan |
|----------|-------|--------|
| Script extractor per region | `extract_<region_lower>_<layer>.py` | `extract_<provinsi>_*.py` |
| Data master CSV | `<layer>_master_<region_lower>.csv` | `<layer>_master_<provinsi>.csv` |
| GeoJSON | `<layer>_<region_lower>.geojson` | — |
| Extraction log | `extraction_log_<layer>_<region_lower>.md` | — |

Contoh untuk Sumatra:
- `scripts/extract_sumatra_substations.py`
- `scripts/extract_sumatra_generators.py`
- `data/processed/substation_master_sumatra.csv`
- `data/processed/substations_sumatra.geojson`
- `docs/extraction_log_substations_sumatra.md`

Untuk Jamali, file lama udah pakai `jamali_*` — itu OK, gak perlu di-rename
karena Jamali sendiri adalah acronym yang gak punya ejaan English alternatif.

## ID prefix untuk records

| Prefix | Maksudnya |
|--------|-----------|
| `GI-JMB-XXXX` | Gardu Induk, region Jamali |
| `GI-SMT-XXXX` | Gardu Induk, region Sumatra (semua sistem: Sumatra/Batam/Babel) |
| `GEN-JMB-XXXX` | Generator, Jamali |
| `GEN-SMT-XXXX` | Generator, Sumatra |
| `TRM-JMB-XXXX` | Transmission (ruas), Jamali |
| `TRM-SMT-XXXX` | Transmission (ruas), Sumatra |

ID prefix region-level (bukan per-system) supaya pembagian Sumatra vs Batam
vs Babel jadi tanggung jawab field `system`, bukan prefix ID. Memudahkan
filter & query.

## Override CSV

`data/overrides/substation_overrides.csv` (dan kelak `generator_overrides.csv`
kalau diperlukan) pakai field `province` dengan ejaan resmi (mis. "Sumatera
Utara" tetap pakai "Sumatera"). Tidak ada field `system` di override CSV
karena matching dilakukan via `(ruptl_name, province)` pair.

## Saat ada konflik

Kalau di code lo nemu mismatch (mis. file lama pakai "Sumatera" di nama
folder atau variable Python), update sebagai bagian dari commit terkait
fitur lain (jangan rename-only commit kalau bisa dihindari, biar history
lebih meaningful). Pengecualian: kalau renaming-nya banyak (>10 file),
dedicated commit OK.
