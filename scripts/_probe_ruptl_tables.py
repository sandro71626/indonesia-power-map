"""
Probe RUPTL PDF: cari semua heading tabel "Gardu Induk Eksisting" per provinsi
beserta nomor halamannya.

Menangkap kedua format heading yang dipakai RUPTL:
  - Lampiran A (Sumatra, Kalimantan): "Tabel A1.4. Realisasi Kapasitas
    Trafo Gardu Induk"
  - Lampiran B (JAMALI): "Tabel B1.4 Realisasi Kapasitas Gardu Induk
    Eksisting"

Dipakai untuk discover posisi tabel region baru (Sulawesi, Maluku-Papua,
Nusa Tenggara). Run sekali, output dipakai untuk populate PROVINCES list
di extractor regional.

Pakai:
    python3 scripts/_probe_ruptl_tables.py

Skrip scratchpad — prefix '_' membedakannya dari extractor yang shipped.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"

# Heading tabel GI eksisting per provinsi. Membidik dua kata kunci yang
# spesifik untuk tabel eksisting — "Trafo Gardu Induk" (format Lampiran A)
# atau "Gardu Induk Eksisting" (format Lampiran B). Tabel rencana
# ("Rencana Pembangunan Gardu Induk") tidak ikut tertangkap.
HEADING_RE = re.compile(
    r'Tabel\s+([A-Z]\d+)\.(\d+)\.?\s*[^\n]{0,60}?'
    r'(?:Trafo Gardu Induk|Gardu Induk Eksisting)[^\n]*'
)


def main():
    print(f"Scanning {PDF.name}... (~30 detik)")
    out = subprocess.run(['pdftotext', '-layout', str(PDF), '-'],
                         capture_output=True, text=True).stdout
    pages = out.split('\f')  # form feed = pemisah halaman
    print(f"Total pages: {len(pages)}\n")

    print(f"{'Page':>5}  Heading")
    print(f"{'-' * 5}  {'-' * 72}")
    found = []
    for idx, page_text in enumerate(pages):
        page_num = idx + 1
        for m in HEADING_RE.finditer(page_text):
            disp = re.sub(r'\s+', ' ', m.group(0)).strip()[:92]
            print(f"{page_num:>5}  {disp}")
            found.append((page_num, m.group(1)))

    if not found:
        print("  (tidak ada heading ditemukan)")
        return

    # Ringkasan per Lampiran (A, B, C, ...)
    by_lampiran = {}
    for page, tid in found:
        by_lampiran.setdefault(tid[0], []).append((page, tid))
    print("\nRingkasan per Lampiran:")
    for prefix in sorted(by_lampiran):
        rows = by_lampiran[prefix]
        tids = sorted(set(r[1] for r in rows), key=lambda t: int(t[1:]))
        p0 = min(r[0] for r in rows)
        p1 = max(r[0] for r in rows)
        print(f"  Lampiran {prefix}: {len(tids)} tabel "
              f"({', '.join(tids)}) — page {p0}..{p1}")


if __name__ == '__main__':
    main()
