"""
Probe RUPTL PDF: cari semua heading 'Tabel X<n>.<m> ... Gardu Induk Eksisting'
beserta nomor halamannya.

Tujuan: discover page range per provinsi untuk extractor regional baru
(Sumatera, Kalimantan, Sulawesi, dst). Run sekali, output dipakai untuk
populate PROVINCES list di extractor.

Skrip ini scratchpad — nama prefix '_' biar gampang dibedakan dari extractor
yang shipped. Boleh dihapus atau di-keep sebagai utility.

Pakai:
    python3 scripts/_probe_ruptl_tables.py

Output kira-kira:
    Page  Heading
    ----  -------
      45  Tabel A1.4 Kapasitas Gardu Induk Eksisting Provinsi Aceh
      67  Tabel A2.4 Kapasitas Gardu Induk Eksisting Provinsi Sumut
      ...
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"

# Tiga pattern berbeda untuk catching variasi heading di RUPTL:
PATTERNS = [
    # 1. Strict: Tabel X<n>.<m> ... Kapasitas Gardu Induk Eksisting (yang dipakai JAMALI)
    ('strict_kapasitas_eksisting',
     re.compile(r'Tabel\s+([A-Z]\d+)\.(\d+)\.?\s*(?:Realisasi\s+)?Kapasitas\s+Gardu\s+Induk\s+Eksisting[^\n]*')),
    # 2. Mid: Tabel X<n>.<m> apapun yang ada "Gardu Induk" (lebih luas)
    ('any_tabel_gardu_induk',
     re.compile(r'Tabel\s+([A-Z]?\d+)\.?(\d*)\.?\s*[^\n]*Gardu\s+Induk[^\n]*')),
    # 3. Province name mentions (cari section header Sumatera)
    ('sumatera_section_header',
     re.compile(r'(?:Sistem|Wilayah|Provinsi|Lampiran)\s+[^\n]{0,100}(?:Sumatera|Aceh|Sumatera Utara|Sumatera Selatan|Riau|Lampung|Bengkulu|Jambi|Bangka)[^\n]*')),
]


def scan_with_pattern(pages, label, pattern):
    print(f"\n=== Pattern: {label} ===")
    print(f"{'Page':>5}  Match")
    print(f"{'-'*5}  {'-'*70}")
    hits = 0
    seen = set()
    for idx, page_text in enumerate(pages):
        page_num = idx + 1
        for m in pattern.finditer(page_text):
            display = re.sub(r'\s+', ' ', m.group(0)).strip()[:90]
            key = (page_num, display)
            if key in seen:
                continue
            seen.add(key)
            print(f"{page_num:>5}  {display}")
            hits += 1
            if hits >= 100:
                print(f"  ... (truncated at 100 hits)")
                return
    if hits == 0:
        print("  (no match)")


def main():
    print(f"Scanning {PDF.name}... (~30 detik)")
    out = subprocess.run(
        ['pdftotext', '-layout', str(PDF), '-'],
        capture_output=True, text=True
    ).stdout
    pages = out.split('\f')
    print(f"Total pages: {len(pages)}")

    for label, pat in PATTERNS:
        scan_with_pattern(pages, label, pat)


if __name__ == '__main__':
    main()
