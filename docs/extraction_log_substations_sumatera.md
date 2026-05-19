# Ekstraksi Gardu Induk Sumatera — Log

**Tanggal:** 2026-05-19 — extraction perdana (Step 2)
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran A), OSM (Overpass API)
**Output:** `data/processed/substation_master_sumatera.csv`, `data/processed/substations_sumatera.geojson`
**Skrip:** `scripts/extract_sumatera_substations.py`
**Overrides:** `data/overrides/substation_overrides.csv` (19 entries Sumatera, plus 11 entries Jamali — shared)

**Threshold matching identik dengan JAMALI iterasi 2:** 0.85 absolute, override prioritas pertama, fuzzy SequenceMatcher di bawahnya.

## Ringkasan

| Provinsi | Tabel sumber | System | RUPTL | OSM (bbox) | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------------|--------|------:|-----------:|-------------:|---------:|----------:|
| Aceh | Tabel A1.4 | Sumatera | 20 | 22 | 16 | 2 | 2 |
| Sumatera Utara | Tabel A2.4 | Sumatera | 53 | 61 | 45 | 6 | 2 |
| Riau | Tabel A3.4 | Sumatera | 21 | 58 | 19 | 2 | 0 |
| Kepulauan Riau | Tabel A4.4 | Batam | 5 | 17 | 5 | 0 | 0 |
| Kep. Bangka Belitung | Tabel A5.4 | Babel | 10 | 14 | 7 | 2 | 1 |
| Sumatera Barat | Tabel A6.4 | Sumatera | 20 | 36 | 15 | 3 | 2 |
| Jambi | Tabel A7.4 | Sumatera | 12 | 19 | 8 | 0 | 4 |
| Sumatera Selatan | Tabel A8.4 | Sumatera | 34 | 59 | 29 | 1 | 4 |
| Bengkulu | Tabel A9.4 | Sumatera | 6 | 20 | 3 | 2 | 1 |
| Lampung | Tabel A10.4 | Sumatera | 29 | 45 | 26 | 1 | 2 |
| **Total** | | | **210** | | **173** | **19** | **18** |

Match rate: **91,4%** (192 / 210).

Breakdown per sistem listrik:

| System | Cakupan | Matched | Total | Rate |
|--------|---------|--------:|------:|-----:|
| Sumatera (interkoneksi 275 kV mainland) | 8 provinsi mainland | 178 | 195 | 91.3% |
| Batam | Kepulauan Riau (Batam–Bintan) | 5 | 5 | 100.0% |
| Babel | Kep. Bangka Belitung | 9 | 10 | 90.0% |

## Yang berbeda dari JAMALI

### 1. Urutan tabel Lampiran A tidak alfabetis

RUPTL Lampiran A meloncat-loncat secara geografis. Setelah Aceh & Sumut (urut), tabel meloncat ke Riau → Kepri → Babel (timur), baru balik ke Sumbar → Jambi → Sumsel (tengah/barat), terus Bengkulu → Lampung. Urutan tabel persis:

| Tabel ID | Provinsi |
|----------|----------|
| A1 | Aceh |
| A2 | Sumatera Utara |
| A3 | Riau |
| A4 | Kepulauan Riau (Batam) |
| A5 | Kep. Bangka Belitung |
| A6 | Sumatera Barat |
| A7 | Jambi |
| A8 | Sumatera Selatan |
| A9 | Bengkulu |
| A10 | Lampung |

Asumsi awal alfabetis menyebabkan iterasi pertama match rate 50,5% dengan banyak **false-positive match di koordinat salah**: nama GI Riau ke-extract tapi di-label Sumbar dengan bbox Sumbar → 9 false match. Fix: re-order `PROVINCES` list di extractor + assign bbox sesuai nama provinsi. Match rate naik ke 82,4%.

### 2. Heading tabel berbeda phrasing

Lampiran B (JAMALI) pakai **"Kapasitas Gardu Induk Eksisting"**. Lampiran A (Sumatera) pakai **"Kapasitas Trafo Gardu Induk"** — ada kata "Trafo" yang tidak ada di JAMALI. Plus, A8 (Babel) doang yang pakai variasi "Kapasitas Trafo Gardu Induk **Eksisting**".

Regex extraction Sumatera dibuat fleksibel: kata "Trafo" wajib, modifier "Realisasi" dan "Eksisting" opsional.

### 3. Tegangan 275 kV muncul (tidak ada di JAMALI)

Backbone Sumatera interkoneksi pakai 275 kV (vs 500 kV di JAMALI). Beberapa GI di output punya `voltage = '275/150'` atau `'150/275'`. Color palette di `docs/design_decisions.md` sudah punya entry untuk 275 kV (`#9467bd`, ungu) — siap pakai.

