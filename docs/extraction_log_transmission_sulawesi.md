# Ekstraksi Transmisi (Transmission) Sulawesi — Log

**Tanggal:** 2026-05-26 — extraction perdana (Step 4)
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_lines.geojson`
**Output:** `data/processed/transmission_master_sulawesi.csv`, `data/processed/transmission_sulawesi.geojson`
**Skrip:** `scripts/extract_sulawesi_transmission.py`

## Metodologi

Sama dengan extractor transmisi JAMALI, Sumatra & Kalimantan: OSM
`power=line` adalah sumber otoritatif (punya geometri LineString). Extractor
memfilter tegangan transmisi (≥ 70 kV), menghitung panjang via haversine,
mengkategorikan voltage class, dan meng-assign sub-sistem listrik berdasar
centroid garis.

Sama seperti Kalimantan, ketiga sub-sistem Sulawesi ada di satu daratan dan
bbox-nya overlap di "pinggang" tengah pulau. `assign_system` memakai
centroid tiebreak — kalau centroid garis masuk >1 bbox, dipilih sistem
dengan centroid sistem terdekat.

## Ringkasan

**390 ruas transmisi** ter-extract di region Sulawesi, total **4.733 km**.

### Skip breakdown

| Alasan skip | Jumlah |
|-------------|-------:|
| Di luar region Sulawesi (JAMALI, Sumatra, Kalimantan, dll) | 3.698 |
| Tanpa tag voltage | 0 |
| Di bawah 70 kV (distribusi) | 2 |
| Bukan LineString valid | 0 |
| **Included** | **390** |

### Per voltage class

| Class | Lines | Length (km) | Warna |
|-------|------:|------------:|-------|
| 275 kV | 28 | 216 | `#9467bd` ungu |
| 150 kV | 320 | 4.225 | `#1f77b4` biru |
| 70 kV | 42 | 292 | `#2ca02c` hijau |
| **Total** | **390** | **4.733** | |

**150 kV mendominasi total** — 89% panjang (4.225 km). Backbone interkoneksi
Sulawesi memang 150 kV. **500 kV tidak ada** — Sulawesi belum punya jaringan
500 kV (sama seperti Kalimantan, berbeda dari JAMALI). **275 kV** muncul
lebih banyak dari Kalimantan: 28 ruas / 216 km — ini segmen-segmen backbone
275 kV Sulawesi (interkoneksi Sulbagsel–Sulbagut) yang sebagian sudah
energized; rata-rata ruasnya pendek (~8 km), khas backbone yang dibangun
bertahap segmen demi segmen.

### Per sub-sistem

| System | Lines | Length (km) |
|--------|------:|------------:|
| Sulutgo (Sulawesi Utara + Gorontalo) | 94 | 1.029 |
| Sulteng (Sulawesi Tengah) | 111 | 1.325 |
| Sulselrabar (Sulsel + Sultra + Sulbar) | 185 | 2.380 |

Sulselrabar punya jaringan transmisi terpanjang (2.380 km, 50% total) —
konsisten dengan posisinya sebagai sistem dengan pusat beban & pembangkitan
terbesar (koridor Makassar–Parepare–Palopo plus lengan tenggara). Sulteng
1.325 km cukup panjang untuk provinsi tunggal — wajar, jaringan Sulteng
membentang jauh karena backbone Sulawesi yang menghubungkan utara dan
selatan melintasinya. Sulutgo 1.029 km menjalar di sepanjang lengan utara
Gorontalo–Manado.

## Catatan ekstraksi

### Assignment sistem: bbox + centroid tiebreak

Tiga sub-sistem Sulawesi ada di satu pulau, jadi bbox-nya (union provinsi
penyusun) overlap di "pinggang" tengah pulau. Garis yang centroid-nya
jatuh di area overlap di-tiebreak ke sistem dengan centroid terdekat:

- **Sulutgo** centroid (0,90; 123,60) — tengah lengan utara.
- **Sulteng** centroid (−1,20; 121,00) — tengah Sulawesi Tengah.
- **Sulselrabar** centroid (−4,20; 120,20) — koridor Makassar–Parepare.

### Penjagaan bbox dua sisi

bbox region Sulawesi sengaja diberi batas di kedua ujung supaya tidak
menangkap jaringan region tetangga:

- `lon_min 118,50` — cukup menutup Sulawesi Barat (Mamuju) tapi berhenti
  sebelum Kalimantan Timur (infrastruktur paling timur ~lon 117,6).
  Selat Makassar di antaranya berupa laut, jadi tidak ada centroid garis
  yang jatuh di sana.
- `lon_max 127,00` — menutup Kepulauan Talaud (Sulawesi Utara) tapi
  berhenti sebelum Maluku Utara (Ternate ~lon 127,4).

Hasilnya: 3.698 ruas region lain ter-skip bersih, 0 kebocoran.

## Limitasi & batasan

- **Status line dari OSM** — `power=line` tidak membedakan eksisting vs
  konstruksi. Sebagian 275 kV kemungkinan masih tahap pembangunan.
- **Tegangan dari tag OSM** — kalau OSM salah tag, klasifikasi ikut salah.
- **Assignment sistem via centroid garis + tiebreak** — line panjang yang
  membentang lintas-sistem (mis. backbone 275 kV utara–selatan) bisa
  ke-assign ke salah satu sistem berdasar centroidnya; ini wajar untuk
  ruas yang memang menyambungkan dua sub-sistem.
- **Panjang via haversine** — jarak great-circle antar titik LineString.
- **Coverage OSM** transmisi Sulawesi setara Kalimantan (390 ruas /
  4.733 km vs Kalimantan 332 / 4.731 km), lebih tipis dari Jawa & Sumatra.
  Sebagian ruas 70 kV dan jaringan di lengan tenggara/timur kemungkinan
  belum di-tag — sebagian gap juga mencerminkan kondisi nyata (interkoneksi
  Sulawesi belum sepenuhnya tersambung penuh).

## Struktur kolom CSV

```
id              TRM-SLW-XXXX
system          Sulutgo / Sulteng / Sulselrabar
voltage_class   500 kV / 275 kV / 150 kV / 70 kV / lain
voltage_kv_max  tegangan tertinggi pada ruas (kV)
voltage_kv_all  semua tegangan pada ruas, dipisah ';'
length_km       panjang ruas via haversine (km, 3 desimal)
osm_id          OSM way ID
osm_voltage     tag voltage mentah dari OSM
source_id       'OSM-overpass'
```

GeoJSON menyimpan geometri LineString penuh plus properti `color` & `weight`
untuk rendering langsung di peta.

## Status Step 4 Sulawesi

Dengan transmisi ini, ketiga layer data Sulawesi lengkap:

| Layer | Hasil |
|-------|-------|
| Substations | 105 GI, 87,6% match rate |
| Generators | 101 plant, 3.795 MW |
| Transmission | 390 ruas, 4.733 km |

Langkah berikutnya: bundle `data_sulawesi.js` dan integrasi ke
`preview_indonesia.html` (combined map) untuk menutup Step 4.
