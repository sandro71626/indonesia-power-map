#!/usr/bin/env python3
"""Extract Rincian pembangkit row-level dari RUPTL PLN 2025-2034 per region.

Pakai pdfplumber untuk parse table structure (bukan `pdftotext -layout` yang
brittle). Prinsip port dari
`indonesia-100gw-solar-study/tools/ruptl_extract.py` — header-signature
detection, dynamic column mapping, multi-line cell handling, total-row filter.

Output:
    data/processed/ruptl_generators_{region}.csv

Schema:
    id, name, type, capacity_mw, province, region_key, status,
    target_cod_year, cod_re_base, cod_ared, developer,
    source_table, source_page

Usage:
    python3 scripts/extract_ruptl_generators.py --region jamali \\
        --pdf data/raw/sources/RUPTL-2025-2034.pdf
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("pdfplumber not installed. Run: pip install pdfplumber",
          file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import (  # noqa: E402
    PLT_PREFIXES, CANONICAL_PLT_TYPE, infer_plant_type, normalize,
)

# Regex untuk cari PLT-token di jenis cell yang kompleks — handle:
#   "PLTGU/G"        → PLTGU (slash gabung dari pdfplumber "PLTGU//G")
#   "PLTS+BESS"      → PLTS (composite: solar generation + battery storage)
#   "PLTS +/BESS"    → PLTS (whitespace variasi)
#   "PLTBm1)"        → PLTBm (annotation "1)" footnote reference)
#   "PLTU/MT"        → PLTU
# Prioritas: PLT prefix panjang duluan (PLTGU sebelum PLTG, PLTMG sebelum PLTM).
# Sort by length desc supaya greedy match yang benar. BESS di-akhir supaya
# "PLTS+BESS" match PLTS dulu, bukan BESS.
_PLT_TOKEN_RE = re.compile(
    r"\b(" + "|".join(sorted(CANONICAL_PLT_TYPE.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def resolve_plant_type(name: str, jenis_cell: str) -> str:
    """Determine canonical PLT type (mixed-case, sesuai frontend).

    Order:
      1. Extract PLT-code token dari jenis_cell via regex (handle slash/plus/
         parens/footnote annotations).
      2. Special promote: kalau jenis standalone "BESS" (storage), cek name
         untuk primary generation type (PLTS+BESS/PLTA+BESS/Hybrid) —
         Kalau ada, gunakan generation type supaya map tidak salah kira
         BESS = pembangkit.
      3. Special: "Hybrid" di nama tanpa jenis clear → default PLTS
         (Indonesian hybrid systems mayoritas PV+diesel).
      4. Fallback ke `infer_plant_type` (name-prefix + fuel heuristic).
    """
    resolved = None
    if jenis_cell:
        m = _PLT_TOKEN_RE.search(jenis_cell)
        if m:
            resolved = CANONICAL_PLT_TYPE.get(m.group(1).upper(), m.group(1))

    # BESS-promotion heuristic: BESS row biasanya companion storage untuk
    # PLTS project (satu proyek fisik, dua baris RUPTL karena tarif beda).
    # Kalau name explicit menyebutkan generation partner, gunakan itu.
    if resolved == "BESS" and name:
        name_upper = name.upper()
        for gen_type in ("PLTS", "PLTA", "PLTU", "PLTGU", "PLTB", "PLTP"):
            if gen_type in name_upper:
                return gen_type
        if "hybrid" in name.lower():
            return "PLTS"
        # BESS standalone tanpa hint → keep sebagai BESS
        return "BESS"

    if resolved:
        return resolved

    # Heuristic: "Hybrid" di nama tanpa jenis clear → default PLTS
    if name and "hybrid" in name.lower():
        return "PLTS"
    fallback = infer_plant_type(name, jenis_cell)
    return CANONICAL_PLT_TYPE.get(fallback.upper(), fallback)


# ------------------------------------------------------------
# Region → set provinsi (untuk filter halaman Lampiran)
# ------------------------------------------------------------
REGION_PROVINCES: dict[str, set[str]] = {
    "jamali":       {"dki jakarta", "banten", "jawa barat", "jawa tengah",
                     "daerah istimewa yogyakarta", "jawa timur", "bali"},
    "sumatra":      {"aceh", "sumatera utara", "sumatera barat", "riau",
                     "kepulauan riau", "kepulauan bangka belitung",
                     "sumatera selatan", "jambi", "bengkulu", "lampung"},
    "kalimantan":   {"kalimantan barat", "kalimantan tengah",
                     "kalimantan selatan", "kalimantan timur",
                     "kalimantan utara"},
    "sulawesi":     {"sulawesi utara", "sulawesi tengah", "sulawesi selatan",
                     "sulawesi tenggara", "gorontalo", "sulawesi barat"},
    "maluku":       {"maluku", "maluku utara"},
    "papua":        {"papua", "papua barat", "papua tengah", "papua selatan",
                     "papua barat daya", "papua pegunungan"},
    "ntb":          {"nusa tenggara barat"},
    "ntt":          {"nusa tenggara timur"},
    # Combined region aliases (untuk backward compat dengan scripts existing)
    "maluku_papua":  {"maluku", "maluku utara", "papua", "papua barat",
                      "papua tengah", "papua selatan", "papua barat daya",
                      "papua pegunungan"},
    "nusa_tenggara": {"nusa tenggara barat", "nusa tenggara timur"},
}

# Default page range for Lampiran A/B/C — di RUPTL 2025-2034 ~pages 595-1190.
# Empiris dari earlier extraction: A (Sumatera+Kalimantan) 600-810,
# B (Jamali) 811-950, C (Sulawesi+Maluku+Papua+Nusra) 951-1189.
DEFAULT_PAGES = (595, 1190)


# ------------------------------------------------------------
# Text cleaners
# ------------------------------------------------------------
def clean_cell(v) -> str:
    """Compress whitespace in one cell, preserving line breaks removed."""
    return " ".join(str(v or "").split())


def cell_lines(v) -> list[str]:
    """Split a cell into non-empty lines (preserve for column-split repair)."""
    return [x.strip() for x in str(v or "").split("\n") if x.strip()]


def join_column_lines(subcols: list[list[str]]) -> list[str]:
    """Join multi-column cell lines row-by-row (port `jahit_baris`).

    pdfplumber kadang split one wide cell jadi dua narrow columns saat ada
    garis palsu di tengah. Rejoining line-per-line memulihkan text asli.
    """
    n = max((len(x) for x in subcols), default=0)
    return ["".join(x[i] if i < len(x) else "" for x in subcols)
            for i in range(n)]


def stitch_lines(lines: list[str]) -> str:
    """Sambung baris dalam satu sel menjadi satu string.

    Simplified port `sambung_baris`: default sambung dengan spasi.
    Kalau line kiri berakhir huruf kecil dan kanan mulai huruf kecil pendek
    (<=3 char), assume kata terpenggal → sambung tanpa spasi.
    """
    if not lines:
        return ""
    out = [lines[0]]
    for cur in lines[1:]:
        prev = out[-1]
        if (prev and cur and prev[-1].isalpha()
                and re.match(r"^[a-z]{1,3}(?:$|[^a-z])", cur)):
            out[-1] = prev + cur
        else:
            out.append(cur)
    return " ".join(out)


# ------------------------------------------------------------
# Table type detection
# ------------------------------------------------------------
def is_pembangkit_header(head_norm: list[str]) -> bool:
    """Return True kalau header row menandai tabel Rincian Pembangkit.

    Port `jenis_tabel` — signature-based, bukan judul-based (nomor tabel
    tidak seragam antarprovinsi).
    """
    if not head_norm or head_norm[0] != "no":
        return False
    joined = " | ".join(head_norm)
    # Ada dua varian judul kolom Jenis Pembangkit:
    #   "Jenis Pembangkit"     (Sumatera style)
    #   "Jenis" + "Lokasi/Nama Pembangkit"  (Jawa style)
    if "jenis pembangkit" in joined:
        return True
    if "jenis" in head_norm and any(
            "pembangkit" in x or x == "proyek" for x in head_norm):
        return True
    return False


def column_map(head_norm: list[str]) -> dict[str, Optional[int]]:
    """Peta nama kolom → indeks. Port simplified dari `peta_kolom`."""
    idx: dict[str, Optional[int]] = {"no": 0}

    def find(*keys: str, start: int = 0) -> Optional[int]:
        for i, x in enumerate(head_norm):
            if i < start or not x:
                continue
            for k in keys:
                if k in x:
                    return i
        return None

    idx["sistem"] = find("sistem", "nama sistem")
    idx["jenis"] = find("jenis")
    idx["lokasi"] = find("lokasi", "nama pembangkit", "proyek")
    idx["kapasitas"] = find("kapasitas")
    idx["status"] = find("status")
    idx["pengembang"] = find("pengembang")
    # Dua kolom COD sekaligus (RE Base + ARED)
    cods = [i for i, x in enumerate(head_norm) if "cod" in x]
    idx["cod1"] = cods[0] if cods else None
    idx["cod2"] = cods[1] if len(cods) > 1 else None
    # Kalimantan variant: kolom Lokasi kosong di header padahal data ada
    if (idx["lokasi"] is None and idx["jenis"] is not None
            and idx["kapasitas"] is not None
            and idx["kapasitas"] - idx["jenis"] >= 2):
        idx["lokasi"] = idx["jenis"] + 1
    return idx


TOTAL_KEYWORDS = frozenset({"total", "jumlah", "subtotal", "sub"})


def is_total_row(cells: list[str], colmap: dict) -> bool:
    """Filter baris "Sulbagsel Total" / "Jumlah" yang bukan proyek riil."""
    for key in ("sistem", "lokasi"):
        i = colmap.get(key)
        if i is None or i >= len(cells):
            continue
        t = cells[i].strip()
        if not t or len(t) > 28:
            continue
        words = {w for w in re.split(r"[^a-z]+", t.lower()) if w}
        if words & TOTAL_KEYWORDS:
            return True
    return False


# ------------------------------------------------------------
# Value parsers
# ------------------------------------------------------------
def parse_all_numbers(s: str) -> list[float]:
    """Extract semua angka dari sel (mungkin multi-unit '45 43').

    Handle 3 format:
      - "120.0"       → 120.0     (English decimal — 1-2 digit setelah .)
      - "1.234"       → 1234      (Indonesian thousands — 3+ digit setelah .)
      - "1.234,56"    → 1234.56   (Indonesian: . thousands, , decimal)
      - "45,5"        → 45.5      (Indonesian decimal-only)
      - "1200"        → 1200.0    (integer, no separator)
    """
    if not s:
        return []
    s = s.replace("*", "")
    out = []
    for m in re.finditer(r"(\d[\d.,]*)", s):
        token = m.group(1)
        try:
            if "," in token:
                # Indonesian: . = thousands, , = decimal
                cleaned = token.replace(".", "").replace(",", ".")
            elif "." in token:
                # Ambiguous: decimal atau thousands separator?
                parts = token.split(".")
                last = parts[-1]
                # Kalau bagian setelah . panjangnya 1-2 digit → decimal
                # Kalau 3+ digit → thousands separator
                if len(parts) == 2 and len(last) <= 2:
                    cleaned = token  # English decimal
                elif all(len(p) == 3 for p in parts[1:]):
                    cleaned = token.replace(".", "")  # thousands
                else:
                    # Mixed/ambiguous — treat . as decimal for last segment
                    cleaned = "".join(parts[:-1]) + "." + last
            else:
                cleaned = token
            out.append(float(cleaned))
        except ValueError:
            pass
    return out


def parse_capacity(s: str) -> Optional[float]:
    """Total kapasitas satu baris. SUM semua angka (multi-unit case).

    Port `kapasitas` dari referensi: mis. "45 43" (dua unit) = 88 MW total.
    """
    v = parse_all_numbers(s)
    return sum(v) if v else None


def parse_years(s: str) -> list[int]:
    """Extract semua tahun COD 2025–2034."""
    return [int(y) for y in re.findall(r"\b(20[2-3]\d)\b", s or "")
            if 2025 <= int(y) <= 2034]


def normalize_status(s: str) -> str:
    """Fold RUPTL status verbatim → 5 kelas standar.

    Port `status_d03`. Return kelas kanonik untuk konsistensi dengan
    reconciler downstream.
    """
    n = s.lower()
    if "konstruksi" in n or "energize" in n:
        return "Construction"
    if "committed" in n or "commited" in n or "ppa" in n:
        return "Committed"
    if any(k in n for k in ("pengadaan", "rencana", "pendanaan")):
        return "Planned"
    if "eksplorasi" in n:
        return "Proposed"
    return s.strip() or "Unknown"


# ------------------------------------------------------------
# Province detection per page
# ------------------------------------------------------------
PROVINCE_HEADING_RE = re.compile(
    r"(?:LAMPIRAN\s+[A-C]\.?\s*\d+[\s\.:]*)?"
    r"(?:PROVINSI\s+)?"
    r"([A-Z][A-Z\s\.\(\)]{4,60})",
    re.MULTILINE,
)


def detect_province(page_text: str,
                    valid_provinces: set[str]) -> Optional[str]:
    """Cari nama provinsi di teks halaman.

    Cari HANYA di 15 baris teratas (heading area) — JANGAN fallback ke
    full page text, karena footer PLN sering menyebut "Jawa-Bali",
    "Bali", "Sumatera" yang akan spill ke province salah.

    Sort provinces by length desc supaya "sumatera utara" match sebelum
    "sumatera".
    """
    if not page_text:
        return None
    sorted_provs = sorted(valid_provinces, key=len, reverse=True)
    # Compile word-boundary regex per prov agar "bali" tidak match "jawa-bali"
    # ("jawa bali" setelah normalize).
    prov_res = [(p, re.compile(rf"\b{re.escape(p)}\b")) for p in sorted_provs]
    for line in page_text.split("\n")[:15]:
        norm_line = normalize(line)
        if not norm_line:
            continue
        # Skip line kalau mengandung "jawa bali" / "jawa-bali" (sistem name,
        # bukan province heading) — cek eksplisit sebelum matching provinsi.
        if "jawa bali" in norm_line or "jawabali" in norm_line:
            continue
        for prov, rx in prov_res:
            if rx.search(norm_line):
                return prov
    return None


# ------------------------------------------------------------
# Table extraction main loop
# ------------------------------------------------------------
def extract_from_pdf(pdf_path: Path, region_key: str,
                     valid_provinces: set[str],
                     page_start: int, page_end: int) -> list[dict]:
    """Iterasi halaman, extract pembangkit rows dari tabel Rincian."""
    rows_out: list[dict] = []
    seen_keys: set[tuple] = set()  # dedupe: (page, table_hash, row_no)
    idx_counter = 1
    last_prov: Optional[str] = None  # carry-forward untuk multi-page tabel

    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        end = min(page_end, n_pages)
        print(f"[extract_ruptl_gen] scanning pages {page_start}–{end} "
              f"({end - page_start + 1} pages)")

        for page_idx in range(page_start - 1, end):  # 0-indexed
            page = pdf.pages[page_idx]
            page_no = page_idx + 1
            page_text = page.extract_text() or ""
            prov_here = detect_province(page_text, valid_provinces)
            if prov_here:
                last_prov = prov_here
            prov = prov_here or last_prov
            if not prov:
                continue

            for tab in page.extract_tables() or []:
                if not tab or len(tab) < 3:
                    continue
                head = [clean_cell(c) for c in tab[0]]
                head_norm = [normalize(x) for x in head]
                if not is_pembangkit_header(head_norm):
                    continue
                colmap = column_map(head_norm)
                if colmap.get("lokasi") is None:
                    continue  # tabel tanpa kolom nama pembangkit — skip

                # Track table id (regex from context text near top of page)
                table_id = ""
                m_tab = re.search(r"Tabel\s+([A-C]\d+\.\d+[a-z]?)",
                                   page_text)
                if m_tab:
                    table_id = f"Tabel {m_tab.group(1)}"

                # Row-by-row parse (with continuation-line stitching).
                # pdfplumber kadang taruh nomor baris di col[0] atau col[1]
                # (alternasi random per table). Cek keduanya.
                last_row = None
                for row in tab[1:]:
                    first = clean_cell(row[0] if row else "")
                    second = clean_cell(row[1] if len(row) > 1 else "")
                    row_no = None
                    if re.fullmatch(r"\d{1,3}", first or ""):
                        row_no = first
                    elif not first and re.fullmatch(r"\d{1,3}", second or ""):
                        row_no = second
                    if row_no is not None:
                        # New row entry
                        key = (page_no, table_id, row_no)
                        if key in seen_keys:
                            last_row = None
                            continue
                        seen_keys.add(key)
                        last_row = {
                            "row_no": row_no,
                            "col_lines": [cell_lines(c) for c in row],
                            "page_no": page_no,
                            "table_id": table_id,
                            "province": prov,
                            "colmap": colmap,
                        }
                        rows_out.append(last_row)
                    elif last_row is not None and row_no is None and not first:
                        # Continuation row: append to previous cell lines
                        for i, c in enumerate(row):
                            if i < len(last_row["col_lines"]):
                                last_row["col_lines"][i].extend(cell_lines(c))

    # Materialize row dicts
    final = []
    for r in rows_out:
        cells = [stitch_lines(x) for x in r["col_lines"]]
        cmap = r["colmap"]
        if is_total_row(cells, cmap):
            continue

        def pick(key: str) -> str:
            i = cmap.get(key)
            return cells[i] if (i is not None and i < len(cells)) else ""

        name = pick("lokasi")
        jenis = pick("jenis")
        capacity_raw = pick("kapasitas")
        status_raw = pick("status")
        developer = pick("pengembang")
        cod_re_base = pick("cod1")
        cod_ared = pick("cod2")

        capacity = parse_capacity(capacity_raw)
        plt_type = resolve_plant_type(name, jenis)
        years_base = parse_years(cod_re_base)
        years_ared = parse_years(cod_ared)
        first_year = years_base[0] if years_base else (
            years_ared[0] if years_ared else "")

        if not name:
            continue

        final.append({
            "id": f"RUPTL-{region_key.upper()}-P-{idx_counter:04d}",
            "name": name,
            "type": plt_type,
            "capacity_mw": capacity or "",
            "province": r["province"].title(),
            "region_key": region_key,
            "status": normalize_status(status_raw),
            "target_cod_year": first_year,
            "cod_re_base": " ".join(str(y) for y in years_base),
            "cod_ared": " ".join(str(y) for y in years_ared),
            "developer": developer.strip(),
            "source_table": r["table_id"],
            "source_page": str(r["page_no"]),
        })
        idx_counter += 1
    return final


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True,
                    choices=sorted(REGION_PROVINCES.keys()),
                    help="region key (jamali/sumatra/…)")
    ap.add_argument("--pdf", type=Path, required=True,
                    help="Path ke RUPTL PDF")
    ap.add_argument("--pages", type=str, default=None,
                    help="Page range 'START-END' (default: 595-1190 = Lampiran A/B/C)")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output CSV path (default: data/processed/ruptl_generators_{region}.csv)")
    opts = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]

    if opts.pages:
        m = re.match(r"(\d+)-(\d+)", opts.pages)
        if not m:
            print("Invalid --pages format, use START-END", file=sys.stderr)
            return 2
        page_start, page_end = int(m.group(1)), int(m.group(2))
    else:
        page_start, page_end = DEFAULT_PAGES

    if not opts.pdf.exists():
        print(f"PDF not found: {opts.pdf}", file=sys.stderr)
        return 2

    provinces = REGION_PROVINCES[opts.region]
    print(f"[extract_ruptl_gen] region={opts.region} "
          f"({len(provinces)} target provinces)")
    print(f"  PDF: {opts.pdf}")

    rows = extract_from_pdf(opts.pdf, opts.region, provinces,
                             page_start, page_end)
    print(f"\n  extracted {len(rows)} pembangkit rows")

    if not rows:
        print("  ! no rows — check --pages or region filter")
        return 1

    # Group summary by province
    from collections import Counter
    by_prov = Counter(r["province"] for r in rows)
    print("\n  per province:")
    for prov, n in by_prov.most_common():
        print(f"    {prov:<40} {n:>4}")

    # Write CSV
    out_path = (opts.out if opts.out and opts.out.is_absolute() else
                project_root / (opts.out or
                                f"data/processed/ruptl_generators_{opts.region}.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["id", "name", "type", "capacity_mw", "province", "region_key",
               "status", "target_cod_year", "cod_re_base", "cod_ared",
               "developer", "source_table", "source_page"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in headers})
    print(f"\n  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
