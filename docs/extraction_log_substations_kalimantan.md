# Ekstraksi Gardu Induk Kalimantan — Log

**Tanggal:** 2026-05-23 — extraction perdana (Step 3)
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran A, Tabel A11–A15), OSM (Overpass API)
**Output:** `data/processed/substation_master_kalimantan.csv`, `data/processed/substations_kalimantan.geojson`
**Skrip:** `scripts/extract_kalimantan_substations.py`
**Overrides:** `data/overrides/substation_overrides.csv` (7 entries Kalimantan, shared dgn JAMALI & Sumatra)

**Threshold matching identik:** 0.85 absolute, override prioritas pertama, fuzzy SequenceMatcher di bawahnya.

## Ringkasan

| Provinsi | Tabel | System | RUPTL | OSM (bbox) | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------|--------|------:|-----------:|-------------:|---------:|----------:|
| Kalimantan Barat | A11 | Khatulistiwa | 21 | 32 | 20 | 0 | 1 |
| Kalimantan Selatan | A12 | Kalselteng | 27 | 30 | 21 | 3 | 3 |
| Kalimantan Tengah | A13 | Kalselteng | 20 | 36 | 14 | 1 | 5 |
| Kalimantan Timur | A14 | Mahakam | 29 | 42 | 22 | 2 | 5 |
| Kalimantan Utara | A15 | Mahakam | 3 | 7 | 1 | 1 | 1 |
| **Total** | | | **100** | | **78** | **7** | **15** |

Match rate: **85,0%** (85 / 100).

Breakdown per sistem listrik:

| System | Cakupan | Matched | Total | Rate |
|--------|---------|--------:|------:|-----:|
| Khatulistiwa | Kalimantan Barat | 20 | 21 | 95.2% |
| Kalselteng | Kalimantan Tengah + Kalimantan Selatan (Sistem Barito) | 39 | 47 | 83.0% |
| Mahakam | Kalimantan Timur + Kalimantan Utara | 26 | 32 | 81.2% |

## Catatan ekstraksi

### Urutan tabel: A12 & A13 ter-swap

Seperti kasus A3–A8 Sumatra, RUPTL Lampiran A untuk Kalimantan tidak alfabetis. Tebakan awal (A12=Kalteng, A13=Kalsel) salah — verifikasi via cross-check nama kota menunjukkan:

| Tabel | Provinsi sebenarnya | Bukti nama GI |
|-------|---------------------|---------------|
| A11 | Kalimantan Barat | Pontianak, Singkawang, Sambas, Sanggau, Sintang, Ketapang |
| A12 | **Kalimantan Selatan** | Trisakti, Ulin, Kayutangi, Cempaka, Pelaihari, Barikin, Asam Asam |
| A13 | **Kalimantan Tengah** | Buntok, Muara Teweh, Palangkaraya, Sampit, Pangkalan Bun, Sukamara |
| A14 | Kalimantan Timur | Balikpapan, Samarinda, Bontang, Sangatta, Tenggarong, IKN |
| A15 | Kalimantan Utara | Bulungan/Tanjung Selor, Tana Tidung, Malinau |

Iterasi pertama dengan tebakan salah: A13 cuma 2/20 match (signature swap). Setelah A12↔A13 ditukar: 62% → 78%, lalu 85% dengan override.

### Struktur 3 sub-sistem

Region Kalimantan dibagi 3 sub-sistem listrik (field `system`):

- **Khatulistiwa** — Kalimantan Barat. Sistem yang terhubung ke Sarawak (Malaysia) via interkoneksi.
- **Kalselteng** — Kalimantan Selatan + Kalimantan Tengah (dikenal juga Sistem Barito).
- **Mahakam** — Kalimantan Timur + Kalimantan Utara.

PLN sedang menyambungkan ketiga sub-sistem ini jadi satu interkoneksi Kalimantan; sub-sistem tetap dipakai sebagai label karena masih relevan secara operasional.

### Kalimantan Utara hanya 3 GI

A15 (Kaltara) hanya berisi 3 GI di RUPTL — wajar, Kaltara provinsi termuda (pemekaran 2012) dengan sistem kecil. Catatan: "GI Tanjung Selor" muncul di A14 (Kaltim) maupun A15 (Kaltara) sebagai entri terpisah — kemungkinan dua fasilitas berbeda atau pencatatan lintas-tabel RUPTL.

## 7 override yang di-apply

