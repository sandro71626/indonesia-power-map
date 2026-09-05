#!/usr/bin/env python3
"""Extract Rincian Rencana Pembangunan Gardu Induk dari RUPTL 2025-2034.

Beda dengan `extract_ruptl_generators.py` yang extract pembangkit, script ini
target tabel **planning gardu induk** (New/Ext/Uprate) yang berisi info
COD + status — bukan tabel summary yang sudah dipakai baseline.

Signature header planning table (variasi antarprovinsi):
    "No | Gardu Induk | Tegangan (kV) | Baru/Ext./Uprate | Kapasitas (MVA) | COD | Status"
    "No | Nama GI    | Tegangan (kV) | Jenis           | Kapasitas (MVA) | Target COD"

Output: data/processed/ruptl_substations_{region}.csv

Schema:
    id, name, voltage_kv, action_type, capacity_mva, target_cod_year,
    status, province, region_key, source_page, source_table

Usage:
    python3 scripts/extract_ruptl_substations.py --region jamali \\
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

# Import shared utilities dari generator extractor (DRY — cell parsers sama).
from extract_ruptl_generators import (  # noqa: E402
    REGION_PROVINCES, DEFAULT_PAGES,
    clean_cell, cell_lines, stitch_lines,
    detect_province, parse_all_numbers, parse_years, normalize_status,
)


# ------------------------------------------------------------
# Header detection — different from generator (no "Jenis Pembangkit")
# ------------------------------------------------------------
def is_substation_header(head_norm: list[str]) -> bool:
    """True kalau baris header menandai tabel planning gardu induk.

    Signature: kolom "no" + ("gardu induk" atau "nama gi") + "tegangan" +
    salah satu dari kapasitas MVA. Sengaja exclude tabel summary yang
    tidak punya "baru", "ext", "uprate", "cod", atau "status".
    """
    if not head_norm or head_norm[0] != "no":
        return False
    joined = " | ".join(head_norm)
    has_name = any(k in joined for k in ("gardu induk", "nama gi"))
    has_kv = "tegangan" in joined or "kv" in joined
    has_action_or_cod = any(k in joined for k in
                             ("baru", "ext", "uprate", "cod", "status",
                              "target"))
    return has_name and has_kv and has_action_or_cod


def substation_column_map(head_norm: list[str]) -> dict[str, Optional[int]]:
    """Peta nama kolom → indeks untuk tabel gardu induk."""
    idx: dict[str, Optional[int]] = {"no": 0}

    def find(*keys: str, start: int = 0) -> Optional[int]:
        for i, x in enumerate(head_norm):
            if i < start or not x:
                continue
            for k in keys:
                if k in x:
                    return i
        return None

    idx["sistem"] = find("sistem")
    idx["name"] = find("gardu induk", "nama gi", "nama")
    idx["voltage"] = find("tegangan", " kv ", "kv")
    idx["action"] = find("baru", "ext", "uprate", "jenis")
    idx["capacity"] = find("kapasitas", "mva")
    idx["trafo"] = find("trafo", "jumlah")
    # COD: bisa muncul 2x (RE Base + ARED). Ambil yang paling akhir.
    cods = [i for i, x in enumerate(head_norm) if "cod" in x]
    idx["cod1"] = cods[0] if cods else None
    idx["cod2"] = cods[1] if len(cods) > 1 else None
    idx["status"] = find("status")
    idx["target"] = find("target")
    return idx


TOTAL_KEYWORDS = frozenset({"total", "jumlah", "subtotal", "sub"})


def is_total_row(cells: list[str], colmap: dict) -> bool:
    for key in ("sistem", "name"):
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
    """Extract voltage class string, e.g. '150/20 kV' → '150/20'."""
    s = str(s or "").replace("kV", "").replace("KV", "").strip()
    # Normalize whitespace
    s = " ".join(s.split())
    return s


def parse_capacity_mva(s: str) -> Optional[float]:
    """Sum semua angka di kolom kapasitas (multi-trafo case)."""
    v = parse_all_numbers(s)
    return sum(v) if v else None


def normalize_action(s: str) -> str:
    """Normalize action type: Baru → New, Ext./Extension → Extension,
    Uprate/Uprating → Uprate. Fallback: return trimmed original."""
    n = normalize(s)
    if not n:
        return ""
    if "baru" in n or "new" in n:
        return "New"
    if "ext" in n:
        return "Extension"
    if "uprat" in n or "upr" in n:
        return "Uprate"
    return s.strip()


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
        print(f"[extract_ruptl_sub] scanning pages {page_start}–{end} "
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
                if not is_substation_header(head_norm):
                    continue
                colmap = substation_column_map(head_norm)
                if colmap.get("name") is None:
                    continue

                # Track table id (regex from context)
                m_tab = re.search(r"Tabel\s+([A-C]\d+\.\d+[a-z]?)", page_text)
                table_id = f"Tabel {m_tab.group(1)}" if m_tab else ""

                last_row = None
                for row in tab[1:]:
                    first = clean_cell(row[0] if row else "")
                    if re.fullmatch(r"\d{1,3}", first or ""):
                        key = (page_no, table_id, first)
                        if key in seen_keys:
                            last_row = None
                            continue
                        seen_keys.add(key)
                        last_row = {
                            "row_no": first,
                            "col_lines": [cell_lines(c) for c in row],
                            "page_no": page_no,
                            "table_id": table_id,
                            "province": prov,
                            "colmap": colmap,
                        }
                        rows_out.append(last_row)
                    elif last_row is not None and not first:
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

        name = pick("name")
        if not name:
            continue
        voltage = parse_voltage(pick("voltage"))
        action = normalize_action(pick("action"))
        capacity = parse_capacity_mva(pick("capacity"))
        status_raw = pick("status")
        cod_raw = pick("cod1") or pick("cod2") or pick("target")
        years = parse_years(cod_raw)
        first_year = years[0] if years else ""

        final.append({
            "id": f"RUPTL-{region_key.upper()}-GI-{idx_counter:04d}",
            "name": name,
            "voltage_kv": voltage,
            "action_type": action,
            "capacity_mva": capacity or "",
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
    ap.add_argument("--pages", type=str, default=None,
                    help="Page range 'START-END'")
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
    print(f"[extract_ruptl_sub] region={opts.region} "
          f"({len(provinces)} target provinces)")

    rows = extract_from_pdf(opts.pdf, opts.region, provinces, ps, pe)
    print(f"\n  extracted {len(rows)} gardu induk rows")
    if not rows:
        return 1

    from collections import Counter
    by_prov = Counter(r["province"] for r in rows)
    by_act = Counter(r["action_type"] for r in rows)
    print("\n  per province:")
    for prov, n in by_prov.most_common():
        print(f"    {prov:<40} {n:>4}")
    print("\n  per action:")
    for act, n in by_act.most_common():
        print(f"    {act or '(unknown)':<20} {n:>4}")

    out_path = (opts.out if opts.out and opts.out.is_absolute() else
                project_root / (opts.out or
                                f"data/processed/ruptl_substations_{opts.region}.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["id", "name", "voltage_kv", "action_type", "capacity_mva",
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
