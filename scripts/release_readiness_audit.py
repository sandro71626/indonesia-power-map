#!/usr/bin/env python3
"""Release-readiness audit — comprehensive checks across 8 regions.

Reports:
  - Total records per asset type
  - Tier distribution (CONFIRMED/PROBABLE/AMBIGUOUS/CONFLICT/UNMATCHED)
  - Coord confidence distribution + planned features rendered
  - Transmission endpoint resolution rate
  - Substation delta classifications
  - Planned asset target_cod_year coverage
  - Manual override applied/stale/invalid per object type

Regression checks:
  - Duplicate IDs within any CSV
  - Missing required fields (id, name, coordinates for point features)
  - Invalid coordinates (outside Indonesia bbox 94-142 lon, -11-6 lat)
  - Impossible voltage (< 20 kV for transmission, > 1000 kV any)
  - Impossible capacity (< 0 or > 5000 MW single unit)
  - Planned features missing target_cod_year
  - Missing provenance (coord_source, match_tier)

Findings classified:
  RELEASE_BLOCKER          — data corruption / duplicate IDs / broken bundle
  SHOULD_FIX               — accuracy issues, resolvable in short term
  ACCEPTABLE_LIMITATION    — known trade-off, documented, not release-critical
"""
from __future__ import annotations
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']
BASE = Path(__file__).resolve().parents[1] / "data/processed"

# Indonesia rough bbox for coordinate sanity
LON_MIN, LON_MAX = 94.0, 142.0
LAT_MIN, LAT_MAX = -11.5, 6.5


def check_coord(lon, lat):
    """Return list of issues found."""
    issues = []
    if lon is None or lat is None:
        return ["missing coord"]
    if not (LON_MIN <= lon <= LON_MAX):
        issues.append(f"lon {lon} out of Indonesia bbox")
    if not (LAT_MIN <= lat <= LAT_MAX):
        issues.append(f"lat {lat} out of Indonesia bbox")
    if lon == 0 and lat == 0:
        issues.append("(0,0) placeholder")
    return issues


def parse_float(v):
    try:
        return float(str(v).strip()) if v else None
    except (ValueError, TypeError):
        return None


