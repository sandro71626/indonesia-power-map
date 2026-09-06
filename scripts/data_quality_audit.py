#!/usr/bin/env python3
"""Data quality audit across all 8 regions.

Inspect reconciliation results untuk gen/sub/trm, kategorikan issues,
dan generate prioritized review queue. Tidak auto-resolve — hanya
identify + recommend action (algorithmic fix vs manual override).

Kategori issue:
  FALSE_POSITIVE     — algorithm made match tapi kemungkinan salah
                       (naming variant, colocated but different asset)
  FALSE_NEGATIVE     — algorithm miss match tapi kemungkinan match ada
                       (high-MW asset UNMATCHED, common name variants)
  EXTRACTOR_ISSUE    — parse-level bug (bad number, generic endpoint,
                       missing voltage, aggregate row)
  GEOCODING_ISSUE    — coord fallback ke centroid (planned tidak render)
  AMBIGUOUS_DATA     — PDF data itself unclear (CONFLICT tier, capacity
                       mismatch dengan valid values dari 2 sumber)
  GENUINELY_UNMATCHED — real new project tanpa baseline (mis. RUPTL
                       kuota tersebar, planned yang belum di OSM)

Output:
    data/reconciliation/data_quality_audit_{ts}.md — full review queue

Usage:
    python3 scripts/data_quality_audit.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REGIONS = ['jamali', 'sumatra', 'kalimantan', 'sulawesi',
           'maluku', 'papua', 'ntb', 'ntt']
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROC = PROJECT_ROOT / "data/processed"


# ------------------------------------------------------------
# Categorization heuristics
# ------------------------------------------------------------
GENERIC_ENDPOINT_RE = re.compile(
    r"\b(inc|tx|kuota|tersebar|eksisting|eksisiting|existing|tap)\b",
    re.IGNORECASE)


def is_generic_endpoint(name: str) -> bool:
    return bool(name and GENERIC_ENDPOINT_RE.search(name))


def parse_float(v):
    try:
        return float(str(v).strip()) if v else None
    except (ValueError, TypeError):
        return None


def haversine_km(lon1, lat1, lon2, lat2):
    from math import sin, cos, sqrt, asin, pi
    p = pi / 180
    h = (sin((lat2 - lat1) * p / 2) ** 2
         + cos(lat1 * p) * cos(lat2 * p) * sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371.0088 * asin(sqrt(max(0.0, h)))


# ------------------------------------------------------------
# Generator audit
# ------------------------------------------------------------
def audit_generators(region: str) -> dict:
    """Return {category: [issues]} untuk region ini."""
    path = PROC / f"generator_master_reconciled_{region}.csv"
    if not path.exists():
        return {}
    result = defaultdict(list)
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        tier = r.get("match_tier", "")
        name = r.get("name", "").strip()
        mw = parse_float(r.get("capacity_mw"))
        ruptl_id = r.get("ruptl_id", "")
        ipm_id = r.get("ipm_id", "")

        if tier == "AMBIGUOUS":
            result["AMBIGUOUS_DATA"].append({
                "region": region, "kind": "gen", "id": ipm_id or ruptl_id,
                "name": name, "mw": mw,
                "reason": r.get("match_reason", ""),
                "action": "Manual review needed — multiple candidates in threshold",
            })
        elif tier == "CONFLICT":
            has_cap = r.get("has_capacity_conflict", "") == "true"
            has_type = r.get("has_type_conflict", "") == "true"
            typ = "capacity" if has_cap else ("type" if has_type else "unknown")
            result["AMBIGUOUS_DATA"].append({
                "region": region, "kind": "gen", "id": f"{ipm_id} ↔ {ruptl_id}",
                "name": name, "mw": mw,
                "reason": f"{typ} conflict: OSM {r.get('capacity_mw_ipm')} MW vs RUPTL {r.get('capacity_mw_ruptl')} MW",
                "action": "Manual override USE_RUPTL_VALUE or KEEP_BASELINE",
            })
        elif tier == "UNMATCHED_RUPTL" and mw and mw >= 100:
            # High MW planned yang tidak match ada 2 kemungkinan:
            # - Genuinely new (not in OSM yet) → GENUINELY_UNMATCHED
            # - Should have matched but missed → FALSE_NEGATIVE
            # Heuristik: kalau nama generic (Kuota Tersebar, dll) → genuinely unmatched planned
            #            kalau nama specific → possible false negative
            n_lower = name.lower()
            if any(w in n_lower for w in ("kuota", "tersebar", "hybrid")):
                result["GENUINELY_UNMATCHED"].append({
                    "region": region, "kind": "gen", "id": ruptl_id,
                    "name": name, "mw": mw,
                    "reason": "Planned aggregate/kuota placeholder — expected unmatched",
                    "action": "No action (this is expected)",
                })
            else:
                result["FALSE_NEGATIVE"].append({
                    "region": region, "kind": "gen", "id": ruptl_id,
                    "name": name, "mw": mw,
                    "reason": "High-MW planned without baseline match — check for naming variant",
                    "action": "Manual review + potential FORCE_MATCH",
                })
        elif tier == "UNMATCHED_IPM" and mw and mw >= 100:
            result["GENUINELY_UNMATCHED"].append({
                "region": region, "kind": "gen", "id": ipm_id,
                "name": name, "mw": mw,
                "reason": "High-MW OSM plant without RUPTL entry — likely pre-2025 existing not in current plan",
                "action": "No action (existing outside RUPTL scope)",
            })
        elif tier == "UNMATCHED_RUPTL" and (r.get("type") == "?" or r.get("type") == ""):
            # Extractor didn't get type
            result["EXTRACTOR_ISSUE"].append({
                "region": region, "kind": "gen", "id": ruptl_id,
                "name": name, "mw": mw,
                "reason": "Type = '?' (extractor couldn't infer PLT category)",
                "action": "Extend name_stem heuristics or update PLANT_LABEL",
            })

    return result


# ------------------------------------------------------------
# Substation audit — from delta CSV
# ------------------------------------------------------------
def audit_substations(region: str) -> dict:
    path = PROC / f"substation_delta_{region}.csv"
    if not path.exists():
        return {}
    result = defaultdict(list)
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        cls = r.get("classification", "")
        ruptl_id = r.get("ruptl_id", "")
        name = r.get("name", "").strip()
        cap_mva = parse_float(r.get("capacity_mva"))
        voltage = r.get("voltage_kv", "").strip()

        if cls == "ORPHAN":
            # Row extracted tapi action_type kosong / tidak dikenal
            result["EXTRACTOR_ISSUE"].append({
                "region": region, "kind": "sub", "id": ruptl_id,
                "name": name, "mw": cap_mva,
                "reason": f"Action type kosong ({r.get('action_type', 'empty')})",
                "action": "Check RUPTL PDF Lingkup column parsing",
            })
        elif cls == "RECLASSIFY_NEW":
            baseline = r.get("baseline_name", "")
            # RUPTL bilang NEW tapi baseline sudah ada dengan nama mirip
            result["FALSE_POSITIVE"].append({
                "region": region, "kind": "sub", "id": f"{ruptl_id} ↔ {r.get('baseline_id')}",
                "name": f"{name} ↔ {baseline}",
                "mw": cap_mva,
                "reason": "Naming variant — baseline exists, RUPTL flagged as NEW build",
                "action": "Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely different",
            })
        elif cls == "NEW_BUILD":
            # Check if this is likely a genuinely new build vs a name variant miss
            # Heuristic: cek if name generic
            n_lower = name.lower()
            if any(w in n_lower for w in ("kuota", "tersebar", "eksisting")):
                # Placeholder aggregate → likely no baseline expected
                pass  # tidak dilaporkan (expected)
            elif cap_mva and cap_mva >= 60:
                # High capacity NEW_BUILD — verify tidak ada baseline variant
                result["FALSE_NEGATIVE"].append({
                    "region": region, "kind": "sub", "id": ruptl_id,
                    "name": name, "mw": cap_mva,
                    "reason": f"High-MVA NEW_BUILD ({voltage} kV, {cap_mva} MVA) — check for baseline naming variant",
                    "action": "Manual review + potential FORCE_MATCH",
                })

    return result


# ------------------------------------------------------------
# Transmission audit — from audit CSV
# ------------------------------------------------------------
def audit_transmission(region: str) -> dict:
    path = PROC.parent / f"reconciliation/transmission_audit_{region}.csv"
    result = defaultdict(list)
    if not path.exists():
        return result
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        issues = r.get("issues", "").split(",")
        length = parse_float(r.get("length_km"))
        straight = parse_float(r.get("straight_km"))
        ratio = parse_float(r.get("ratio"))
        ruptl_id = r.get("ruptl_id", "")
        from_bus = r.get("from_bus", "")
        to_bus = r.get("to_bus", "")
        vkv = r.get("voltage_kv", "")

        # Classify by dominant issue
        if "GENERIC_ENDPOINT" in issues:
            # Endpoint contains Inc./Tx./Kuota/Tersebar → extractor gave up
            result["EXTRACTOR_ISSUE"].append({
                "region": region, "kind": "trm", "id": ruptl_id,
                "name": f"{from_bus} → {to_bus}", "mw": length,
                "reason": f"Generic endpoint name → cannot geocode reliably",
                "action": "Skip (already skipped in phase 2) OR improve extractor Inc.-parsing",
            })
        elif "RATIO_TOO_LOW" in issues:
            # Stated length < straight distance = impossible → extractor bug
            result["EXTRACTOR_ISSUE"].append({
                "region": region, "kind": "trm", "id": ruptl_id,
                "name": f"{from_bus} → {to_bus}",
                "mw": length,
                "reason": f"Stated {length} km < straight-line {straight} km (impossible)",
                "action": "Check RUPTL PDF row — likely decimal or unit parse bug",
            })
        elif "RATIO_TOO_HIGH" in issues:
            # Stated length >> straight — bisa jadi aggregate multi-segment
            # atau endpoint match salah
            if length and length > 200:
                result["EXTRACTOR_ISSUE"].append({
                    "region": region, "kind": "trm", "id": ruptl_id,
                    "name": f"{from_bus} → {to_bus}",
                    "mw": length,
                    "reason": f"Length {length} km outlier — likely aggregate row or PDF typo",
                    "action": "Verify PDF page, potentially IGNORE_RUPTL_ROW",
                })
            else:
                result["AMBIGUOUS_DATA"].append({
                    "region": region, "kind": "trm", "id": ruptl_id,
                    "name": f"{from_bus} → {to_bus}",
                    "mw": length,
                    "reason": f"Ratio {ratio}× — cable routing atau endpoint gazetteer imprecise",
                    "action": "Manual verify, may be legitimate SKTT routing",
                })
        elif "NO_VOLTAGE" in issues:
            result["EXTRACTOR_ISSUE"].append({
                "region": region, "kind": "trm", "id": ruptl_id,
                "name": f"{from_bus} → {to_bus}", "mw": length,
                "reason": "Voltage kosong (column detection failed)",
                "action": "Check extractor column_map for this table variant",
            })
        elif "LENGTH_OUTLIER" in issues:
            # Only length outlier, no ratio issue = mungkin legit
            result["GENUINELY_UNMATCHED"].append({
                "region": region, "kind": "trm", "id": ruptl_id,
                "name": f"{from_bus} → {to_bus}", "mw": length,
                "reason": f"Length {length} km — verify inter-island / EHV route",
                "action": "Likely legitimate (Bali crossing, EHV inter-region), no action",
            })

    return result


# ------------------------------------------------------------
# Geocoding gap — from RUPTL gen CSV
# ------------------------------------------------------------
def audit_geocoding(region: str) -> dict:
    path = PROC / f"ruptl_generators_{region}.csv"
    result = defaultdict(list)
    if not path.exists():
        return result
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    placeholder = sum(1 for r in rows if r.get("coord_confidence") == "low")
    if placeholder > 0:
        result["GEOCODING_ISSUE"].append({
            "region": region, "kind": "gen", "id": "(bulk)",
            "name": f"{placeholder} planned generators fallback ke province centroid",
            "mw": None,
            "reason": f"Gazetteer match miss → coord = province centroid + jitter",
            "action": "Build additional gazetteer (BIG shapefile, PLN annual report locations)",
        })
    return result


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    all_findings = defaultdict(list)
    per_region = defaultdict(lambda: defaultdict(int))

    for region in REGIONS:
        for auditor in (audit_generators, audit_substations,
                          audit_transmission, audit_geocoding):
            findings = auditor(region)
            for cat, items in findings.items():
                all_findings[cat].extend(items)
                per_region[region][cat] += len(items)

    # Print summary
    print(f"{'=' * 60}")
    print(f"  DATA QUALITY AUDIT — 8 regions")
    print(f"  Generated: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'=' * 60}\n")

    print("== Per category ==")
    for cat in ["EXTRACTOR_ISSUE", "FALSE_POSITIVE", "FALSE_NEGATIVE",
                 "AMBIGUOUS_DATA", "GEOCODING_ISSUE", "GENUINELY_UNMATCHED"]:
        n = len(all_findings.get(cat, []))
        print(f"  {cat:<24} {n:>5}")

    print("\n== Per region × category ==")
    print(f"  {'region':<12} {'EXT':>4} {'FP':>4} {'FN':>4} {'AMB':>4} {'GEO':>4} {'GEN':>4}")
    for r in REGIONS:
        counts = per_region[r]
        print(f"  {r:<12} "
              f"{counts.get('EXTRACTOR_ISSUE',0):>4} "
              f"{counts.get('FALSE_POSITIVE',0):>4} "
              f"{counts.get('FALSE_NEGATIVE',0):>4} "
              f"{counts.get('AMBIGUOUS_DATA',0):>4} "
              f"{counts.get('GEOCODING_ISSUE',0):>4} "
              f"{counts.get('GENUINELY_UNMATCHED',0):>4}")

    # Write full report
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = PROJECT_ROOT / f"data/reconciliation/data_quality_audit_{ts}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Data Quality Audit — {datetime.now(timezone.utc).isoformat()}",
        "",
        "Cross-region inspection of reconciliation results (gen/sub/trm).",
        "Cases classified into 6 categories; each finding lists suggested",
        "action (algorithmic fix, manual override, or no-action).",
        "",
        "## Summary",
        "",
        "| Category | Total |",
        "| --- | ---: |",
    ]
    for cat in ["EXTRACTOR_ISSUE", "FALSE_POSITIVE", "FALSE_NEGATIVE",
                 "AMBIGUOUS_DATA", "GEOCODING_ISSUE", "GENUINELY_UNMATCHED"]:
        lines.append(f"| {cat} | {len(all_findings.get(cat, []))} |")
    lines.append("")

    lines.append("## Per region")
    lines.append("")
    lines.append("| Region | EXTRACTOR | FALSE_POS | FALSE_NEG | AMBIGUOUS | GEOCODING | GENUINELY_UNMATCHED |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in REGIONS:
        c = per_region[r]
        lines.append(f"| {r} | {c.get('EXTRACTOR_ISSUE',0)} | "
                      f"{c.get('FALSE_POSITIVE',0)} | {c.get('FALSE_NEGATIVE',0)} | "
                      f"{c.get('AMBIGUOUS_DATA',0)} | {c.get('GEOCODING_ISSUE',0)} | "
                      f"{c.get('GENUINELY_UNMATCHED',0)} |")
    lines.append("")

    for cat in ["EXTRACTOR_ISSUE", "FALSE_POSITIVE", "FALSE_NEGATIVE",
                 "AMBIGUOUS_DATA", "GEOCODING_ISSUE", "GENUINELY_UNMATCHED"]:
        items = all_findings.get(cat, [])
        if not items:
            continue
        # Sort by MW desc (bigger impact first)
        items.sort(key=lambda x: -(x.get("mw") or 0))
        lines.append(f"## {cat} ({len(items)})")
        lines.append("")
        lines.append("| Region | Kind | ID | Name | MW/km | Reason | Action |")
        lines.append("| --- | --- | --- | --- | ---: | --- | --- |")
        for it in items[:80]:  # cap per category
            mw = f"{it['mw']:.1f}" if it.get("mw") is not None else "—"
            lines.append(f"| {it['region']} | {it['kind']} | `{it['id']}` | "
                          f"{it['name'][:40]} | {mw} | {it['reason'][:70]} | "
                          f"{it['action'][:60]} |")
        if len(items) > 80:
            lines.append(f"\n_(+{len(items) - 80} more, see per-region reports)_")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Wrote full report → {out_path}")


if __name__ == "__main__":
    main()
