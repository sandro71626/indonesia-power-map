#!/usr/bin/env python3
"""Audit PLANNED_RUPTL transmission features untuk deteksi extraction bugs.

Semua PLANNED_RUPTL feature adalah 2-point LineString by construction
(gambar dari substation A ke B). Kalau ada bug di extractor (voltage
salah, length salah, endpoint keliru) baris itu tetap ke-render sebagai
garis lurus — susah dibedakan visually dari yang real.

Script ini flag features yang secara statistik mencurigakan:

  A. RATIO_TOO_LOW      — straight_distance > stated_length_km
                          (impossible — bug ekstraksi length)
  B. RATIO_TOO_HIGH     — ratio (stated/straight) > 3.0
                          (endpoint gazetteer match salah? RUPTL length aggregate?)
  C. LENGTH_OUTLIER     — length_km > threshold (default 150 km)
                          150 kV jarang lebih dari 150 km — bisa jadi
                          angka digabung 2 baris atau typo
  D. NO_VOLTAGE         — voltage_kv kosong (extractor kehilangan kolom)
  E. LOOP               — from_bus == to_bus
  F. GENERIC_ENDPOINT   — endpoint bukan real substation ("Inc.", "Tx.",
                          "Kuota", "Tersebar", "Eksisting")
  G. LOW_VOLTAGE_LONG   — voltage < 150 kV tapi > 100 km (jarang secara
                          teknis; kemungkinan salah baca voltage)

Output: table di stdout, sorted by severity + rank.
Optional --csv untuk simpan ke file untuk review manual.

Usage:
    python3 scripts/audit_planned_transmission.py --region jamali
    python3 scripts/audit_planned_transmission.py --region jamali --csv audit.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import haversine_km  # noqa: E402


# ------------------------------------------------------------
# Issue detectors
# ------------------------------------------------------------
GENERIC_ENDPOINT_TOKENS = frozenset({
    "inc", "tx", "kuota", "tersebar", "eksisting", "eksisiting",
    "existing", "baru", "new", "tap",
})


def is_generic_endpoint(name: str) -> bool:
    """True kalau nama endpoint mengandung generic placeholder token."""
    if not name:
        return True
    n = name.lower()
    for tok in GENERIC_ENDPOINT_TOKENS:
        if re.search(rf"\b{tok}\b", n):
            return True
    return False


def voltage_int(v: str) -> Optional[int]:
    m = re.search(r"\d+", str(v or ""))
    return int(m.group()) if m else None


def parse_float(v) -> Optional[float]:
    try:
        s = str(v or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


def audit_feature(f: dict) -> list[str]:
    """Return list of issue codes untuk 1 feature. Empty list = clean."""
    p = f.get("properties", {})
    coords = (f.get("geometry") or {}).get("coordinates") or []
    if len(coords) < 2 or len(coords[0]) < 2 or len(coords[-1]) < 2:
        return ["INVALID_GEOM"]

    issues = []
    length_km = parse_float(p.get("length_km"))
    v_kv = voltage_int(p.get("voltage_kv"))
    from_bus = (p.get("from_bus") or "").strip()
    to_bus = (p.get("to_bus") or "").strip()

    # Straight-line distance (haversine)
    lonA, latA = coords[0][0], coords[0][1]
    lonB, latB = coords[-1][0], coords[-1][1]
    straight_km = haversine_km((lonA, latA), (lonB, latB))
    p["_straight_km"] = round(straight_km, 2)
    p["_ratio"] = (round(length_km / straight_km, 2)
                    if length_km and straight_km > 0.1 else None)

    # A. RATIO_TOO_LOW: straight > stated (impossible)
    if length_km is not None and straight_km > 0.1:
        if length_km < straight_km * 0.85:  # 15% tolerance for rounding
            issues.append("RATIO_TOO_LOW")

    # B. RATIO_TOO_HIGH: stated way longer than straight
    if length_km is not None and straight_km > 0.1:
        ratio = length_km / straight_km
        if ratio > 3.0:
            issues.append("RATIO_TOO_HIGH")

    # C. LENGTH_OUTLIER: unusually long
    if length_km is not None and length_km > 150:
        issues.append("LENGTH_OUTLIER")

    # D. NO_VOLTAGE
    if v_kv is None:
        issues.append("NO_VOLTAGE")

    # E. LOOP
    if from_bus and to_bus and from_bus.lower() == to_bus.lower():
        issues.append("LOOP")

    # F. GENERIC_ENDPOINT
    if is_generic_endpoint(from_bus) or is_generic_endpoint(to_bus):
        issues.append("GENERIC_ENDPOINT")

    # G. LOW_VOLTAGE_LONG
    if v_kv is not None and v_kv < 150 and length_km is not None and length_km > 100:
        issues.append("LOW_VOLTAGE_LONG")

    return issues


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
SEVERITY = {
    "INVALID_GEOM": 5,
    "RATIO_TOO_LOW": 4,
    "LOOP": 4,
    "NO_VOLTAGE": 3,
    "RATIO_TOO_HIGH": 3,
    "LENGTH_OUTLIER": 2,
    "LOW_VOLTAGE_LONG": 2,
    "GENERIC_ENDPOINT": 1,
}


def audit(region: str, project_root: Path,
          csv_out: Optional[Path] = None) -> int:
    gj_path = project_root / f"data/processed/transmission_{region}.reconciled.geojson"
    if not gj_path.exists():
        print(f"missing: {gj_path}", file=sys.stderr)
        return 2

    gj = json.loads(gj_path.read_text(encoding="utf-8"))
    features = gj.get("features", [])
    planned = [f for f in features
               if f.get("properties", {}).get("match_tier") == "PLANNED_RUPTL"]
    print(f"[audit] region={region}, {len(planned)} PLANNED_RUPTL features")

    flagged = []
    for f in planned:
        issues = audit_feature(f)
        if issues:
            p = f["properties"]
            flagged.append({
                "ruptl_id": p.get("ruptl_id", ""),
                "from_bus": p.get("from_bus", ""),
                "to_bus": p.get("to_bus", ""),
                "voltage_kv": p.get("voltage_kv", ""),
                "length_km": p.get("length_km", ""),
                "straight_km": p.get("_straight_km", ""),
                "ratio": p.get("_ratio", ""),
                "action_type": p.get("action_type", ""),
                "target_cod_year": p.get("target_cod_year", ""),
                "province": p.get("province", ""),
                "source_page": p.get("source_page", ""),
                "issues": ",".join(issues),
                "severity": max(SEVERITY.get(i, 0) for i in issues),
            })

    # Sort by severity desc, then by ratio (extreme first)
    flagged.sort(key=lambda x: (-x["severity"],
                                 -(x["ratio"] if isinstance(x["ratio"], (int, float)) else 0)))

    print(f"  flagged: {len(flagged)} / {len(planned)} "
          f"({100*len(flagged)/len(planned):.0f}%)")
    print()

    from collections import Counter
    issue_counts: Counter = Counter()
    for row in flagged:
        for i in row["issues"].split(","):
            issue_counts[i] += 1
    print("  issues breakdown:")
    for issue, n in sorted(issue_counts.items(),
                             key=lambda x: (-SEVERITY.get(x[0], 0), -x[1])):
        print(f"    {issue:<20} {n:>4}  (severity {SEVERITY.get(issue, 0)})")

    # Top 20 offenders
    print()
    print("  === TOP 20 offenders (highest severity first) ===")
    print(f"  {'#':<3} {'ruptl_id':<22} {'from → to':<45} {'kV':>4} {'len':>5} {'straight':>8} {'ratio':>5}  {'issues'}")
    for i, r in enumerate(flagged[:20], 1):
        pair = f"{r['from_bus'][:20]} → {r['to_bus'][:20]}"
        print(f"  {i:<3} {r['ruptl_id']:<22} {pair:<45} {r['voltage_kv'] or '?':>4} "
              f"{str(r['length_km'])[:5]:>5} {str(r['straight_km'])[:6]:>8} "
              f"{str(r['ratio'])[:5]:>5}  {r['issues']}")

    if csv_out:
        headers = ["severity", "ruptl_id", "from_bus", "to_bus", "voltage_kv",
                   "length_km", "straight_km", "ratio", "action_type",
                   "target_cod_year", "province", "source_page", "issues"]
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        with csv_out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in flagged:
                w.writerow({k: r.get(k, "") for k in headers})
        print(f"\n  wrote full audit → {csv_out}")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    ap.add_argument("--csv", type=Path, default=None,
                    help="Simpan full audit ke CSV file")
    opts = ap.parse_args()
    return audit(opts.region, Path(__file__).resolve().parents[1], opts.csv)


if __name__ == "__main__":
    raise SystemExit(main())