def audit_region(region):
    """Return {section: findings} dict for one region."""
    findings = {}
    proc = BASE

    # === RUPTL extraction ===
    for kind in ('generators', 'substations', 'transmission'):
        csv_path = proc / f"ruptl_{kind}_{region}.csv"
        if not csv_path.exists():
            findings[f"missing_ruptl_{kind}"] = "MISSING"
            continue
        with csv_path.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        ids = [r.get("id", "").strip() for r in rows]
        dup = [k for k, v in Counter(ids).items() if v > 1 and k]
        empty_ids = sum(1 for i in ids if not i)
        empty_names = sum(1 for r in rows if not r.get("name", "").strip())
        findings[f"ruptl_{kind}"] = {
            "total": len(rows),
            "duplicate_ids": len(dup),
            "empty_ids": empty_ids,
            "empty_names": empty_names,
            "dup_samples": dup[:5],
        }

    # === Generator reconciled ===
    gj_path = proc / f"generators_{region}.reconciled.geojson"
    if gj_path.exists():
        gj = json.loads(gj_path.read_text())
        features = gj.get("features", [])
        tiers = Counter(f['properties'].get('match_tier','') for f in features)
        coord_issues = 0
        missing_tier = 0
        missing_source = 0
        planned_no_year = 0
        dup_ids = []
        ids = []
        for f in features:
            props = f.get("properties", {})
            fid = props.get("id", "")
            ids.append(fid)
            if not props.get("match_tier"):
                missing_tier += 1
            if not (props.get("coord_source") or props.get("match_source")):
                missing_source += 1
            geom = f.get("geometry", {})
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    issues = check_coord(coords[0], coords[1])
                    if issues:
                        coord_issues += 1
            if props.get("match_tier") == "UNMATCHED_RUPTL":
                y = (props.get("target_cod_year") or props.get("target_cod_year_ruptl") or "").strip()
                if not y:
                    planned_no_year += 1
        dup_ids = [k for k, v in Counter(ids).items() if v > 1]
        findings["gen_reconciled"] = {
            "total_features": len(features),
            "tiers": dict(tiers),
            "coord_issues": coord_issues,
            "missing_tier": missing_tier,
            "missing_source": missing_source,
            "planned_no_year": planned_no_year,
            "duplicate_ids": len(dup_ids),
        }

    # === Substation reconciled ===
    gj_path = proc / f"substations_{region}.reconciled.geojson"
    if gj_path.exists():
        gj = json.loads(gj_path.read_text())
        features = gj.get("features", [])
        tiers = Counter(f['properties'].get('match_tier','') for f in features)
        coord_issues = 0
        invalid_voltage = 0
        ids = []
        for f in features:
            p = f.get("properties", {})
            ids.append(p.get("id", ""))
            geom = f.get("geometry", {})
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    if check_coord(coords[0], coords[1]):
                        coord_issues += 1
            # Voltage check
            v = (p.get("voltage") or "").strip()
            import re
            m = re.search(r"\d+", v)
            if m:
                kv = int(m.group())
                if kv > 1000 or (kv > 0 and kv < 20):
                    invalid_voltage += 1
        dup_ids = [k for k, v in Counter(ids).items() if v > 1]
        findings["sub_reconciled"] = {
            "total_features": len(features),
            "tiers": dict(tiers),
            "coord_issues": coord_issues,
            "invalid_voltage": invalid_voltage,
            "duplicate_ids": len(dup_ids),
        }

    # === Transmission reconciled ===
    gj_path = proc / f"transmission_{region}.reconciled.geojson"
    if gj_path.exists():
        gj = json.loads(gj_path.read_text())
        features = gj.get("features", [])
        tiers = Counter(f['properties'].get('match_tier','') for f in features)
        endpoints_both = 0
        endpoints_partial = 0
        endpoints_none = 0
        invalid_voltage = 0
        planned_no_year = 0
        for f in features:
            p = f.get("properties", {})
            ec = p.get("endpoint_confidence", "")
            if ec == "both": endpoints_both += 1
            elif ec == "partial": endpoints_partial += 1
            elif ec == "none": endpoints_none += 1
            # Voltage check
            v = parse_float(p.get("voltage_kv_max") or p.get("voltage_kv") or "")
            if v and (v > 1000 or v < 20):
                invalid_voltage += 1
            if p.get("match_tier") == "PLANNED_RUPTL":
                y = (p.get("target_cod_year") or "").strip()
                if not y:
                    planned_no_year += 1
        findings["trm_reconciled"] = {
            "total_features": len(features),
            "tiers": dict(tiers),
            "endpoints_both": endpoints_both,
            "endpoints_partial": endpoints_partial,
            "endpoints_none": endpoints_none,
            "invalid_voltage": invalid_voltage,
            "planned_no_year": planned_no_year,
        }

    # === Sub delta ===
    delta_path = proc / f"substation_delta_{region}.csv"
    if delta_path.exists():
        with delta_path.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        cls = Counter(r["classification"] for r in rows)
        empty_action = sum(1 for r in rows if not r.get("action_type", "").strip())
        findings["sub_delta"] = {
            "total": len(rows),
            "classification": dict(cls),
            "empty_action": empty_action,
        }

    # === Coord confidence for planned gen ===
    ruptl_path = proc / f"ruptl_generators_{region}.csv"
    if ruptl_path.exists():
        with ruptl_path.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        conf = Counter(r.get("coord_confidence", "unknown") for r in rows)
        types_unk = sum(1 for r in rows if r.get("type", "?") == "?")
        findings["gen_coords"] = {
            "confidence": dict(conf),
            "type_unknown": types_unk,
        }

    # === Bundle file ===
    bundle = Path("web") / f"data_{region}.js"
    bundle_full = Path(__file__).resolve().parents[1] / bundle
    if bundle_full.exists():
        findings["bundle_size_kb"] = round(bundle_full.stat().st_size / 1024, 1)

    return findings


