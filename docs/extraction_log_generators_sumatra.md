# Ekstraksi Pembangkit (Generators) Sumatra — Log

**Tanggal:** 2026-05-21 — extraction perdana
**Sumber utama:** OSM (Overpass API) — `data/geojson/indonesia_plants.geojson`
**Output:** `data/processed/generator_master_sumatra.csv`, `data/processed/generators_sumatra.geojson`
**Skrip:** `scripts/extract_sumatra_generators.py`

> Catatan ejaan: "Sumatra" = label region/sistem (English, lihat
> `docs/naming_conventions.md`). "Sumatera Utara/Barat/Selatan" tetap ejaan
> resmi BPS untuk nama administratif provinsi.

## Metodologi — beda dari substations

Extractor generator pakai pola yang **berbeda** dari extractor substations:

| Aspek | Substations | Generators |
|-------|-------------|------------|
| Sumber otoritatif | RUPTL (daftar GI) | OSM (`power=plant`) |
| Koordinat | dari OSM via fuzzy match / override | sudah ada di OSM |
| Fuzzy matching | ya | tidak perlu |
| Override CSV | ya | tidak (koordinat sudah presisi) |

Alasan: RUPTL tidak mendaftar pembangkit eksisting satu per satu dengan
koordinat — RUPTL hanya memberi agregat per jenis per provinsi. OSM, sebaliknya,
punya polygon `power=plant` individual dengan koordinat presisi. Jadi untuk
generators, OSM adalah sumber terbaik; extractor hanya **mengkategorikan tipe**
dan **meng-assign provinsi + sistem**.

## Ringkasan

**136 pembangkit** ter-extract di region Sumatra (dari ~600 plant OSM
se-Indonesia; 464 di luar region Sumatra di-skip). **103 punya data kapasitas**,
total **14.182 MW**.

### Per sistem listrik

| System | Plant (berkapasitas) | Total MW |
|--------|---------------------:|---------:|
| Sumatra (interkoneksi mainland) | 87 | 13.240 |
| Batam | 9 | 783 |
| Babel | 7 | 159 |
| **Total** | **103** | **14.182** |

### Per jenis pembangkit (sistem Sumatra mainland)

| Jenis | Count | Total MW |
|-------|------:|---------:|
| PLTU (batubara) | 23 | 6.331 |
| PLTA (hidro besar) | 22 | 2.803 |
| PLTP (panas bumi) | 8 | 1.163 |
| PLTGU (gas combined cycle) | 5 | 1.110 |
| PLTG (gas open cycle) | 9 | 1.065 |
| PLTMG (gas engine) | 3 | 409 |
| PLTD (diesel) | 9 | 140 |
| PLTS (surya) | 5 | 11 |
| PLTM (mini hidro) | 1 | 6 |
| Unknown | 2 | 202 |

PLTU mendominasi mix Sumatra (6,3 GW dari 13,2 GW ≈ 48%) — konsisten dengan
profil Sumatra yang batubara-heavy (mulut tambang Sumsel, Bukit Asam).

### Per provinsi (plant berkapasitas)

| Provinsi | Count | Total MW |
|----------|------:|---------:|
| Sumatera Utara | 22 | 3.514 |
| Sumatera Selatan | 16 | 3.548 |
| Lampung | 11 | 1.785 |
| Aceh | 11 | 1.573 |
| Riau | 11 | 1.057 |
| Sumatera Barat | 8 | 903 |
| Kepulauan Riau | 9 | 783 |
| Bengkulu | 6 | 496 |
| Jambi | 2 | 365 |
| Kep. Bangka Belitung | 7 | 159 |

## Assignment provinsi: bbox + centroid tiebreak

Karena OSM plant tidak punya tag provinsi, extractor meng-assign provinsi dari
koordinat. Provinsi nyata bukan persegi, jadi bbox per provinsi pasti overlap
di perbatasan.

**Bug yang ditemukan di iterasi pertama:** strategi awal "first bbox match
wins" menyebabkan plant ke-assign ke provinsi yang kebetulan dicek duluan.
Contoh: PLTU Ombilin (Sawahlunto, fisiknya jelas Sumatera Barat) jatuh di
bbox Riau **dan** bbox Sumatera Barat; karena Riau dicek lebih dulu, Ombilin
salah ter-label Riau. Empat plant Sumatera Barat (Ombilin, Teluk Sirih,
Singkarak, Maninjau) salah masuk Riau, plus beberapa salah-assign di
perbatasan Aceh/Sumut, Jambi, Sumsel/Bengkulu.

**Fix:** kalau sebuah plant jatuh di overlap >1 bbox, pilih provinsi yang
**centroid geografisnya paling dekat** ke titik plant (jarak Euclidean
lat/lon). Plant yang cuma match 1 bbox tidak terpengaruh — jadi fix ini hanya
bisa memperbaiki, tidak mungkin merusak assignment yang sudah benar.

