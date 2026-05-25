# Ekstraksi Gardu Induk Maluku & Papua — Log

**Tanggal:** 2026-05-26 — extraction perdana (Step 5)
**Sumber utama:** RUPTL PLN 2025–2034 (Lampiran C, Tabel C7–C10), OSM (Overpass API)
**Output:**
- `data/processed/substation_master_maluku.csv`, `data/processed/substations_maluku.geojson`
- `data/processed/substation_master_papua.csv`, `data/processed/substations_papua.geojson`

**Skrip:** `scripts/extract_maluku_papua_substations.py` (satu extractor, dua region)
**Overrides:** `data/overrides/substation_overrides.csv` (1 entry Maluku, shared dgn region lain)

**Threshold matching identik:** 0.85 absolute, override prioritas pertama, fuzzy SequenceMatcher di bawahnya.

## Struktur region

Berbeda dari region sebelumnya, Maluku & Papua **tidak punya grid
interkoneksi** — keduanya kumpulan sistem pulau yang terisolasi. Sesuai
keputusan desain, Step 5 ditulis sebagai **dua region peta terpisah**, dan
field `system` cuma dua makro-grup (bukan sub-sistem interkoneksi):

| Region peta | Provinsi (Tabel) | system | ID prefix |
|-------------|------------------|--------|-----------|
| `maluku` | Maluku (C7) + Maluku Utara (C8) | Maluku | GI-MLK |
| `papua` | Papua (C9) + Papua Barat (C10) | Papua | GI-PAP |

Satu extractor memproses keempat tabel dan menulis dua set output.

## Ringkasan

| Provinsi | Tabel | Region | RUPTL | Fuzzy ≥ 0.85 | Override | Unmatched |
|----------|-------|--------|------:|-------------:|---------:|----------:|
| Maluku | C7 | maluku | 7 | 6 | 1 | 0 |
| Maluku Utara | C8 | maluku | 5 | 5 | 0 | 0 |
| Papua | C9 | papua | 5 | 5 | 0 | 0 |
| Papua Barat | C10 | papua | 3 | 3 | 0 | 0 |
| **Total** | | | **20** | **19** | **1** | **0** |

Match rate: **100%** (20 / 20).

| Region | GI | Trafo | Kapasitas (MVA) | Match |
|--------|---:|------:|----------------:|------:|
| Maluku | 12 | 20 | 720 | 100% |
| Papua | 8 | 18 | 675 | 100% |
| **Total** | **20** | **38** | **1.395** | **100%** |

Match rate 100% di sini **bukan** karena coverage OSM bagus, melainkan
karena jaringan transmisi Maluku & Papua memang sangat kecil (cuma 20 GI
eksisting di seluruh RUPTL C7–C10) dan GI-GI yang ada itu sudah ter-map
di OSM. Lihat bagian "Limitasi".

## Catatan ekstraksi

### Format tabel MULTI-TEGANGAN — parser ditulis ulang

Tabel Lampiran C Maluku/Papua memakai layout yang **tidak muncul** di
region sebelumnya: satu GI bisa membentang beberapa baris, satu baris per
level tegangan trafo. Sel "No" & "Nama GI" di-merge vertikal, jadi
`pdftotext` me-render nama GI di baris **tengah** blok — kadang di baris
yang juga memuat data, kadang di baris sendiri tanpa data.

Contoh nyata (Tabel C9.4, Papua):

```
                          70/20      1     20
  1  Skyland/Jayapura     150/20     2     120
                          150/70     1     60
  2  Sentani/Wamena       70/20      2     60
  3  Genyem               70/20      2     25
                          70/20      1     30
  4  Holtekamp
                          150/70     1     60
  5  Timika               150/20     2     120
```

Parser lama (satu baris = satu GI) **melewatkan Holtekamp** (baris namanya
tanpa data) dan **under-count** trafo/kapasitas GI multi-tegangan (Skyland
tercatat 2 trafo/120 MVA, padahal 4 trafo/200 MVA).

`extract_table()` ditulis ulang: klasifikasi tiap baris jadi NAME atau
VOLT, lalu tiap NAME "menyerap" baris VOLT di atas & bawahnya secara
**simetris** (karena sel nama ter-render di tengah blok, jumlah VOLT di
atas selalu sama dengan di bawah). `trafo_count` & `capacity_mva` tiap GI
= jumlah seluruh level tegangan; `voltage` = level tegangan unik, desc
(mis. `150/70/20`). Diverifikasi terhadap baris "Jumlah" tiap tabel:
C7 = 14 trafo/490 MVA, C8 = 6/230, C9 = 12/495, C10 = 6/180 — semua cocok.

