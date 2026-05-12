# Design Decisions — Indonesia Power Map

Catatan singkat keputusan desain yang udah final, biar konsisten di setiap iterasi.

---

## 1. Basemap default: Carto Positron

**Keputusan:** Pakai **Carto Positron** (`https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`) sebagai peta dasar utama.

**Alasan:**
- Warna abu-abu lembut — ga kompetisi sama layer kelistrikan (warna pembangkit/transmisi/GI tetap menonjol).
- Tetap ada label kota dan provinsi tipis — penting untuk audiens **orang awam** supaya bisa identifikasi "daerah mana, ada apa aja".
- Free, no API key, attribution sederhana (© OSM, © CARTO).
- Sudah jadi standar industri untuk peta data viz.

**Beda filosofi vs OpenInfraMap:** OpenInfraMap pakai basemap minimal karena audiensnya power engineer (udah hafal peta). Indonesia Power Map menargetkan audiens yang lebih luas (mahasiswa, peneliti, media, publik teknis), jadi konteks geografis perlu cukup terbaca.

**Alternatif yang akan tetap di-bundle (sebagai opsi switcher):**
- Carto Positron (no labels) — buat user yang mau super clean.
- Carto Voyager — sedikit lebih informatif.
- Carto Dark Matter — mode malam, dramatic.
- OSM Standar — fallback kalau user mau full info.

Untuk Step 2 nanti, akan ditambah:
- Esri WorldImagery (satellite) — untuk konteks fisik pembangkit hidro & lokasi industri.

## 2. Filosofi visual (general)

- **Basemap = kanvas yang ngalah.** Tipis, ga kompetisi.
- **Layer kelistrikan = thick.** Warna jelas, marker ukuran proporsional ke kapasitas, popup detail saat klik.
- **Hierarki visual:** zoom out → cuma struktur besar; zoom in → label dan detail muncul.

## 3. Color palette layer kelistrikan

Tegangan Gardu Induk / Transmisi:
- 500 kV → `#d62728` (merah) — tegangan ekstra tinggi (GITET / backbone transmisi)
- 275 kV → `#9467bd` (ungu) — interkoneksi besar (Sumatera/Sulawesi)
- 150 kV → `#1f77b4` (biru) — backbone
- 70 kV → `#2ca02c` (hijau) — sub-transmisi
- < 70 kV → `#999` (abu-abu) — fallback

Jenis pembangkit:
- PLTU (batubara) → `#3a3a3a` (hitam keabuan)
- PLTGU (gas combined cycle) → `#ff7f0e` (oranye)
- PLTG (gas open cycle) → `#ffbb78` (oranye muda)
- PLTA (hidro besar) → `#1f77b4` (biru)
- PLTM/PLTMH (mini/micro hidro) → `#76b7e1` (biru muda)
- PLTP (panas bumi) → `#d62728` (merah)
- PLTS (surya) → `#f7d100` (kuning)
- PLTB (angin) → `#17becf` (cyan)
- PLTD (diesel) → `#8c564b` (coklat)
- PLTMG (gas engine) → `#c49c94` (coklat muda)
- PLTSa (sampah) → `#8b4513` (coklat tua)
- Unknown → `#999` (abu-abu)

## 4. Simbol marker — mengikuti konvensi Single Line Diagram (SLD)

**Keputusan:** Pakai simbol yang mengikuti konvensi single line diagram IEC/ANSI,
modifikasi agar tetap readable di peta interaktif.

Mapping:
- **Pembangkit** → **lingkaran** (SLD: generator) dengan label jenis di tengah
  (U / GU / G / A / M / P / S / B / D / Sa). Ukuran ∝ kapasitas MW (8 tier:
  <10 / <50 / <200 / <500 / <1000 / <2000 / ≥2000).
- **Gardu Induk** → **kotak** (SLD: substation). Color by tegangan max.
  Ukuran ∝ √(kapasitas MVA).
- **GITET (500 kV)** → **kotak dengan border ganda** (outline + body), visual
  differentiator dari GI biasa, sesuai konvensi SLD untuk busbar tegangan ekstra tinggi.
- **Transmisi** → **garis berwarna** by tegangan, ketebalan ∝ tegangan
  (500 kV paling tebal). Sudah sesuai konvensi SLD.

**Alasan pilihan ini vs full-icon (foto turbin, panel surya, dll):**
- SLD adalah bahasa visual standar di industri listrik. Engineer/teknisi langsung paham.
- Untuk orang awam, perbedaan circle vs square cukup intuitif (mirip "node titik" vs
  "fasilitas kotak") dan label dalam circle membantu identifikasi jenis tanpa harus
  buka legenda.
- Lebih cepat di-render daripada SVG icon kompleks (penting karena ada 700+ marker).
- Konsisten dengan diagram listrik di RUPTL, Annual Report, dan tools internal.

## 5. Catatan penamaan GITET di RUPTL

**Issue yang ditemukan:** Beberapa GITET (500 kV) yang dikenal publik (mis.
"GITET Bekasi") **tidak tercatat dengan nama yang sama** di RUPTL Tabel Bx.4.

**Penjelasan:** RUPTL kemungkinan mendaftar GITET dengan nama desa/kecamatan
administratif terdekat. Contoh area Bekasi-Cikarang (Jawa Barat) yang tercatat:
- GITET Cibatu (2.000 MVA)
- GITET Deltamas (1.000 MVA)
- GISTET 500kV New Tambun (1.000 MVA)
- GISTET 500kV Sukatani (1.000 MVA)

Sedangkan "GITET Bekasi" yang umum disebut publik dan ada di OSM (lat -6.20, lon 106.98)
tidak ditemukan dengan nama itu di Tabel Bx.4.

**Implikasi & action:**
- Untuk iterasi sekarang, dokumentasikan gap ini di disclaimer modal (sudah).
- Untuk iterasi berikut: pertimbangkan augmentasi data dengan referensi silang OSM
  untuk GITET yang tidak ke-match by nama (manual mapping nama RUPTL ↔ nama publik).

## 6. Disclaimer & polish

- **First-load modal** menampilkan disclaimer + sumber data + konvensi simbol.
  Modal bisa di-trigger ulang via tombol "ℹ Sumber data &amp; tentang peta" di
  sidebar atau link di footer.
- **Footer permanen** menampilkan attribution singkat plus link ke modal detail.
- **Mobile responsive**: sidebar collapse-able, modal scrollable, font sizes adaptif
  via media query @600px.
