"""
Shared parser untuk tabel "Realisasi Kapasitas Trafo Gardu Induk" RUPTL
PLN 2025-2034. Dipakai semua extractor substation regional
(JAMALI / Sumatra / Kalimantan / Sulawesi / Maluku-Papua).

Phrasing heading bervariasi antar Lampiran:
  - Lampiran A & C: "Realisasi Kapasitas Trafo Gardu Induk"
  - Lampiran B (JAMALI): "Realisasi Kapasitas Gardu Induk Eksisting"
Regex heading menerima keduanya (kata 'Trafo' dan 'Eksisting' opsional).

Layout tabel juga bervariasi. Parser ini menangani SEMUA varian yang
ditemukan via audit (`scripts/_audit_multivolt.py`):

1. **Single-line standard.** Satu GI = satu baris (No + Nama + Tegangan
   + Jumlah Trafo + Kapasitas). Mayoritas baris.

2. **Multi-tegangan, nama di tengah blok.** Satu GI = beberapa baris
   (satu per level tegangan trafo); sel No & Nama di-merge vertikal dan
   `pdftotext` me-render nama di baris TENGAH blok GI itu — kadang di
   baris yang juga memuat data, kadang di baris sendiri tanpa data.
   Berlaku di: Sulawesi C4 (Pangkep), Sumatra A8 (Keramasan)/A9
   (Pekalongan), Maluku/Papua C7-C10.

3. **Multi-tegangan, nomor terbawa baris VOLT.** GI dengan nomor di
   baris data (bukan di baris nama) dan nama berdiri sendiri di baris
   sendiri. Cuma satu kasus ditemukan: GI Panakkukang di Sulawesi C4.

4. **Named continuation.** GI dengan DUA baris bernama berurutan, hanya
   baris pertama yang punya nomor. RUPTL menomori keduanya sebagai SATU
   entry — parser meng-gabung jadi satu GI (pakai nama dari baris
   bernomor). Satu kasus: 'Bontoala' + 'GIS Bontoala' di Sulawesi C4.

5. **Dash placeholder.** GI listed dengan '-' untuk trafo & kapasitas
   (GI dibangun tapi trafo belum direalisasi). Di-emit dengan
   `trafo_count=0` dan `capacity_mva=None`. Ditemukan di Sumatra A2
   (Sorik Merapi) dan A6 (Indarung).

Algoritma:
  - Klasifikasi tiap baris: NAME_PRIMARY (nama+nomor), NAME_CONT
    (nama+volts tanpa nomor), NAME_CTR (nama saja), VOLT (data saja,
    boleh bawa nomor), JUNK.
  - Iterasi: NAME_PRIMARY & NAME_CTR start GI baru lalu menyerap VOLT
    line tetangga secara SIMETRIS. NAME_CONT menempel ke GI saat ini.

Output per GI:
  - `voltage`: level tegangan unik desc (mis. '150/70/20')
  - `trafo_count`: jumlah seluruh level tegangan
  - `capacity_mva`: jumlah seluruh level tegangan; None bila semua dash
"""
import re
import subprocess


# Heading: matches A/C ("Kapasitas Trafo Gardu Induk") dan B
# ("Kapasitas Gardu Induk Eksisting"). 'Realisasi', 'Trafo', 'Eksisting'
# semua opsional supaya menerima ketiga phrasing.
def _heading_pat(prefix, num):
    return re.compile(
        rf'Tabel\s+{prefix}{num}\.(\d+)\.?\s*(?:Realisasi\s+)?'
        rf'Kapasitas\s+(?:Trafo\s+)?Gardu\s+Induk(?:\s+Eksisting)?[^\n]*\n'
    )


# Volt tuple: HV/LV  jumlah_trafo  kapasitas. Count & cap boleh '-'.
VOLT_RE = re.compile(
    r'(\d{2,3})\s*/\s*(\d{2,3})\s+(\d+|-)\s+([\d.,]+|-)'
)
# Nomor GI di depan baris: 1-3 digit + whitespace (bukan '/').
# 'X/Y' format voltage tidak match karena '\d+\s+' butuh whitespace.
NUM_LEAD_RE = re.compile(r'^\s*(\d{1,3})\s+')

# Pola untuk skip line: header tabel, footer halaman, baris ringkasan.
_SKIP_KEYWORDS = ('Tegangan', 'Total Kapasitas', 'Jumlah Trafo',
                  'Nama GI', 'Nama GI/GITET')
_SKIP_PAGENUM = re.compile(r'^\s*[A-C]\s*-?\s*\d+\s*$')
_SKIP_LEADWORD = re.compile(r'^\s*(Total|Jumlah|PLN|\(Unit\))\b',
                            re.IGNORECASE)


def _skip_line(s):
    if not s.strip():
        return True
    if any(k in s for k in _SKIP_KEYWORDS):
        return True
    if _SKIP_PAGENUM.match(s):
        return True
    if _SKIP_LEADWORD.search(s):
        return True
    return False


def _to_int(s):
    return 0 if s == '-' else int(s)


