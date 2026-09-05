#!/usr/bin/env python3
"""Extract Rincian Rencana Pembangunan Transmisi dari RUPTL 2025-2034.

Target: tabel planning transmisi dengan kolom From/To/Tegangan/Lingkup/
Panjang/COD/Status. Signature header:

    "No | Transmisi Dari | Transmisi Ke | Tegangan | Lingkup | Panjang (Kms) | COD | Status"

Kolom "Lingkup" berisi pattern kompak: "New, 4 cct, SUTT" atau
"Ext, 2 cct, SKTT" — kita parse jadi action_type + circuits + line_type.

Output: data/processed/ruptl_transmission_{region}.csv

Schema:
    id, name, from_bus, to_bus, voltage_kv, action_type, circuits,
    line_type, length_km, target_cod_year, status, province, region_key,
    source_page, source_table

Usage:
    python3 scripts/extract_ruptl_transmission.py --region jamali \\
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
from _shared.name_stem import normalize  # noqa: E402

# Reuse cell parsers dari generator extractor
from extract_ruptl_generators import (  # noqa: E402
    REGION_PROVINCES, DEFAULT_PAGES,
    clean_cell, cell_lines, stitch_lines,
    detect_province, parse_all_numbers, parse_years, normalize_status,
)


# ------------------------------------------------------------
# Header detection
# ------------------------------------------------------------
def is_transmission_header(head_norm: list[str]) -> bool:
    """True kalau baris header menandai tabel planning transmisi.

    Signature: kolom "no" + "transmisi dari" + "transmisi ke" + "tegangan"
    atau ("dari"+"ke"+"panjang").
    """
    if not head_norm or head_norm[0] != "no":
        return False
    joined = " | ".join(head_norm)
    has_dari = "transmisi dari" in joined or "dari" in head_norm
    has_ke = "transmisi ke" in joined or "ke" in head_norm
    has_length_or_kv = ("panjang" in joined or "kms" in joined
                        or "tegangan" in joined or "tegang" in joined)
    return has_dari and has_ke and has_length_or_kv


def transmission_column_map(head_norm: list[str]) -> dict[str, Optional[int]]:
    idx: dict[str, Optional[int]] = {"no": 0}

    def find(*keys: str) -> Optional[int]:
        for i, x in enumerate(head_norm):
            if not x:
                continue
            for k in keys:
                if k in x:
                    return i
        return None

    idx["dari"] = find("transmisi dari", "dari")
    idx["ke"] = find("transmisi ke")
    if idx["ke"] is None:
        # Cari "ke" as exact/word match saja (bukan substring dari "kesatuan")
        idx["ke"] = next((i for i, x in enumerate(head_norm)
                           if x == "ke" or x.startswith("ke ")), None)
    # pdfplumber kadang split "Tegangan" jadi "Tegang\nan" → setelah
    # normalize whitespace jadi "tegang an" → tidak match "tegangan".
    # Cover both full ("tegangan") dan partial ("tegang") + fallback "kv".
    idx["tegangan"] = find("tegangan", "tegang", "kv")
    idx["lingkup"] = find("lingkup", "scope")
    idx["panjang"] = find("panjang", "kms")
    cods = [i for i, x in enumerate(head_norm) if "cod" in x]
    idx["cod1"] = cods[0] if cods else None
    idx["cod2"] = cods[1] if len(cods) > 1 else None
    idx["status"] = find("status")
    return idx


TOTAL_KEYWORDS = frozenset({"total", "jumlah", "subtotal", "sub"})


def is_total_row(cells: list[str], colmap: dict) -> bool:
    for key in ("dari", "ke"):
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
def parse_voltage(s: str) -> str:
    """Extract voltage class string, e.g. '150 kV' → '150'."""
    s = str(s or "").replace("kV", "").replace("KV", "").strip()
    return " ".join(s.split())


def parse_length_km(s: str) -> Optional[float]:
    """Sum semua angka di kolom Panjang (multi-section case)."""
    v = parse_all_numbers(s)
    return sum(v) if v else None


# Lingkup pattern: "New, 4 cct, SUTT" atau "Ext, 2 cct, SKTT"
LINGKUP_RE = re.compile(
    r"(?P<action>New|Ext|Uprating|Uprate|Baru|Extension)?\s*,?\s*"
    r"(?P<circuits>\d+)\s*/?\s*cct\s*,?\s*"
    r"(?P<line_type>SUTT|SUTET|SKTT|SKLT|SUTM|SKTM)?",
    re.IGNORECASE,
)


def parse_lingkup(s: str) -> tuple[str, str, str]:
    """Parse Lingkup cell → (action_type, circuits, line_type)."""
    if not s:
        return "", "", ""
    m = LINGKUP_RE.search(s)
    if not m:
        return "", "", ""
    action = (m.group("action") or "").strip()
    # Normalize action
    a = action.lower()
    if "new" in a or "baru" in a:
        action = "New"
    elif "uprat" in a:
        action = "Uprate"
    elif "ext" in a:
        action = "Extension"
    circuits = (m.group("circuits") or "").strip()
    line_type = (m.group("line_type") or "").strip().upper()
    return action, circuits, line_type


def clean_bus_name(s: str) -> str:
    """Clean 'Dari'/'Ke' cell — hilangkan garis miring gabungan pdfplumber,
    normalisasi whitespace.

    pdfplumber kadang encode "GI Gandul II / Pamulang" jadi "Gandul II /
    Pamulang" (with / separator) — pertahankan tapi normalize whitespace.
    """
    s = str(s or "").strip()
    # pdfplumber suka insert 2x slash: "//" → "/"
    s = re.sub(r"/+", "/", s)
    s = re.sub(r"\s*/\s*", " / ", s)
    return " ".join(s.split())


# ------------------------------------------------------------
# Extraction
# ------------------------------------------------------------
def extract_from_pdf(pdf_path: Path, region_key: str,
                     valid_provinces: set[str],
                     page_start: int, page_end: int) -> list[dict]:
    rows_out: list[dict] = []
    seen_keys: set[tuple] = set()
    idx_counter = 1
    last_prov: Optional[str] = None

    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        end = min(page_end, n_pages)
        print(f"[extract_ruptl_trm] scanning pages {page_start}–{end} "
              f"({end - page_start + 1} pages)")

        for page_idx in range(page_start - 1, end):
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
                if not is_transmission_header(head_norm):
                    continue
                colmap = transmission_column_map(head_norm)
                if colmap.get("dari") is None or colmap.get("ke") is None:
                    continue

                m_tab = re.search(r"Tabel\s+([A-C]\d+\.\d+[a-z]?)", page_text)
                table_id = f"Tabel {m_tab.group(1)}" if m_tab else ""

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
                        key = (page_no, table_id, row_no)
                        if key in seen_keys:
                            last_row = None
                            continue
                        seen_keys.add(key)
                        last_row = {
                            "col_lines": [cell_lines(c) for c in row],
                            "page_no": page_no,
                            "table_id": table_id,
                            "province": prov,
                            "colmap": colmap,
                        }
                        rows_out.append(last_row)
                    elif last_row is not None and row_no is None and not first:
                        for i, c in enumerate(row):
                            if i < len(last_row["col_lines"]):
                                last_row["col_lines"][i].extend(cell_lines(c))

    final = []
    for r in rows_out:
        cells = [stitch_lines(x) for x in r["col_lines"]]
        cmap = r["colmap"]
        if is_total_row(cells, cmap):
            continue

        def pick(key: str) -> str:
            i = cmap.get(key)
            return cells[i] if (i is not None and i < len(cells)) else ""

        from_bus = clean_bus_name(pick("dari"))
        to_bus = clean_bus_name(pick("ke"))
        if not from_bus or not to_bus:
            continue

        voltage = parse_voltage(pick("tegangan"))
        length = parse_length_km(pick("panjang"))
        action, circuits, line_type = parse_lingkup(pick("lingkup"))
        status_raw = pick("status")
        cod_raw = pick("cod1") or pick("cod2")
        years = parse_years(cod_raw)
        first_year = years[0] if years else ""

        final.append({
            "id": f"RUPTL-{region_key.upper()}-T-{idx_counter:04d}",
            "name": f"{from_bus} — {to_bus}",
            "from_bus": from_bus,
            "to_bus": to_bus,
            "voltage_kv": voltage,
            "action_type": action,
            "circuits": circuits,
            "line_type": line_type,
            "length_km": length or "",
            "target_cod_year": first_year,
            "status": normalize_status(status_raw),
            "province": r["province"].title(),
            "region_key": region_key,
            "source_page": str(r["page_no"]),
            "source_table": r["table_id"],
        })
        idx_counter += 1
    return final


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True,
                    choices=sorted(REGION_PROVINCES.keys()))
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--pages", type=str, default=None)
    ap.add_argument("--out", type=Path, default=None)
    opts = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]

    if opts.pages:
        m = re.match(r"(\d+)-(\d+)", opts.pages)
        if not m:
            print("Invalid --pages format", file=sys.stderr)
            return 2
        ps, pe = int(m.group(1)), int(m.group(2))
    else:
        ps, pe = DEFAULT_PAGES

    if not opts.pdf.exists():
        print(f"PDF not found: {opts.pdf}", file=sys.stderr)
        return 2

    provinces = REGION_PROVINCES[opts.region]
    print(f"[extract_ruptl_trm] region={opts.region} "
          f"({len(provinces)} target provinces)")

    rows = extract_from_pdf(opts.pdf, opts.region, provinces, ps, pe)
    print(f"\n  extracted {len(rows)} transmisi rows")
    if not rows:
        return 1

    from collections import Counter
    by_prov = Counter(r["province"] for r in rows)
    by_act = Counter(r["action_type"] for r in rows)
    by_kv = Counter(r["voltage_kv"] for r in rows)
    print("\n  per province:")
    for prov, n in by_prov.most_common():
        print(f"    {prov:<40} {n:>4}")
    print("\n  per action:")
    for act, n in by_act.most_common():
        print(f"    {act or '(unknown)':<20} {n:>4}")
    print("\n  per voltage (top 5):")
    for kv, n in by_kv.most_common(5):
        print(f"    {kv or '(unknown)':<20} {n:>4}")

    out_path = (opts.out if opts.out and opts.out.is_absolute() else
                project_root / (opts.out or
                                f"data/processed/ruptl_transmission_{opts.region}.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["id", "name", "from_bus", "to_bus", "voltage_kv",
               "action_type", "circuits", "line_type", "length_km",
               "target_cod_year", "status", "province", "region_key",
               "source_page", "source_table"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in headers})
    print(f"\n  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
