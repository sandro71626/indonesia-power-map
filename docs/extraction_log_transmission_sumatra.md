# Ekstraksi Transmisi (Transmission) Sumatra — Log

**Tanggal:** 2026-05-21 — extraction perdana
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_lines.geojson`
**Output:** `data/processed/transmission_master_sumatra.csv`, `data/processed/transmission_sumatra.geojson`
**Skrip:** `scripts/extract_sumatra_transmission.py`

> Catatan ejaan: "Sumatra" = label region/sistem (English, lihat
> `docs/naming_conventions.md`).

## Metodologi

Seperti extractor generator, extractor transmisi pakai **OSM sebagai sumber
otoritatif** — `power=line` punya geometri LineString lengkap. Tidak ada
fuzzy matching atau override. Extractor:

1. Filter feature `LineString` yang valid (≥ 2 titik).
2. Hitung centroid (rata-rata lat/lon) → assign ke sistem (Sumatra / Batam /
   Babel) via bbox; line yang centroid-nya di luar region Sumatra di-skip.
3. Filter tegangan: hanya transmisi **≥ 70 kV** (exclude distribusi 20 kV).
4. Hitung panjang via formula haversine.
5. Kategorikan voltage class + assign warna/weight untuk rendering peta.

## Ringkasan

**794 ruas transmisi** ter-extract di region Sumatra, total **11.657 km**.

### Skip breakdown

| Alasan skip | Jumlah |
|-------------|-------:|
| Di luar region Sumatra (JAMALI, Kalimantan, dll) | 3.289 |
| Tanpa tag voltage | 0 |
| Di bawah 70 kV (distribusi) | 7 |
| Bukan LineString valid | 0 |
| **Included** | **794** |

Catatan: 0 line tanpa tag voltage — dataset `indonesia_lines.geojson`
tampaknya sudah di-query dari Overpass dengan filter voltage, jadi semua
feature punya tag tegangan.

### Per voltage class

| Class | Lines | Length (km) | Warna |
|-------|------:|------------:|-------|
| 500 kV | 10 | 403 | `#d62728` merah |
| 275 kV | 115 | 2.610 | `#9467bd` ungu |
| 150 kV | 649 | 8.261 | `#1f77b4` biru |
| 70 kV | 20 | 384 | `#2ca02c` hijau |
| **Total** | **794** | **11.657** | |

150 kV mendominasi (8.261 km, 71% panjang) — jaringan sub-transmisi utama.
275 kV (2.610 km) adalah backbone interkoneksi Sumatra.

### Per sistem

| System | Lines | Length (km) |
|--------|------:|------------:|
| Sumatra (interkoneksi mainland) | 714 | 11.176 |
| Batam | 63 | 167 |
| Babel | 17 | 314 |

Batam punya 63 ruas tapi cuma 167 km — jaringan padat-pendek khas pulau
industri. Babel 17 ruas / 314 km tersebar di Bangka & Belitung.

## Catatan: 10 ruas 500 kV

OSM menandai 10 ruas di Sumatra dengan `voltage=500000` (total 403 km).
**Backbone interkoneksi Sumatra yang sudah established adalah 275 kV** —
500 kV adalah proyek upgrade yang sebagian masih konstruksi.

Verifikasi 2 ruas terpanjang (yang menyumbang ~400 dari 403 km):

- **way/736595654** (241 km) — mulai di (103,54°E, −1,69°S), Jambi bagian
  tengah. Unnamed.
- **way/1186182644** (159 km) — mulai di (102,03°E, −0,50°S), perbatasan
  Riau–Jambi–Sumatera Barat. Unnamed.

Keduanya jelas berada di mainland Sumatra (jauh dari Jawa), jadi **bukan
line JAMALI yang bocor** — assignment extractor sudah benar. 8 ruas sisanya
adalah stub pendek (< 0,5 km) di area yang sama, kemungkinan segmen
konektor di dekat gardu.

**Interpretasi:** kemungkinan besar ini segmen **backbone 500 kV Sumatra**
yang sedang dibangun PLN. OSM menandainya `power=line` biasa tanpa status
`construction`/`proposed`, jadi di output extractor ruas ini muncul sebagai
"existing". Status energize sebenarnya tidak bisa dipastikan dari tag OSM.
Untuk peta publik, ini perlu disclaimer — atau di iterasi berikutnya,
cross-check dengan RUPTL untuk menandai mana yang sudah COD vs konstruksi.

## Limitasi & batasan

- **Status line dari OSM** — `power=line` tidak selalu membedakan eksisting
  vs konstruksi vs rencana. 10 ruas 500 kV kemungkinan masih konstruksi
  (lihat di atas). Selebihnya (275/150/70 kV) diasumsikan eksisting.
- **Tegangan dari tag OSM** — kalau OSM salah tag, klasifikasi ikut salah.
  Tidak ada cross-check dengan sumber lain di iterasi ini.
- **Assignment sistem via centroid** — line yang sangat panjang dan
  membentang melewati batas sistem bisa salah assign. Untuk region Sumatra
  ini risiko kecil karena Batam & Babel adalah pulau terpisah; line tidak
  menyeberang laut antar-sistem.
- **Panjang via haversine** — jarak great-circle antar titik LineString.
  Akurat untuk ruas transmisi; sedikit under-estimate untuk line yang
  banyak belokan dengan titik jarang.
- **Coverage OSM** — line transmisi di OSM Indonesia cukup lengkap untuk
  150 kV ke atas, tapi 70 kV dan segmen baru bisa missing.

## Struktur kolom CSV

```
id              TRM-SMT-XXXX (unique ID, region Sumatra)
system          Sumatra / Batam / Babel
voltage_class   500 kV / 275 kV / 150 kV / 70 kV / lain
voltage_kv_max  tegangan tertinggi pada ruas (kV)
voltage_kv_all  semua tegangan pada ruas, dipisah ';' (mis. '275;150')
length_km       panjang ruas via haversine (km, 3 desimal)
osm_id          OSM way ID
osm_voltage     tag voltage mentah dari OSM (Volt)
source_id       'OSM-overpass'
```

GeoJSON menyimpan geometri LineString penuh plus properti `color` dan
`weight` untuk rendering langsung di peta (Leaflet).

## Reusability untuk Kalimantan & seterusnya

Extractor (`extract_sumatra_transmission.py`) reusable:

1. Copy template, ganti `SYSTEMS` list (nama sistem + bbox region).
2. Ganti `ID_PREFIX` dan path output.
3. Logika `parse_voltages_kv`, `haversine_km`, `voltage_class` tidak perlu
   diubah — generic untuk semua region.

`voltage_class` sudah menyertakan rule 500 kV (walau Sumatra hampir tidak
punya) supaya forward-compatible dengan JAMALI dan region lain.

## Kandidat iterasi berikutnya

1. **Bedakan eksisting vs konstruksi** untuk 10 ruas 500 kV — cross-check
   RUPTL atau tag OSM `construction:power`.
2. **Validasi total panjang** per voltage class terhadap statistik PLN
   (Statistik PLN punya angka panjang transmisi per region).
3. **Web bundle** — gabungkan substations + generators + transmission
   Sumatra ke `web/data_sumatra.js` dan bikin `preview_sumatra.html`,
   menutup Step 2.