def _to_cap(s):
    if s == '-':
        return None
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def _classify(line):
    """Pecah satu baris jadi (num, volts, name_text)."""
    nm = NUM_LEAD_RE.match(line)
    num = None
    rest = line
    if nm:
        num = int(nm.group(1))
        rest = line[nm.end():]
    volts = []
    last = 0
    name_parts = []
    for vm in VOLT_RE.finditer(rest):
        seg = rest[last:vm.start()].strip()
        if seg:
            name_parts.append(seg)
        volts.append((int(vm.group(1)), int(vm.group(2)),
                      _to_int(vm.group(3)), _to_cap(vm.group(4))))
        last = vm.end()
    tail = rest[last:].strip()
    if tail:
        name_parts.append(tail)
    nametext = ' '.join(name_parts).strip()
    return num, volts, nametext


def _summarize(name, num, volts):
    cnt = sum(c for _, _, c, _ in volts)
    cap_vals = [cap for _, _, _, cap in volts if cap is not None]
    cap = round(sum(cap_vals), 2) if cap_vals else None
    levels = sorted({v for hv, lv, _, _ in volts for v in (hv, lv)},
                    reverse=True)
    voltage = '/'.join(str(x) for x in levels) if levels else ''
    return {'src_no': num, 'name': name, 'voltage': voltage,
            'trafo_count': cnt, 'capacity_mva': cap}


def extract_table(pdf_path, table_id, start_page, end_page, debug=False):
    """Ekstrak GI dari Tabel `<table_id>.4` (atau .3) dalam range halaman.

    Args:
        pdf_path: path ke RUPTL PDF
        table_id: 'A1', 'B3', 'C9', dll. (prefix + nomor lampiran)
        start_page, end_page: range halaman (1-indexed) untuk pdftotext
        debug: True → cetak peringatan kalau ada VOLT line tak ter-grup

    Returns:
        List of dict per GI:
        {src_no, name, voltage, trafo_count, capacity_mva}
        - src_no: nomor RUPTL (int) atau None
        - voltage: '150/70/20' (level tegangan unik desc)
        - trafo_count: int (0 bila dash)
        - capacity_mva: float atau None (None bila semua dash)
    """
    out = subprocess.run(
        ['pdftotext', '-layout', '-f', str(start_page), '-l', str(end_page),
         str(pdf_path), '-'],
        capture_output=True, text=True
    ).stdout
    prefix, num = table_id[0], table_id[1:]
    m = _heading_pat(prefix, num).search(out)
    if not m:
        return []
    sub = int(m.group(1))
    end_m = re.compile(
        rf'Tabel\s+{prefix}{num}\.{sub + 1}\b').search(out, m.end())
    block = out[m.end():end_m.start() if end_m else len(out)]

    # Klasifikasi tiap baris.
    entries = []
    for line in block.split('\n'):
        s = line.rstrip()
        if _skip_line(s):
            continue
        n, volts, name = _classify(s)
        entries.append({'num': n, 'volts': volts, 'name': name})

    # Tentukan role per entry.
    roles = []
    for e in entries:
        has_n = bool(e['name'])
        has_v = bool(e['volts'])
        has_num = e['num'] is not None
        if has_n and has_num:
            roles.append('NAME_PRIMARY')
        elif has_n and has_v:
            roles.append('NAME_CONT')
        elif has_n:
            roles.append('NAME_CTR')
        elif has_v:
            roles.append('VOLT')
        else:
            roles.append('JUNK')

    n = len(entries)
    claimed = [False] * n
    gis = []

    def expand_sym(idx, gi):
        """Klaim VOLT line atas & bawah secara simetris."""
        r = 0
        while True:
            lo, hi = idx - r - 1, idx + r + 1
            if lo < 0 or hi >= n:
                break
            if (roles[lo] == 'VOLT' and not claimed[lo]
                    and roles[hi] == 'VOLT' and not claimed[hi]):
                claimed[lo] = claimed[hi] = True
                gi['volts'] = (entries[lo]['volts'] + gi['volts']
                               + entries[hi]['volts'])
                if gi['num'] is None:
                    gi['num'] = entries[lo]['num'] or entries[hi]['num']
                r += 1
            else:
                break

    current = None
    for i in range(n):
        if roles[i] == 'NAME_PRIMARY':
            claimed[i] = True
            gi = {'num': entries[i]['num'], 'name': entries[i]['name'],
                  'volts': list(entries[i]['volts'])}
            expand_sym(i, gi)
            gis.append(gi)
            current = gi
        elif roles[i] == 'NAME_CTR':
            claimed[i] = True
            gi = {'num': None, 'name': entries[i]['name'], 'volts': []}
            expand_sym(i, gi)
            if not gi['volts']:
                # Tidak menyerap VOLT apa pun — kemungkinan teks liar
                # (catatan kaki yang terlewat dari skip filter). Drop.
                continue
            gis.append(gi)
            current = gi
        elif roles[i] == 'NAME_CONT':
            claimed[i] = True
            if current is None:
                continue   # continuation tanpa GI sebelumnya — anomali
            current['volts'].extend(entries[i]['volts'])
        # VOLT: di-claim via expand_sym; JUNK: diabaikan.

    if debug:
        leftover = [i for i in range(n)
                    if roles[i] == 'VOLT' and not claimed[i]]
        if leftover:
            print(f"  WARN {table_id}: {len(leftover)} baris VOLT "
                  f"tak ter-grup")

    return [_summarize(g['name'], g['num'], g['volts'])
            for g in gis if g['volts']]
