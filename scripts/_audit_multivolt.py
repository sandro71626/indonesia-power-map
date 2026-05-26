"""
AUDIT: deteksi GI multi-tegangan yang ter-lewat / under-count oleh parser
substation LAMA (single-line) di region JAMALI / Sumatra / Kalimantan /
Sulawesi.

Latar belakang: tabel "Realisasi Kapasitas Trafo Gardu Induk" RUPTL bisa
memakai layout MULTI-TEGANGAN — satu GI membentang beberapa baris (satu per
level tegangan trafo), nama GI di baris tengah blok (kadang tanpa data).
Ditemukan saat ekstraksi Maluku/Papua (Step 5). Parser lama (satu baris =
satu GI) bisa: (a) melewatkan GI yang baris namanya tanpa data, dan (b)
under-count trafo/kapasitas GI multi-tegangan.

Skrip ini TIDAK mengubah file apa pun — cuma membandingkan parser LAMA vs
parser BARU (multi-tegangan) per tabel dan melaporkan selisih.

Pakai:
    python3 scripts/_audit_multivolt.py

Scratchpad — prefix '_'.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"

# (region, table_id, start_page, end_page) — dari PROVINCES tiap extractor.
TABLES = [
    ("JAMALI", "B1", 812, 823), ("JAMALI", "B2", 824, 840),
    ("JAMALI", "B3", 841, 873), ("JAMALI", "B4", 874, 897),
    ("JAMALI", "B5", 898, 904), ("JAMALI", "B6", 905, 937),
    ("JAMALI", "B7", 938, 950),
    ("Sumatra", "A1", 601, 616), ("Sumatra", "A2", 617, 632),
    ("Sumatra", "A3", 633, 645), ("Sumatra", "A4", 646, 658),
    ("Sumatra", "A5", 659, 669), ("Sumatra", "A6", 670, 680),
    ("Sumatra", "A7", 681, 691), ("Sumatra", "A8", 692, 704),
    ("Sumatra", "A9", 705, 715), ("Sumatra", "A10", 716, 729),
    ("Kalimantan", "A11", 730, 745), ("Kalimantan", "A12", 746, 759),
    ("Kalimantan", "A13", 760, 774), ("Kalimantan", "A14", 775, 797),
    ("Kalimantan", "A15", 798, 813),
    ("Sulawesi", "C1", 955, 972), ("Sulawesi", "C2", 973, 991),
    ("Sulawesi", "C3", 992, 1004), ("Sulawesi", "C4", 1005, 1030),
    ("Sulawesi", "C5", 1031, 1050), ("Sulawesi", "C6", 1051, 1062),
    # Kontrol — Maluku/Papua sudah pakai parser baru; old harus < new.
    ("Maluku-Papua", "C7", 1063, 1087), ("Maluku-Papua", "C8", 1088, 1110),
    ("Maluku-Papua", "C9", 1111, 1134), ("Maluku-Papua", "C10", 1135, 1152),
]


def pdftext(start, end):
    return subprocess.run(
        ['pdftotext', '-layout', '-f', str(start), '-l', str(end), str(PDF), '-'],
        capture_output=True, text=True).stdout


def get_block(out, table_id):
    """Ambil teks tabel GI eksisting (heading -> tabel berikutnya)."""
    prefix, num = table_id[0], table_id[1:]
    heading = re.compile(
        rf'Tabel\s+{prefix}{num}\.(\d+)\.?\s*(?:Realisasi\s+)?'
        rf'Kapasitas\s+(?:Trafo\s+)?Gardu\s+Induk(?:\s+Eksisting)?[^\n]*\n')
    m = heading.search(out)
    if not m:
        return None
    sub = int(m.group(1))
    end_m = re.compile(rf'Tabel\s+{prefix}{num}\.{sub + 1}\b').search(out, m.end())
    return out[m.end():end_m.start() if end_m else len(out)]


def _skip(s):
    if not s.strip():
        return True
    if 'Tegangan' in s or 'Total Kapasitas' in s or 'Jumlah Trafo' in s or 'Nama GI' in s:
        return True
    if re.match(r'^\s*[A-C]\s*-?\s*\d+\s*$', s):
        return True
    if re.search(r'^\s*(Total|Jumlah)\b', s, re.IGNORECASE):
        return True
    return False


def to_cap(s):
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


# --- Parser LAMA: satu baris = satu GI ---
OLD_ROW = re.compile(
    r'^\s*(\d{1,3})\s+(.+?)\s+(\d{2,3}\s*/\s*\d{2,3})\s+(\d+)\s+([\d.,]+)\s*$')


def parse_old(block):
    gis = []
    for line in block.split('\n'):
        s = line.rstrip()
        if _skip(s):
            continue
        m = OLD_ROW.match(s)
        if m:
            gis.append({'name': m.group(2).strip(),
                        'trafo': int(m.group(4)),
                        'cap': to_cap(m.group(5))})
    return gis


# --- Parser BARU: multi-tegangan, grup VOLT simetris di sekitar NAME ---
VOLT = r'(\d{2,3})\s*/\s*(\d{2,3})\s+(\d+)\s+([\d.,]+)'
VOLT_ONLY = re.compile(rf'^\s*{VOLT}\s*$')
NAME_DATA = re.compile(rf'^\s*(\d{{1,3}})\s+(.+?)\s+{VOLT}\s*$')
NAME_ONLY = re.compile(r'^\s*(\d{1,3})\s+([A-Za-z(].*?)\s*$')


def parse_new(block):
    entries = []
    for line in block.split('\n'):
        s = line.rstrip()
        if _skip(s):
            continue
        mv = VOLT_ONLY.match(s)
        if mv:
            entries.append({'type': 'volt', 'row': (
                int(mv.group(3)), to_cap(mv.group(4)))})
            continue
        md = NAME_DATA.match(s)
        if md:
            entries.append({'type': 'name', 'name': md.group(2).strip(),
                            'row': (int(md.group(5)), to_cap(md.group(6)))})
            continue
        mo = NAME_ONLY.match(s)
        if mo:
            entries.append({'type': 'name', 'name': mo.group(2).strip(),
                            'row': None})
    n = len(entries)
    claimed = [False] * n
    gis = []
    for ni in [i for i, e in enumerate(entries) if e['type'] == 'name']:
        claimed[ni] = True
        r = 0
        while True:
            lo, hi = ni - r - 1, ni + r + 1
            if lo < 0 or hi >= n:
                break
            if (entries[lo]['type'] == 'volt' and not claimed[lo]
                    and entries[hi]['type'] == 'volt' and not claimed[hi]):
                claimed[lo] = claimed[hi] = True
                r += 1
            else:
                break
        vr = [entries[k]['row'] for k in range(ni - r, ni + r + 1)
              if entries[k].get('row')]
        gis.append({'name': entries[ni]['name'],
                    'trafo': sum(t for t, c in vr),
                    'cap': round(sum(c for t, c in vr), 2)})
    leftover = sum(1 for i in range(n)
                   if entries[i]['type'] == 'volt' and not claimed[i])
    return gis, leftover


def main():
    print("AUDIT parser multi-tegangan — LAMA vs BARU\n")
    print(f"{'Region':<13}{'Tbl':<5}{'old':>5}{'new':>5}{'missed':>8}"
          f"{'under':>7}{'leftover':>9}")
    print("-" * 52)
    grand = {}
    details = []
    for region, tid, start, end in TABLES:
        out = pdftext(start, end)
        block = get_block(out, tid)
        if block is None:
            print(f"{region:<13}{tid:<5}  (heading tidak ditemukan)")
            continue
        old = parse_old(block)
        new, leftover = parse_new(block)
        old_by = {g['name']: g for g in old}
        new_by = {g['name']: g for g in new}
        missed = [n for n in new_by if n not in old_by]
        undercounted = []
        for nm in new_by:
            if nm in old_by:
                o, nw = old_by[nm], new_by[nm]
                if o['trafo'] != nw['trafo'] or abs(o['cap'] - nw['cap']) > 0.01:
                    undercounted.append((nm, o, nw))
        g = grand.setdefault(region, {'old': 0, 'new': 0, 'missed': 0,
                                      'under': 0, 'leftover': 0})
        g['old'] += len(old)
        g['new'] += len(new)
        g['missed'] += len(missed)
        g['under'] += len(undercounted)
        g['leftover'] += leftover
        flag = '  <-- CEK' if (missed or undercounted or leftover) else ''
        print(f"{region:<13}{tid:<5}{len(old):>5}{len(new):>5}"
              f"{len(missed):>8}{len(undercounted):>7}{leftover:>9}{flag}")
        for nm in missed:
            details.append(f"  [{region} {tid}] MISSED: '{nm}' "
                           f"(new: {new_by[nm]['trafo']} trafo, "
                           f"{new_by[nm]['cap']} MVA)")
        for nm, o, nw in undercounted:
            details.append(f"  [{region} {tid}] UNDER : '{nm}' "
                           f"old {o['trafo']}t/{o['cap']} -> "
                           f"new {nw['trafo']}t/{nw['cap']}")

    print("\n=== Ringkasan per region ===")
    print(f"{'Region':<14}{'old':>6}{'new':>6}{'missed':>8}{'under':>7}{'leftover':>9}")
    for region, g in grand.items():
        print(f"{region:<14}{g['old']:>6}{g['new']:>6}{g['missed']:>8}"
              f"{g['under']:>7}{g['leftover']:>9}")

    if details:
        print("\n=== Detail GI terdampak ===")
        for d in details:
            print(d)
    else:
        print("\nTidak ada GI terdampak.")


if __name__ == '__main__':
    main()
