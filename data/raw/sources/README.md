# Sumber Dokumen PDF

Folder ini berisi dokumen publik PDF yang dipakai sebagai input pipeline ekstraksi.
**PDF tidak di-commit ke repo** karena ukurannya besar (~184 MB total) dan untuk
menjaga keterhubungan langsung ke sumber resmi. Untuk reproduksi pipeline,
download manual dari sumber asli dan letakkan di folder ini.

## Daftar dokumen

| File yang diharapkan | Sumber asli | Status | Catatan |
|----------------------|-------------|--------|---------|
| `RUPTL-2025-2034.pdf` | PT PLN (Persero), via Kementerian ESDM | Dokumen publik | Lampiran Keputusan Menteri ESDM No. 188.K/TL.03/MEM.L/2025 (26 Mei 2025) |
| `Statistik-PLN-2024.pdf` | PT PLN (Persero), Statistik PLN 2024 (revisi tabel 28 & 60) | Dokumen publik | ISSN 0852-8179, No. 01001-300625 |
| `Statistik-PLN-2025-Unaudited.pdf` | PT PLN (Persero), Statistik PLN 2025 (Unaudited) | Dokumen publik | Untuk validasi tren — masih unaudited |
| `AnnualReport-PLN-2024.pdf` | PT PLN (Persero), Annual Report 2024 | Dokumen publik | High-resolution edition |
| `HEESI-2024.pdf` | Kementerian ESDM RI, Handbook of Energy and Economic Statistics of Indonesia 2024 | Dokumen publik | Untuk validasi konsumsi energi nasional |

## Cara download

### 1. RUPTL PLN 2025–2034
- **Sumber resmi:** Website Kementerian ESDM atau PT PLN
  - Coba: <https://gatrik.esdm.go.id/> (Direktorat Jenderal Ketenagalistrikan)
  - Atau: <https://web.pln.co.id/> → publikasi → RUPTL
- **Search keyword:** "RUPTL PLN 2025-2034" atau Kepmen ESDM "188.K/TL.03/MEM.L/2025"
- **Ukuran perkiraan:** ~52 MB
- **Format file di repo:** `data/raw/sources/RUPTL-2025-2034.pdf`

### 2. Statistik PLN 2024 & 2025
- **Sumber resmi:** <https://web.pln.co.id/> → Hubungan Investor → Publikasi → Statistik PLN
- **Search keyword:** "Statistik PLN 2024" / "Statistik PLN 2025"
- **Ukuran perkiraan:** ~8 MB masing-masing
- **Format file di repo:**
  - `data/raw/sources/Statistik-PLN-2024.pdf`
  - `data/raw/sources/Statistik-PLN-2025-Unaudited.pdf`

### 3. Annual Report PLN 2024
- **Sumber resmi:** <https://web.pln.co.id/> → Hubungan Investor → Laporan Tahunan
- **Search keyword:** "Annual Report PLN 2024" atau "Laporan Tahunan PLN 2024"
- **Ukuran perkiraan:** ~100 MB (Hi-Res version)
- **Format file di repo:** `data/raw/sources/AnnualReport-PLN-2024.pdf`

### 4. HEESI 2024
- **Sumber resmi:** Kementerian ESDM
  - Coba: <https://www.esdm.go.id/en/publication/handbook-of-energy-economic-statistics-of-indonesia>
- **Search keyword:** "Handbook Energy Economic Statistics Indonesia 2024"
- **Ukuran perkiraan:** ~15 MB
- **Format file di repo:** `data/raw/sources/HEESI-2024.pdf`

## Catatan hukum

Semua dokumen di atas adalah **dokumen publik** dari institusi resmi pemerintah dan
BUMN. Penggunaan untuk **edukasi, riset, dan analisis kebijakan** umumnya tidak
memerlukan izin khusus, namun tetap mengikuti prinsip atribusi.

Repo ini tidak melakukan redistribusi PDF asli. Yang di-commit ke repo adalah
**data turunan/agregat** hasil ekstraksi (lihat `data/processed/`), yang merupakan
hasil olahan original dari Sandro Agassi.

## Verifikasi tanggal akses

Kalau lo download dokumen sekarang dan ingin merekam tanggalnya untuk reproducibility,
edit file ini dan tambahkan tanggal akses di kolom catatan. Contoh:

```markdown
| RUPTL-2025-2034.pdf | ... | Dokumen publik | Diakses 2026-05-10 oleh @sandroagassi |
```