| RUPTL name | Provinsi | Sumber koordinat |
|------------|----------|------------------|
| GI ASAM ASAM | Kalimantan Selatan | centroid PLTU Asam Asam (way/611478867) |
| GI PLTA | Kalimantan Selatan | centroid PLTA Riam Kanan (way/613098761) |
| GI SEI TABUK | Kalimantan Selatan | OSM Gardu Induk Sungai Tabuk (way/1191574020) |
| GI NANGABULIK | Kalimantan Tengah | OSM Gardu Induk Nanga Bulik (way/1193123288) |
| GI Embalut | Kalimantan Timur | centroid PLTU Embalut (way/450527118) |
| GI Muara Jawa | Kalimantan Timur | centroid PLTU Muara Jawa (way/945128872) |
| Bulungan/Tj. Selor | Kalimantan Utara | OSM Gardu Induk Tanjung Selor (way/943966222) |

Catatan: "GI PLTA" adalah nama generik di RUPTL — diidentifikasi sebagai GI di kompleks PLTA Riam Kanan (PLTA Ir P M Noor), satu-satunya PLTA besar di sistem Kalselteng (kapasitas RUPTL 6 MVA, tegangan 70/20).

## 15 GI yang masih UNMATCHED

Mayoritas GI distribusi 150/20 yang belum ada di OSM substations dataset dan tidak punya padanan pembangkit. Untuk iterasi berikutnya: PLN Annual Report atau Overpass API direct query.

| RUPTL name | Provinsi | Catatan |
|------------|----------|---------|
| GI SENGGIRING | Kalimantan Barat | Area Singkawang/Pontianak |
| GI SEBERANG BARITO | Kalimantan Selatan | Banjarmasin, seberang Sungai Barito |
| GI BANDARA | Kalimantan Selatan | GI Bandara Syamsudin Noor, Banjarbaru |
| GI PULAU LAUT | Kalimantan Selatan | Kotabaru; ada "GI Kotabaru" di OSM tapi belum dipastikan fasilitas yang sama |
| GI MINTIN | Kalimantan Tengah | Pulang Pisau area |
| GI SEBANGAU | Kalimantan Tengah | Dekat Palangka Raya |
| GI PLTU SLK | Kalimantan Tengah | Nama mengandung "PLTU"; pembangkit belum teridentifikasi di OSM |
| GI SUDAN | Kalimantan Tengah | Nama tidak lazim, butuh verifikasi |
| GI PANGKALAN BANTENG | Kalimantan Tengah | Kotawaringin Barat |
| GI Bukit Biru | Kalimantan Timur | Tenggarong |
| GI Muara Badak | Kalimantan Timur | Kutai Kartanegara (area gas) |
| GI Teluk Pandan | Kalimantan Timur | Dekat Bontang |
| GI Longikis | Kalimantan Timur | Long Ikis, Paser |
| GI Ibu Kota Negara | Kalimantan Timur | GI untuk IKN Nusantara — fasilitas baru, kemungkinan belum di OSM |
| Tideng Pale/Tana Tidung | Kalimantan Utara | Tideng Pale, Tana Tidung |

## Struktur kolom CSV

Identik dengan JAMALI/Sumatra. Highlights:

- `id` — prefix `GI-KLM-XXXX`
- `system` — `Khatulistiwa` / `Kalselteng` / `Mahakam`
- `match_source` — `osm_fuzzy` / `override:osm_plant` / `override:osm_substation`
- `review_flag` — `UNMATCHED` atau kosong
- `source_table` — `Tabel A11.4` … `Tabel A15.4`

## Limitasi & batasan

- **Hanya GI eksisting** (Tabel Ax.4), tidak termasuk yang masih tahap rencana.
- **Coverage OSM** Kalimantan lebih tipis dari Jawa; sistem Mahakam & Kalteng punya beberapa GI distribusi yang belum di-tag.
- **GI Ibu Kota Negara (IKN)** — infrastruktur baru, kemungkinan besar belum masuk OSM; perlu sumber lain.
- **Bbox per provinsi** overlap di perbatasan; ditangani via name match dalam konteks tabel per-provinsi.

## Reusability untuk Sulawesi & seterusnya

Probe `scripts/_probe_ruptl_tables.py` sudah memetakan: Lampiran A = Sumatra (A1–A10) + Kalimantan (A11–A15), Lampiran B = JAMALI. Region berikutnya (Sulawesi, Maluku-Papua, Nusa Tenggara) kemungkinan di Lampiran C/D — perlu probe ulang untuk konfirmasi. Pola tetap sama:

1. Probe page range & **selalu verifikasi urutan provinsi** (jangan asumsi alfabetis — sudah 2x ter-swap: Sumatra A3–A8, Kalimantan A12–A13).
2. Copy `extract_kalimantan_substations.py`, ganti PROVINCES + ID prefix + path output.
3. Run, cross-check nama kota, perbaiki urutan, populate override, iterate sampai 85%+.