### 4. Multi-system di satu region

Sumatera region punya **3 sistem listrik terpisah** (vs JAMALI yang satu sistem interkoneksi):

- **Sumatera** — 8 provinsi mainland terinterkoneksi (Aceh, Sumut, Sumbar, Riau, Jambi, Sumsel, Bengkulu, Lampung). Backbone 275 kV.
- **Batam** — Sistem Kepulauan Riau (Batam-Bintan-Karimun-Lingga). Sistem isolated yang terinterkoneksi internal antar-pulau Batam-Bintan.
- **Babel** — Sistem Bangka & sistem Belitung. Dua sistem isolated terpisah yang sama-sama di provinsi Kep. Bangka Belitung.

Field `system` di output CSV jadi diskriminator. Saat rendering di peta, ini bisa dipakai untuk style berbeda atau toggle visibility per sistem.

## 19 override yang di-apply

Audit trail per override entry (lihat `data/overrides/substation_overrides.csv` untuk detail koordinat). Semua via centroid OSM (`power=plant` atau `power=substation` dengan nama alternatif).

### Plant centroid (11 entries)

GI step-up yang ko-lokasi dengan polygon `power=plant`:

| RUPTL name | Provinsi | OSM plant |
|------------|----------|-----------|
| PLTU Nagan Raya | Aceh | way/321541350 PLTU Nagan Raya |
| Arun | Aceh | way/542904306 PLTMG Arun I (eks kompleks LNG Arun) |
| Belawan | Sumatera Utara | way/277183762 PLTGU Belawan |
| Tenayan | Riau | way/528916594 PLTU Tenayan Raya |
| Air Anyir | Babel | way/543959909 PLTU Air Anyir (Bangka) |
| Suge (GI Pembangkit) | Babel | way/953023896 PLTU Suge (Belitung) |
| Maninjau | Sumatera Barat | way/930242896 PLTA Maninjau |
| Muaralabuh | Sumatera Barat | way/1312349205 PLTP Muara Laboh |
| Bukit Asam | Sumatera Selatan | way/719550864 PLTU Bukit Asam |
| Tes | Bengkulu | way/956594058 PLTA Tes |
| Ulubelu | Lampung | way/531143189 PLTP Ulubelu |

### Substation alternate name (8 entries)

GI yang ada di OSM substations dataset tapi nama berbeda dari RUPTL — biasanya karena RUPTL pakai singkatan ("P.", "T.", "R.", "S.", "KID") atau ejaan berbeda:

| RUPTL name | Provinsi | OSM substation |
|------------|----------|----------------|
| T. Morawa | Sumatera Utara | way/519390726 Gardu Induk Tanjung Morawa |
| P. Brandan | Sumatera Utara | way/754073847 Gardu Induk Pangkalan Brandan |
| R. Prapat | Sumatera Utara | way/522690659 Gardu Induk Rantau Prapat |
| P. Sidimpuan | Sumatera Utara | way/469888044 Gardu Induk Padang Sidempuan (beda ejaan i/e) |
| Panyabungan | Sumatera Utara | way/938146459 Gardu Induk Panyabungan |
| KID | Riau | way/947860177 Gardu Induk Kawasan Industri Dumai |
| S. Rumbai | Sumatera Barat | way/1312287191 Gardu Induk Sungai Rumbai |
| P. Baai | Bengkulu | way/930719090 Gardu Induk Pulau Baai |

## 18 GI yang masih UNMATCHED

Mayoritas adalah GI distribusi 150/20 atau 70/20 di area pelosok/kabupaten yang belum di-tag di OSM substations dataset (no entry sama sekali). Tidak ada padanan plant juga, karena ini GI distribusi murni (bukan step-up dari pembangkit).

Untuk iterasi berikutnya: kandidat sumber koordinat adalah PLN Annual Report (lokasi GI per UID/UP3), atau Overpass API direct query yang mungkin nge-catch node-node tanpa nama tapi ber-tag `power=substation`.