> **Follow-up:** format multi-tegangan ini kemungkinan juga ada di
> sebagian GI region sebelumnya (Sulawesi C4 punya satu "baris nama
> kosong" yang dulu di-flag UNMATCHED — gejala yang sama). Worth di-audit:
> backport parser baru ini & re-run JAMALI/Sumatra/Kalimantan/Sulawesi
> untuk cek apakah ada GI multi-tegangan yang ter-lewat atau under-count.

### Urutan tabel C7–C10 — terverifikasi

Urutan provinsi diverifikasi lewat probe nama GI (`_probe_c_provinces.py`)
dan dikonfirmasi ulang dari nama GI yang ter-extract:

| Tabel | Provinsi | Bukti nama GI |
|-------|----------|---------------|
| C7 | Maluku | Passo, Sirimau, Hative Besar, Masohi, Piru (Ambon & Seram) |
| C8 | Maluku Utara | Ternate, Jailolo, Malifut, Sofifi, Tobelo (Halmahera) |
| C9 | Papua | Skyland/Jayapura, Sentani, Genyem, Holtekamp, Timika |
| C10 | Papua Barat | Aimas, Sorong, Rufey (Sorong raya) |

Tidak ada swap; C7–C10 berurutan.

## 1 override yang di-apply

| RUPTL name | Provinsi | Sumber koordinat |
|------------|----------|------------------|
| Hative Besar | Maluku | OSM Gardu Induk Wayame (way/949578855) |

RUPTL menyebut GI ketiga ring 150 kV Ambon "Hative Besar"; OSM
menamainya "Gardu Induk Wayame". Identifikasi **by elimination**: ring
150 kV Ambon punya tepat 3 GI — RUPTL {Passo, Sirimau, Hative Besar},
OSM {Passo, Sirimau, Wayame} (dua GI OSM lain di area, Waai & Kairatu,
adalah GI ekstensi interkoneksi Seram yang belum masuk tabel eksisting
RUPTL). Desa Hative Besar & Wayame bersebelahan di pesisir utara Teluk
Ambon. Probe: `scripts/_probe_hative.py`.

## Tidak ada GI UNMATCHED

Pertama kali sejak Step 1: 0 unmatched. Karena populasi GI sangat kecil
(20) dan semuanya GI kota utama yang sudah ter-map di OSM.

## Struktur kolom CSV

Identik dengan region sebelumnya. Highlights:

- `id` — prefix `GI-MLK-XXXX` (Maluku) / `GI-PAP-XXXX` (Papua)
- `voltage` — level tegangan unik desc; GI multi-tegangan mis. `150/70/20`
- `trafo_count`, `capacity_mva` — **total seluruh level tegangan** GI
- `system` — `Maluku` / `Papua`
- `match_source` — `osm_fuzzy` / `override:osm_substation`
- `source_table` — `Tabel C7.4` … `Tabel C10.4`

## Limitasi & batasan

- **Hanya GI eksisting** (Tabel Cx.4). RUPTL Maluku/Papua banyak menyebut
  rencana transmisi 150 kV baru (Seram, Buru, interkoneksi Sorong–
  Manokwari, dll) yang belum masuk tabel eksisting.
- **Jaringan transmisi minim** — sebagian besar Maluku & Papua masih
  dilayani sistem 20 kV + diesel terisolasi tanpa GI tegangan tinggi.
  20 GI untuk dua provinsi besar memang mencerminkan kondisi nyata, bukan
  gap data.
- **Sistem captive** (mis. pembangkit & jaringan Freeport di Timika)
  tidak tercakup tabel GI PLN.
- **`system` = makro-grup**, bukan sistem interkoneksi — di Maluku/Papua
  memang tidak ada interkoneksi; lihat bagian "Struktur region".

## Status Step 5 (substations)

| Region | GI | Match |
|--------|---:|------:|
| Maluku | 12 | 100% |
| Papua | 8 | 100% |

Langkah berikutnya Step 5: generators lalu transmission untuk kedua region,
kemudian integrasi web (dua region baru di `preview_indonesia.html`).
