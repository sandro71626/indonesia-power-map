# Ekstraksi Transmisi (Transmission) Kalimantan — Log

**Tanggal:** 2026-05-23 — extraction perdana
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_lines.geojson`
**Output:** `data/processed/transmission_master_kalimantan.csv`, `data/processed/transmission_kalimantan.geojson`
**Skrip:** `scripts/extract_kalimantan_transmission.py`

## Metodologi

Sama dengan extractor transmisi JAMALI & Sumatra: OSM `power=line` adalah
sumber otoritatif (punya geometri LineString). Extractor memfilter tegangan
transmisi (≥ 70 kV), menghitung panjang via haversine, mengkategorikan
voltage class, dan meng-assign sub-sistem listrik berdasar centroid garis.

Beda dengan Sumatra: ketiga sub-sistem Kalimantan ada di satu daratan dan
bersebelahan, jadi bbox-nya overlap. `assign_system` memakai centroid
tiebreak — kalau centroid garis masuk >1 bbox, dipilih sistem dengan
centroid terdekat (pola yang sama dengan extractor generator Kalimantan).

## Ringkasan

**332 ruas transmisi** ter-extract di region Kalimantan, total **4.731 km**.

### Skip breakdown

| Alasan skip | Jumlah |
|-------------|-------:|
| Di luar region Kalimantan (JAMALI, Sumatra, dll) | 3.757 |
| Tanpa tag voltage | 0 |
| Di bawah 70 kV (distribusi) | 1 |
| Bukan LineString valid | 0 |
| **Included** | **332** |

### Per voltage class

| Class | Lines | Length (km) | Warna |
|-------|------:|------------:|-------|
| 275 kV | 1 | 128 | `#9467bd` ungu |
| 150 kV | 329 | 4.552 | `#1f77b4` biru |
| 70 kV | 2 | 51 | `#2ca02c` hijau |
| **Total** | **332** | **4.731** | |

**150 kV mendominasi total** — 96% panjang (4.552 km). Backbone interkoneksi
Kalimantan memang 150 kV. **500 kV tidak ada** — Kalimantan belum punya
jaringan 500 kV (berbeda dari JAMALI). 275 kV cuma 1 ruas (128 km):
kemungkinan segmen backbone 275 kV Kalimantan yang sebagian besar masih
dalam konstruksi — perlu verifikasi status di iterasi berikutnya.

### Per sub-sistem

| System | Lines | Length (km) |
|--------|------:|------------:|
| Khatulistiwa (Kalimantan Barat) | 64 | 1.375 |
| Kalselteng (Kalteng + Kalsel) | 142 | 2.179 |
| Mahakam (Kaltim + Kaltara) | 126 | 1.177 |

Kalselteng punya jaringan transmisi terpanjang — konsisten dengan posisinya
sebagai sistem dengan pusat pembangkitan terbesar (kompleks PLTU Asam Asam)
dan permintaan terkonsentrasi di koridor Banjarmasin–Palangka Raya.

## Catatan: penyempitan bbox timur (perbaikan)

bbox sistem Mahakam semula `lon_max = 119,10` — kelewat jauh ke timur,
menyeberang Selat Makassar dan menangkap **2 ruas 150 kV Sulawesi Barat**
(area Mamuju) sebagai "Kalimantan". Setelah `lon_max` diperketat ke 118,50
(cukup menutup infrastruktur Kaltim paling timur yang hanya ~lon 117,6,
tapi berhenti sebelum Mamuju), kedua ruas itu dikeluarkan — 334 → 332 ruas,
4.768 → 4.731 km.

## Limitasi & batasan

- **Status line dari OSM** — `power=line` tidak membedakan eksisting vs
  konstruksi. 1 ruas 275 kV kemungkinan masih konstruksi.
- **Tegangan dari tag OSM** — kalau OSM salah tag, klasifikasi ikut salah.
- **Assignment sistem via centroid garis + tiebreak** — line panjang yang
  membentang lintas-sistem bisa salah assign; risiko kecil untuk Kalimantan.
- **Panjang via haversine** — jarak great-circle antar titik LineString.
- **Coverage OSM** transmisi Kalimantan lebih tipis dari Jawa/Sumatra
  (332 ruas / 4.731 km vs Sumatra 794 / 11.657 km) — sebagian 70 kV dan
  ruas baru kemungkinan belum di-tag. Beberapa gap di jaringan Mahakam
  (timur/timur laut) juga mencerminkan kondisi nyata: grid Kaltara masih
  muda dan interkoneksi Kaltim–Kaltara baru dibangun.

## Struktur kolom CSV

```
id              TRM-KLM-XXXX
system          Khatulistiwa / Kalselteng / Mahakam
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

## Status Step 3 Kalimantan

Dengan transmisi ini, ketiga layer data Kalimantan lengkap:

| Layer | Hasil |
|-------|-------|
| Substations | 100 GI, 85% match rate |
| Generators | 66 plant, 2.943 MW |
| Transmission | 332 ruas, 4.731 km |

Web visualization Kalimantan sudah terintegrasi ke `preview_indonesia.html`
(combined map), menutup Step 3.