| RUPTL name | Provinsi | Catatan untuk research lanjutan |
|------------|----------|----------------------------------|
| Banda Aceh I / Lambaroe | Aceh | "Lambaroe" = area Aceh Besar; cek OSM tag `Lambaro` |
| Singkil | Aceh | Aceh Singkil, kemungkinan GI distribusi kecil |
| GIS Listrik | Sumatera Utara | Nama ambigu; cek apakah GI internal industri atau substation kampus |
| Teluk Dalam | Sumatera Utara | Nias Selatan; sistem mungkin isolated kecil |
| Dukong | Babel | Belitung area; cek apakah typo "Dukung" |
| Simpang Haru | Sumatera Barat | Padang kota; GI distribusi |
| Kiliranjao | Sumatera Barat | Dharmasraya area; mungkin "Kiliran Jao" |
| Payo Selincah | Jambi | Jambi kota; cek PLTU Payo Selincah co-location |
| Sungai Gelam | Jambi | Muaro Jambi regency |
| Muara Tebo | Jambi | Tebo regency, GI distribusi |
| Sungai Penuh | Jambi | Kerinci, GI distribusi |
| GIS Kota Barat | Sumatera Selatan | Palembang area, GIS indoor |
| GIS Kota Timur | Sumatera Selatan | Palembang area, GIS indoor |
| Gunung Megang | Sumatera Selatan | Muara Enim; PLTU Gunung Megang? |
| Simpang Tiga | Sumatera Selatan | Nama generik (banyak Simpang Tiga di Indonesia) |
| Mukomuko | Bengkulu | Pesisir utara Bengkulu, distribusi |
| Pakuan Ratu | Lampung | Way Kanan, distribusi |
| Dipasena | Lampung | Tulang Bawang, eks-tambak udang area |

## Struktur kolom CSV

Identik dengan JAMALI iterasi 2 — lihat `docs/extraction_log_substations_jamali.md` untuk reference lengkap. Highlights:

- `id` — prefix `GI-SMT-XXXX` untuk semua entry Sumatera (termasuk Batam & Babel; diskriminator sistem via field `system`)
- `system` — `Sumatera` / `Batam` / `Babel`
- `match_source` — `osm_fuzzy` / `override:osm_plant` / `override:osm_substation` (no `override:manual` di iterasi ini)
- `review_flag` — `UNMATCHED` atau kosong
- `source_table` — `Tabel A1.4`, `Tabel A2.4`, dst.

## Limitasi & batasan

- **Hanya GI eksisting** (Tabel Ax.4), tidak termasuk yang masih tahap rencana.
- **Sistem isolated** (Batam, Babel) coverage OSM lebih tipis dari mainland. Override compensate untuk pembangkit besar tapi GI distribusi murni tetap miss.
- **Bbox per provinsi** diturunkan dari pengetahuan umum batas administratif; ada beberapa kasus overlap (mis. Sumut-Aceh di sekitar Tapanuli Utara) yang ditangani via field name match.
- **Tabel A3 (Riau)** hanya berisi 21 GI di RUPTL — angka ini sengaja dicross-check via diagnostic dan memang sesuai dengan jumlah baris di PDF. GI distribusi Riau berkapasitas kecil (di bawah threshold listing RUPTL) tidak masuk.

## Reusability untuk Kalimantan & seterusnya

Probe `scripts/_probe_ruptl_tables.py` sudah mengonfirmasi bahwa Kalimantan ada di **Lampiran A11–A15** (page 730+), terus B1–B7 = JAMALI (done), kemungkinan Lampiran C/D = Sulawesi/Maluku-Papua. Pola yang dipakai di sini bisa di-replikasi untuk semua region berikutnya:

1. Probe page ranges & confirm urutan tabel (jangan asumsi alfabetis).
2. Identify phrasing tabel (mungkin ada variasi lain lagi).
3. Copy extractor template `extract_sumatera_substations.py`, ganti PROVINCES list + heading regex prefix (A→ C → dst).
4. Run, identify unmatched, populate overrides di CSV yang sama (`substation_overrides.csv`).
5. Iterate sampai match rate 90%+.
6. Document di extraction_log per region.

## Lesson learned untuk iterasi pertama

1. **Verify ordering ground-truth lebih awal.** Asumsi A1=Aceh, A2=Sumut alfabetis ternyata cuma kebetulan benar untuk 2 entry pertama. A3-A8 keacak. Pelajaran: setelah extractor jadi, **cek nama-nama yang ter-extract di 1 baris pertama tiap provinsi** match dengan provinsi yang diharapkan, sebelum kerja override.

2. **Heading regex JAMALI tidak portable.** "Eksisting" wajib di JAMALI, opsional di Sumatera; "Trafo" wajib di Sumatera, tidak ada di JAMALI. Untuk Kalimantan dan seterusnya, mulai dari regex paling fleksibel (`Tabel\s+\w+\.\d+.*Gardu Induk`), lalu sempit-kan setelah probe.

3. **Sistem isolated punya kelemahan struktural OSM.** Coverage substation OSM untuk Batam & Babel sangat tipis. Tapi pembangkit-nya ada (PLTU Suge, PLTU Air Anyir, PLTU Tanjung Kasam). Strategi plant-co-location bekerja sangat baik di sini.