Setelah fix: Sumatera Barat 4→8 plant, Riau 17→11, dan koreksi otomatis di
semua pasangan provinsi berbatasan. Total tetap 136 plant — hanya redistribusi.

Catatan: assignment **sistem** (Sumatra / Batam / Babel) jauh lebih robust
daripada assignment provinsi, karena Batam dan Babel adalah pulau yang
terpisah secara geografis — tidak ada overlap bbox dengan mainland.

## Review flags

OSM adalah data crowdsourced; kelengkapan tag bervariasi. Extractor menandai:

| Flag | Jumlah | Arti |
|------|-------:|------|
| `NO_NAME` | 10 | Plant tanpa tag `name` di OSM — tampil sebagai "(unnamed)" |
| `NO_CAPACITY` | 33 | Plant tanpa tag `plant:output:electricity` — kapasitas kosong |
| `NO_TYPE` | 17 | Tipe PLT tidak bisa diturunkan dari nama maupun `plant:source` |

33 dari 136 plant (24%) tidak punya data kapasitas. Ini batasan kualitas
data OSM, bukan bug extractor. 15 dari 17 plant `NO_TYPE` juga `NO_CAPACITY`
— korelasi yang masuk akal (plant dengan tag minim cenderung minim di semua
field).

## Limitasi & batasan

- **Kapasitas dari tag OSM**, bukan dari sumber resmi PLN. Bisa berupa nameplate
  capacity, bisa termasuk unit yang belum beroperasi penuh. Total 14,2 GW
  agak lebih tinggi dari kapasitas operasional sistem Sumatra (estimasi
  ~10–11 GW) — sebagian karena tag OSM optimistis. **Belum divalidasi silang
  dengan agregat RUPTL** (Lampiran A). Validasi ini kandidat untuk iterasi
  berikutnya.
- **24% plant tanpa kapasitas.** Total MW di atas hanya mencakup 103 plant
  berkapasitas. 33 plant lain ada di CSV tapi `capacity_mw` kosong.
- **Coverage OSM tidak lengkap.** Pembangkit kecil (PLTD pelosok, PLTMH) dan
  pembangkit baru sering belum di-tag di OSM. Coverage Babel & Batam (sistem
  isolated) lebih tipis.
- **Assignment provinsi via bbox + centroid** — akurat untuk mayoritas plant,
  tapi plant yang sangat dekat perbatasan provinsi bisa saja masih meleset.
  Assignment sistem (Sumatra/Batam/Babel) robust.

## Struktur kolom CSV

```
id              GEN-SMT-XXXX (unique ID, region Sumatra)
name            nama pembangkit dari OSM ('(unnamed)' jika tidak ada)
type            PLTU / PLTGU / PLTG / PLTA / PLTM / PLTMH / PLTP / PLTS /
                PLTB / PLTD / PLTMG / PLTSa / Unknown
capacity_mw     kapasitas MW (kosong jika tidak ada tag OSM)
province        provinsi (ejaan resmi BPS)
system          Sumatra / Batam / Babel
status          'existing' (OSM = kondisi terkini)
operator        operator dari tag OSM (bisa kosong)
method          plant:method dari OSM (combustion / water-storage / dll)
lat, lon        koordinat WGS84 (dari OSM, presisi)
osm_id          OSM way/relation/node ID
osm_source      plant:source dari OSM (coal/gas/hydro/geothermal/dll)
review_flag     NO_NAME / NO_CAPACITY / NO_TYPE (gabungan, dipisah ';')
source_id       'OSM-overpass'
```

## Reusability untuk Kalimantan & seterusnya

Pola extractor generator (`extract_sumatra_generators.py`) reusable:

1. Copy template, ganti `PROVINCES` list (nama, sistem, bbox) + `PROVINCE_CENTROIDS`.
2. Ganti `ID_PREFIX` dan path output.
3. Logika kategorisasi (`derive_type`, `SOURCE_MAP`, `parse_capacity_mw`) dan
   assignment (`assign_province` dengan centroid tiebreak) tidak perlu diubah.

Centroid tiebreak adalah fix yang generic — akan dibutuhkan di setiap region
karena provinsi di mana-mana bukan persegi.

## Kandidat iterasi berikutnya

1. **Validasi silang RUPTL.** Extract agregat pembangkit eksisting per jenis
   per provinsi dari RUPTL Lampiran A, bandingkan dengan total OSM. Ini akan
   mengkuantifikasi gap coverage OSM.
2. **Isi `capacity_mw` yang kosong** untuk 33 plant — via RUPTL, PLN Annual
   Report, atau GEM (Global Energy Monitor) wiki.
3. **Resolve `NO_TYPE`** untuk 17 plant — kemungkinan butuh inspeksi manual
   tag OSM atau sumber lain.
