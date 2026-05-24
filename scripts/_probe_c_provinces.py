"""
Probe lanjutan: identifikasi provinsi tiap tabel Lampiran C (C1-C12) RUPTL.

Heading tabel C tidak memuat nama provinsi. Probe ini mengekstrak beberapa
baris GI pertama tiap tabel — nama GI (kota/kabupaten) mengungkap provinsi.
Dipakai untuk memetakan C1..C12 -> provinsi sebelum menulis extractor
regional Sulawesi / Maluku-Papua / Nusa Tenggara.

Pakai:
    python3 scripts/_probe_c_provinces.py

Skrip scratchpad — prefix '_'.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"

# (table_id, start_page, end_page) — diturunkan dari _probe_ruptl_tables.py.
C_TABLES = [
    ("C1",  955,  972), ("C2",  973,  991), ("C3",  992, 1004),
    ("C4", 1005, 1030), ("C5", 1031, 1050), ("C6", 1051, 1062),
    ("C7", 1063, 1087), ("C8", 1088, 1110), ("C9", 1111, 1134),
    ("C10", 1135, 1152), ("C11", 1153, 1169), ("C12", 1170, 1253),
]

HEADING = r'Tabel\s+C{num}\.(\d+)\.?\s*(?:Realisasi\s+)?Kapasitas\s+Trafo\s+Gardu\s+Induk[^\n]*\n'
ROW = re.compile(r'^\s*(\d{1,3})\s+(.+?)\s+(\d{2,3}\s*/\s*\d{2,3})\s+(\d+)\s+([\d\.,]+)\s*$')


def main():
    print("Identifikasi provinsi per tabel Lampiran C")
    print("(nama GI pertama tiap tabel)\n")
    for tid, start, end in C_TABLES:
        out = subprocess.run(
            ['pdftotext', '-layout', '-f', str(start), '-l', str(end), str(PDF), '-'],
            capture_output=True, text=True
        ).stdout
        num = tid[1:]
        h = re.search(HEADING.format(num=num), out)
        names = []
        if h:
            for line in out[h.end():].split('\n'):
                m = ROW.match(line.rstrip())
                if m:
                    names.append(m.group(2).strip())
                if len(names) >= 8:
                    break
        label = ', '.join(names) if names else '(tidak ada baris ter-parse)'
        print(f"  {tid:<4} (p{start}): {label}")


if __name__ == '__main__':
    main()
