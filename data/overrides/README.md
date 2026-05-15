# Manual Coordinate Overrides

Folder ini berisi **override CSV** untuk pasangan (nama RUPTL ↔ koordinat) yang tidak bisa diselesaikan oleh fuzzy match otomatis di extractor. Override mechanism ini **reusable** untuk semua region (Jamali, Sumatera, Kalimantan, Sulawesi, dst).

## File

- **`substation_overrides.csv`** — Override untuk Gardu Induk (GI).
  Ke depan, file sejenis bisa ditambah: `generator_overrides.csv`, `transmission_overrides.csv`.

## Kapan override diperlukan

Berdasarkan iterasi pertama (Jamali, Mei 2026), ada 3 jenis kasus yang fuzzy match tidak bisa selesaikan sendiri:

1. **Nama RUPTL = nama administratif desa, nama OSM = nama publik/historis.**
   Contoh: RUPTL "Karangkates" (Jawa Timur) ↔ OSM "PLTA Sutami" — keduanya merujuk bendungan yang sama.

2. **GI step-up tidak ditag sebagai `power=substation` di OSM, tapi ada di dalam polygon `power=plant`.**
   Contoh: GI Suralaya tidak punya entri substation tersendiri, tapi ko-lokasi dengan polygon PLTU Suralaya. Override menunjuk ke centroid plant.

3. **Perbedaan ejaan/spacing yang fuzzy match score di bawah threshold.**
   Contoh: RUPTL "Tanjungawarawar" ↔ OSM "Tanjung Awar-Awar".

## Schema CSV

| Kolom | Wajib | Deskripsi |
|-------|:-----:|-----------|
| `ruptl_name` | ✓ | Nama GI persis seperti tertulis di RUPTL (case-sensitive). |
| `province` | ✓ | Provinsi (DKI Jakarta / Banten / Jawa Barat / Jawa Tengah / DIY / Jawa Timur / Bali / dst). |
| `coord_source` | ✓ | Sumber koordinat: `osm_plant` (centroid polygon `power=plant`), `osm_substation` (entri OSM substation dengan nama berbeda), `manual` (sumber publik di luar OSM, e.g. PLN annual report). |
| `osm_id` |  | OSM way/relation/node ID jika sumbernya OSM (kosong jika manual). |
| `osm_name` |  | Nama persis di OSM. |
| `lat`, `lon` | ✓ | Koordinat WGS84. |
| `verified_date` | ✓ | Tanggal verifikasi (YYYY-MM-DD). |
| `notes` | ✓ | Penjelasan rasional kenapa override ini valid. |

## Aturan match

Extractor mencari override berdasarkan **pasangan (ruptl_name, province)**. Kalau sebuah baris RUPTL match dengan override, baris itu langsung dapat koordinat dari override dan **fuzzy match di-skip** untuk baris tersebut. Status `review_flag` jadi kosong, dan kolom `match_source` di output CSV jadi `override` (vs `osm_fuzzy` untuk yang diselesaikan oleh fuzzy match).

Override bisa apply ke beberapa baris RUPTL kalau ada GI dengan nama sama di provinsi sama tapi voltage berbeda — keduanya share koordinat (e.g. Suralaya 150/20 & Suralaya 500/150 sama-sama dapat lokasi PLTU Suralaya).

## Cara menambah override baru

1. Buka issue / dokumentasikan GI yang `UNMATCHED` di extraction log.
2. Cari sumber otoritatif (OSM, RUPTL lampiran lain, PLN Annual Report, paper akademik).
3. Tambah baris baru ke `substation_overrides.csv` dengan semua kolom terisi.
4. Re-run extractor (`python3 scripts/extract_jamali_substations.py`).
5. Update extraction log dengan hasil baru.

## Prinsip

- **Conservative bias.** Override hanya untuk kasus yang sumbernya verifiable. Jangan tambahkan koordinat dari "intuisi" — selalu trace ke sumber yang bisa dicek ulang.
- **Reproducible.** Tiap override punya `osm_id` atau `notes` dengan sumber yang jelas. Pembaca lain harus bisa konfirmasi sendiri.
- **Transparent.** Output CSV punya kolom `match_source` agar konsumen data tahu mana yang via fuzzy match vs manual.
