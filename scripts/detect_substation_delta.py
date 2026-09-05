#!/usr/bin/env python3
"""Compare RUPTL planning gardu induk rows vs IPM substation baseline.

Baseline `substation_master_{region}.csv` sudah sourced dari RUPTL Tabel
B1.4 (summary snapshot). Script ini pakai RUPTL planning table
(New/Ext/Uprate + COD) sebagai delta — flag baris planned yang:

    NEW_BUILD        — RUPTL bilang New, baseline TIDAK punya → belum
                       ke-map di IPM. Kandidat untuk add ke baseline.
    EXISTING_EXT     — RUPTL bilang Extension, baseline punya → capacity
                       bakal grow. Optional enrichment.
    EXISTING_UPRATE  — RUPTL bilang Uprate, baseline punya → voltage/MVA
                       bakal berubah.
    RECLASSIFY_NEW   — RUPTL bilang New, baseline PUNYA → konflik/dup,
                       cek nama variation.
    ORPHAN           — Action tidak dikenal atau nama kosong.

Output:
    data/processed/substation_delta_{region}.csv (row-level classification)
    data/reconciliation/substation_delta_{region}_{ts}.md (audit report)

Usage:
    python3 scripts/detect_substation_delta.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import plant_name_stem, plant_name_tokens  # noqa: E402


# ------------------------------------------------------------
# Classification tiers
# ------------------------------------------------------------
CLS_NEW_BUILD = "NEW_BUILD"
CLS_EXISTING_EXT = "EXISTING_EXT"
CLS_EXISTING_UPRATE = "EXISTING_UPRATE"
CLS_RECLASSIFY_NEW = "RECLASSIFY_NEW"
CLS_ORPHAN = "ORPHAN"

TIER_ORDER = [
    CLS_NEW_BUILD, CLS_EXISTING_EXT, CLS_EXISTING_UPRATE,
    CLS_RECLASSIFY_NEW, CLS_ORPHAN,
]


# ------------------------------------------------------------
# Substation name stem (adapted from plant_name_stem)
# ------------------------------------------------------------
def substation_stem(name: str) -> str:
    """Strip GI prefix + boilerplate untuk get substation name-inti.

    "GI Cirebon Baru" → "cirebon"
    "Gardu Induk Ancol" → "ancol"
    "Ancol II / Kelapa Gading" → "ancol / kelapa gading"

    Reuse plant_name_stem (already strips PLT prefixes yang kadang muncul
    di sub name juga), lalu strip GI-specific boilerplate.
    """
    s = plant_name_stem(name)
    # Strip GI/GITET/GIS prefix words yang belum di plant_name_stem
    import re
    s = re.sub(r"\b(?:gi|gis|gitet|new|baru|ext|extension|uprate|switching)\b",
               " ", s)
    return " ".join(s.split())


def substation_tokens(name: str) -> set[str]:
    """Token set untuk substation, exclude 'baru'/'ext'/etc."""
    tokens = plant_name_tokens(name)
    return tokens - {"gi", "gis", "gitet", "new", "baru", "ext",
                      "extension", "uprate", "switching"}


# ------------------------------------------------------------
# Load & index baseline
# ------------------------------------------------------------
def load_baseline(path: Path) -> tuple[list[dict], dict]:
    """Return (rows, {(prov_norm, stem): [rows]})."""
    rows = []
    if not path.exists():
        return rows, {}
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    index: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        stem = substation_stem(r.get("name", ""))
        prov = (r.get("province") or "").strip().lower()
        r["_stem"] = stem
        r["_tokens"] = substation_tokens(r.get("name", ""))
        r["_prov"] = prov
        key = (prov, stem)
        index.setdefault(key, []).append(r)
    return rows, index


def find_baseline_match(rup_row: dict, baseline_rows: list[dict],
                         baseline_index: dict) -> Optional[dict]:
    """Cari baseline substation yang paling cocok untuk RUPTL row.

    Strategy:
      1. Exact stem match + same province → highest confidence
      2. Token subset match + same province → medium confidence
      3. None → new build
    """
    prov = (rup_row.get("province") or "").strip().lower()
    stem = substation_stem(rup_row.get("name", ""))
    tokens = substation_tokens(rup_row.get("name", ""))

    # Tier 1: exact stem
    if stem:
        hits = baseline_index.get((prov, stem))
        if hits:
            return hits[0]  # first hit

    # Tier 2: token overlap ≥ 0.75
    if tokens:
        best = None
        best_score = 0.0
        for cand in baseline_rows:
            if cand.get("_prov") != prov:
                continue
            cand_tokens = cand.get("_tokens", set())
            if not cand_tokens:
                continue
            common = tokens & cand_tokens
            if not common:
                continue
            score = len(common) / max(len(tokens | cand_tokens), 1)
            if score > best_score:
                best_score = score
                best = cand
        if best and best_score >= 0.75:
            return best
    return None


# ------------------------------------------------------------
# Classify
# ------------------------------------------------------------
def classify(rup_row: dict, baseline_match: Optional[dict]) -> str:
    action = (rup_row.get("action_type") or "").strip()
    if not rup_row.get("name"):
        return CLS_ORPHAN
    if not action:
        return CLS_ORPHAN
    if baseline_match is None:
        if action == "New":
            return CLS_NEW_BUILD
        # Ext/Uprate tanpa baseline match — mungkin nama beda; treat as new build
        return CLS_NEW_BUILD
    # Ada baseline match
    if action == "New":
        return CLS_RECLASSIFY_NEW  # RUPTL bilang New tapi baseline sudah punya
    if action == "Extension":
        return CLS_EXISTING_EXT
    if action == "Uprate":
        return CLS_EXISTING_UPRATE
    return CLS_ORPHAN


# ------------------------------------------------------------
# Report writer
# ------------------------------------------------------------
def write_report(out_path: Path, region: str, deltas: list[dict],
                  baseline_count: int, ruptl_count: int) -> None:
    lines = []
    lines.append(f"# Substation Delta Report — {region}")
    lines.append("")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- Baseline substations: {baseline_count}")
    lines.append(f"- RUPTL planning rows:   {ruptl_count}")
    lines.append("")
    counts = Counter(d["classification"] for d in deltas)
    lines.append("## Classification summary")
    lines.append("")
    for cls in TIER_ORDER:
        n = counts.get(cls, 0)
        lines.append(f"- **{cls}**: {n}")
    lines.append(f"- **TOTAL**: {len(deltas)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Details")
    lines.append("")

    def sort_key(d):
        # Sort by MVA desc within each class
        try:
            return -float(d["rup"].get("capacity_mva") or 0)
        except ValueError:
            return 0

    for cls in TIER_ORDER:
        items = [d for d in deltas if d["classification"] == cls]
        if not items:
            continue
        lines.append(f"### {cls} ({len(items)})")
        lines.append("")
        items.sort(key=sort_key)
        for d in items[:50]:  # cap to 50 per class
            r = d["rup"]
            m = d["baseline_match"]
            cap = r.get("capacity_mva") or "?"
            cod = r.get("target_cod_year") or "?"
            base_str = f" ↔ baseline: {m['id']} '{m['name']}'" if m else ""
            lines.append(f"- **{r['name']}** ({r['voltage_kv']} kV, {cap} MVA, COD {cod})"
                          f" — {r['province']}, {r['status']}{base_str}")
        if len(items) > 50:
            lines.append(f"- _(+{len(items) - 50} more, see CSV)_")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True,
                    help="region key (jamali/sumatra/…)")
    ap.add_argument("--write", action="store_true",
                    help="Write CSV + report (default: dry-run, print summary only)")
    opts = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    baseline_path = project_root / f"data/processed/substation_master_{opts.region}.csv"
    ruptl_path = project_root / f"data/processed/ruptl_substations_{opts.region}.csv"

    if not baseline_path.exists():
        print(f"Missing baseline: {baseline_path}", file=sys.stderr)
        return 2
    if not ruptl_path.exists():
        print(f"Missing RUPTL: {ruptl_path}", file=sys.stderr)
        return 2

    baseline_rows, baseline_index = load_baseline(baseline_path)
    with ruptl_path.open(encoding="utf-8-sig") as f:
        ruptl_rows = list(csv.DictReader(f))

    print(f"[delta] region={opts.region}")
    print(f"  baseline: {len(baseline_rows)} substations")
    print(f"  RUPTL:    {len(ruptl_rows)} planning rows")

    deltas = []
    for r in ruptl_rows:
        match = find_baseline_match(r, baseline_rows, baseline_index)
        cls = classify(r, match)
        deltas.append({"rup": r, "baseline_match": match, "classification": cls})

    print("\n== Classification summary ==")
    counts = Counter(d["classification"] for d in deltas)
    for cls in TIER_ORDER:
        print(f"  {cls:<20} {counts.get(cls, 0):>5}")
    print(f"  {'TOTAL':<20} {len(deltas):>5}")

    if not opts.write:
        print("\n(dry-run — pass --write to save CSV + report)")
        return 0

    # Write CSV
    csv_path = project_root / f"data/processed/substation_delta_{opts.region}.csv"
    csv_headers = [
        "ruptl_id", "name", "voltage_kv", "action_type", "capacity_mva",
        "target_cod_year", "status", "province",
        "classification", "baseline_id", "baseline_name",
        "source_page", "source_table",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_headers)
        w.writeheader()
        for d in deltas:
            r = d["rup"]
            m = d["baseline_match"] or {}
            w.writerow({
                "ruptl_id": r.get("id", ""),
                "name": r.get("name", ""),
                "voltage_kv": r.get("voltage_kv", ""),
                "action_type": r.get("action_type", ""),
                "capacity_mva": r.get("capacity_mva", ""),
                "target_cod_year": r.get("target_cod_year", ""),
                "status": r.get("status", ""),
                "province": r.get("province", ""),
                "classification": d["classification"],
                "baseline_id": m.get("id", ""),
                "baseline_name": m.get("name", ""),
                "source_page": r.get("source_page", ""),
                "source_table": r.get("source_table", ""),
            })
    print(f"\n  wrote {csv_path}")

    # Write report
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rep_path = project_root / f"data/reconciliation/substation_delta_{opts.region}_{ts}.md"
    write_report(rep_path, opts.region, deltas,
                  len(baseline_rows), len(ruptl_rows))
    print(f"  wrote {rep_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