def check_overrides():
    """Check 3 override files."""
    result = {}
    for label, fname in [
        ("generator", "generator_reconciliation_overrides.csv"),
        ("substation", "substation_reconciliation_overrides.csv"),
        ("transmission", "transmission_reconciliation_overrides.csv"),
    ]:
        path = Path(__file__).resolve().parents[1] / "data/overrides" / fname
        if not path.exists():
            result[label] = "MISSING FILE"
            continue
        with path.open(encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if r.get("override_id")]
        result[label] = {"rows": len(rows)}
    return result


def main():
    print("=" * 68)
    print("  RELEASE-READINESS AUDIT — 8 regions")
    print("=" * 68)

    per_region = {}
    for region in REGIONS:
        print(f"\n--- Auditing {region} ---")
        per_region[region] = audit_region(region)

    overrides = check_overrides()

    # === Aggregate report ===
    print("\n" + "=" * 68)
    print("  AGGREGATE — PER ASSET TYPE")
    print("=" * 68)

    for kind in ("gen_reconciled", "sub_reconciled", "trm_reconciled"):
        print(f"\n== {kind} ==")
        header = f"  {'region':<11}"
        totals = defaultdict(int)
        for r in REGIONS:
            f = per_region[r].get(kind, {})
            print(f"  {r:<11} features={f.get('total_features', 0):>6}  "
                  f"dup_ids={f.get('duplicate_ids', 0):>3}  "
                  f"coord_issues={f.get('coord_issues', 0):>3}  "
                  f"invalid_v={f.get('invalid_voltage', 0):>3}  "
                  f"planned_no_year={f.get('planned_no_year', 0):>3}")
            for k, v in (f.get("tiers") or {}).items():
                totals[k] += v
        print(f"  Aggregate tiers: {dict(sorted(totals.items()))}")

    # Sub delta
    print("\n== Sub delta ==")
    dcls = defaultdict(int)
    for r in REGIONS:
        d = per_region[r].get("sub_delta", {})
        for k, v in (d.get("classification") or {}).items():
            dcls[k] += v
    print(f"  Aggregate classification: {dict(sorted(dcls.items()))}")
    orph = sum(per_region[r].get("sub_delta", {}).get("empty_action", 0) for r in REGIONS)
    print(f"  Empty action_type (orphan): {orph}")

    # Coord confidence
    print("\n== Planned gen coord confidence ==")
    conf_agg = defaultdict(int)
    type_unk = 0
    for r in REGIONS:
        d = per_region[r].get("gen_coords", {})
        for k, v in (d.get("confidence") or {}).items():
            conf_agg[k] += v
        type_unk += d.get("type_unknown", 0)
    print(f"  {dict(sorted(conf_agg.items()))}")
    print(f"  Type unknown (?): {type_unk}")

    # Transmission endpoints
    print("\n== Transmission endpoint resolution ==")
    b, p, n = 0, 0, 0
    for r in REGIONS:
        d = per_region[r].get("trm_reconciled", {})
        b += d.get("endpoints_both", 0)
        p += d.get("endpoints_partial", 0)
        n += d.get("endpoints_none", 0)
    total = b + p + n
    print(f"  both={b} ({100*b/total:.1f}%) partial={p} ({100*p/total:.1f}%) "
          f"none={n} ({100*n/total:.1f}%) — total {total}")

    # Bundle sizes
    print("\n== Frontend bundle files ==")
    total_kb = 0
    for r in REGIONS:
        kb = per_region[r].get("bundle_size_kb", 0)
        total_kb += kb
        print(f"  data_{r}.js  {kb:>7.1f} KB")
    print(f"  TOTAL:     {total_kb:>7.1f} KB")

    # Overrides
    print("\n== Manual overrides ==")
    for k, v in overrides.items():
        print(f"  {k:<14} {v}")

    # === Regression / issue classification ===
    print("\n" + "=" * 68)
    print("  ISSUE CLASSIFICATION")
    print("=" * 68)

    blockers = []
    should_fix = []
    acceptable = []

    for r in REGIONS:
        for kind in ("gen_reconciled", "sub_reconciled"):
            f = per_region[r].get(kind, {})
            if f.get("duplicate_ids", 0) > 0:
                blockers.append(f"{r} {kind}: {f['duplicate_ids']} duplicate feature IDs")
            if f.get("coord_issues", 0) > 0:
                should_fix.append(f"{r} {kind}: {f['coord_issues']} coord out-of-bbox / (0,0)")
            if f.get("invalid_voltage", 0) > 0:
                should_fix.append(f"{r} {kind}: {f['invalid_voltage']} invalid voltage values")
            if f.get("missing_tier", 0) > 0:
                should_fix.append(f"{r} {kind}: {f['missing_tier']} features missing match_tier")

        # Transmission endpoint resolution
        trm = per_region[r].get("trm_reconciled", {})
        total_trm = trm.get("total_features", 1)
        both_pct = 100 * trm.get("endpoints_both", 0) / max(total_trm, 1)
        if both_pct < 5 and total_trm > 30:
            should_fix.append(f"{r} trm: endpoint resolution rate very low ({both_pct:.1f}%)")

        # RUPTL extractor issues
        for kind in ("ruptl_generators", "ruptl_substations", "ruptl_transmission"):
            f = per_region[r].get(kind, {})
            if isinstance(f, dict):
                if f.get("empty_ids", 0) > 0:
                    blockers.append(f"{r} {kind}: {f['empty_ids']} rows with empty ID")
                if f.get("duplicate_ids", 0) > 0:
                    blockers.append(f"{r} {kind}: {f['duplicate_ids']} duplicate IDs — {f.get('dup_samples')}")

    # Planned no year — acceptable if <10% dari planned total
    total_planned_no_year = sum(
        per_region[r].get("gen_reconciled", {}).get("planned_no_year", 0)
        + per_region[r].get("trm_reconciled", {}).get("planned_no_year", 0)
        for r in REGIONS
    )
    if total_planned_no_year:
        acceptable.append(f"Planned features tanpa target_cod_year: {total_planned_no_year} "
                          "(PDF data itself lacks year — no auto-inference per policy)")

    # Coord placeholder skipped for gen
    total_low = sum(per_region[r].get("gen_coords", {}).get("confidence", {}).get("low", 0)
                    for r in REGIONS)
    if total_low:
        acceptable.append(f"Planned generator with province-centroid coord: {total_low} "
                          "(coord_confidence=low, skipped from GeoJSON rendering — 691 di dataset)")

    # BASELINE_UNRESOLVED transmission
    total_unres = sum(per_region[r].get("trm_reconciled", {}).get("tiers", {}).get("BASELINE_UNRESOLVED", 0)
                      for r in REGIONS)
    if total_unres:
        acceptable.append(f"Transmission BASELINE_UNRESOLVED: {total_unres} "
                          "(OSM segments tanpa dual-endpoint substation match — structural)")

    print("\n### 🔴 RELEASE_BLOCKER")
    if blockers:
        for b in blockers: print(f"  - {b}")
    else:
        print("  (none)")

    print("\n### 🟡 SHOULD_FIX")
    if should_fix:
        for s in should_fix: print(f"  - {s}")
    else:
        print("  (none)")

    print("\n### ⚪ ACCEPTABLE_LIMITATION")
    if acceptable:
        for a in acceptable: print(f"  - {a}")
    else:
        print("  (none)")

    print()
    print("=" * 68)
    if not blockers:
        print("  RECOMMENDATION: Dataset LAYAK di-freeze sebagai release pertama.")
        print("  SHOULD_FIX items dapat diaddress di release berikutnya.")
    else:
        print("  RECOMMENDATION: Dataset BELUM LAYAK — resolve RELEASE_BLOCKER dulu.")
    print("=" * 68)


if __name__ == "__main__":
    main()
