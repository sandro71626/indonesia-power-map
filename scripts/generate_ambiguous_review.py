#!/usr/bin/env python3
"""Generate detailed structured review untuk 11 AMBIGUOUS PLTP clusters.

Per cluster tampilkan semua metadata yang perlu untuk analyst decide:
  MERGE_AS_ONE_COMPLEX | KEEP_SEPARATE | PARTIAL_MERGE | NEED_MORE_EVIDENCE

Priority sort:
  1. Highest potential double-counting capacity (sum of MW at risk)
  2. Highest number of unnamed features
  3. Largest spatial spread (max pairwise distance)

Output: data/reconciliation/ambiguous_pltp_full_review_{ts}.md
Tidak modify data.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from math import sin, cos, sqrt, asin, pi
from pathlib import Path

REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']
PROC = Path(__file__).resolve().parents[1] / "data/processed"

GEOTHERMAL_TYPES = {"PLTP", "PLTPB", "?"}
CLUSTER_RADIUS_KM = 3.0


def haversine_km(lon1, lat1, lon2, lat2):
    p = pi / 180
    h = (sin((lat2 - lat1) * p / 2) ** 2
         + cos(lat1 * p) * cos(lat2 * p) * sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371.0088 * asin(sqrt(max(0.0, h)))


def is_unnamed(name):
    if not name: return True
    n = name.strip().lower()
    return n in ("", "(unnamed)", "unnamed", "n/a", "-", "?")


def load_generators():
    feats = []
    for r in REGIONS:
        p = PROC / f"generators_{r}.reconciled.geojson"
        if not p.exists(): continue
        gj = json.loads(p.read_text())
        for f in gj.get("features", []):
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            if geom.get("type") != "Point": continue
            coords = geom.get("coordinates", [])
            if len(coords) < 2: continue
            # Skip features already tagged as complex child (Tier 1/2 sudah applied)
            if props.get("is_complex_child"): continue
            feats.append({
                "region": r,
                "id": props.get("id", ""),
                "name": props.get("name", "").strip() or "(unnamed)",
                "type": props.get("type", ""),
                "capacity_mw": props.get("capacity_mw", ""),
                "operator": props.get("operator", "").strip(),
                "source_id": props.get("source_id", ""),
                "osm_id": props.get("osm_id", ""),
                "match_tier": props.get("match_tier", ""),
                "ruptl_id": props.get("ruptl_id", ""),
                "target_cod": (props.get("target_cod_year")
                                or props.get("target_cod_year_ruptl") or ""),
                "status": props.get("status", ""),
                "province": props.get("province", ""),
                "lon": coords[0],
                "lat": coords[1],
                "is_planned": props.get("match_tier") == "UNMATCHED_RUPTL",
            })
    return feats


def find_clusters(feats):
    parent = {f["id"]: f["id"] for f in feats}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    for i in range(len(feats)):
        for j in range(i+1, len(feats)):
            a, b = feats[i], feats[j]
            d = haversine_km(a["lon"], a["lat"], b["lon"], b["lat"])
            if d > CLUSTER_RADIUS_KM: continue
            a_geo = a["type"] in GEOTHERMAL_TYPES
            b_geo = b["type"] in GEOTHERMAL_TYPES
            if a_geo and b_geo:
                union(a["id"], b["id"])
            elif (a_geo and is_unnamed(b["name"])) or (b_geo and is_unnamed(a["name"])):
                union(a["id"], b["id"])
    from collections import defaultdict
    clusters = defaultdict(list)
    for f in feats:
        clusters[find(f["id"])].append(f)
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def classify(members):
    named = [m for m in members if not is_unnamed(m["name"]) and m["type"] in GEOTHERMAL_TYPES]
    unnamed = [m for m in members if is_unnamed(m["name"])]
    pltp = [m for m in members if m["type"] == "PLTP"]
    if len(named) >= 1 and len(unnamed) >= 1 and len(pltp) >= 2:
        operators = set(m["operator"] for m in members if m["operator"])
        if len(operators) <= 1:
            return "CONFIDENT_COMPLEX"
        return "PROBABLE_COMPLEX"
    if len(named) == 0 and len(pltp) >= 2:
        return "PROBABLE_COMPLEX"
    if len(named) >= 2:
        return "AMBIGUOUS"
    return "KEEP_SEPARATE"


def spatial_spread(members):
    max_d = 0.0
    for i in range(len(members)):
        for j in range(i+1, len(members)):
            d = haversine_km(members[i]["lon"], members[i]["lat"],
                              members[j]["lon"], members[j]["lat"])
            max_d = max(max_d, d)
    return max_d


def parse_mw(v):
    try:
        return float(v) if v else 0
    except (ValueError, TypeError):
        return 0


def total_capacity(members):
    return sum(parse_mw(m["capacity_mw"]) for m in members)


def cluster_name(members):
    named = [m for m in members if not is_unnamed(m["name"])]
    if not named: return "(all unnamed)"
    # Pick most common stem from named
    from collections import Counter
    # Use first word of longest name for a natural label
    best = max(named, key=lambda m: len(m["name"]))
    return best["name"]


def analyze_cluster(members):
    """Return dict dengan reasoning, risk_merge, risk_separate, recommendation."""
    named = [m for m in members if not is_unnamed(m["name"]) and m["type"] in GEOTHERMAL_TYPES]
    unnamed_count = sum(1 for m in members if is_unnamed(m["name"]))
    total_mw = total_capacity(members)
    spread = spatial_spread(members)
    operators = set(m["operator"] for m in members if m["operator"])
    is_all_ruptl_planned = all(m["is_planned"] for m in members)
    has_existing = any(not m["is_planned"] for m in members)
    has_planned = any(m["is_planned"] for m in members)

    # Extract common name stem (untuk detect naming variants)
    stems = set()
    for m in named:
        # Strip PLTP prefix + common suffix
        s = m["name"].lower().replace("pltp", "").replace("gunung", "").strip()
        # Take first significant word
        parts = [w for w in s.split() if len(w) > 2]
        if parts: stems.add(parts[0])
    common_stem = (list(stems)[0] if len(stems) == 1 else None)

    reasons = []
    if len(named) >= 2:
        reasons.append(f"{len(named)} named PLTP dalam radius {CLUSTER_RADIUS_KM} km — bisa jadi distinct units atau naming variant")
    if len(operators) >= 2:
        reasons.append(f"Multiple operator tags: {operators}")
    if has_existing and has_planned:
        reasons.append("Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit")

    risk_merge = []
    if len(operators) >= 2:
        risk_merge.append("Operator berbeda bisa jadi distinct plants — merge bisa hilangkan info operator")
    if not common_stem:
        risk_merge.append("Nama tidak converge — merge bisa hide distinct plant identity")
    if has_planned and has_existing:
        risk_merge.append("Planned features punya capacity data terpisah — merge bisa double-count capacity")

    risk_separate = []
    if len(named) >= 2 and common_stem:
        risk_separate.append(f"Nama share common stem '{common_stem}' — mungkin single field yang multi-unit")
    if len(operators) <= 1:
        risk_separate.append("Same operator suggests single plant/field")
    if spread < 1.0:
        risk_separate.append(f"Spatial spread < 1 km — physically same geothermal field")

    # Recommendation logic
    if common_stem and len(operators) <= 1 and spread < 2.0 and not (has_planned and has_existing):
        rec = "MERGE_AS_ONE_COMPLEX"
    elif has_planned and has_existing:
        rec = "PARTIAL_MERGE"  # merge existing units only, treat planned as separate
    elif len(named) >= 2 and not common_stem:
        rec = "KEEP_SEPARATE"
    else:
        rec = "NEED_MORE_EVIDENCE"

    return {
        "reasons": reasons,
        "risk_merge": risk_merge,
        "risk_separate": risk_separate,
        "recommended_decision": rec,
        "common_stem": common_stem,
        "spread_km": spread,
        "total_mw": total_mw,
        "operators": operators,
        "unnamed_count": unnamed_count,
    }


def main():
    feats = load_generators()
    clusters_dict = find_clusters(feats)
    ambiguous = []
    for cid, members in clusters_dict.items():
        if classify(members) == "AMBIGUOUS":
            analysis = analyze_cluster(members)
            ambiguous.append({
                "cluster_id": cid,
                "members": members,
                "analysis": analysis,
                "name": cluster_name(members),
            })

    # Sort by (1) capacity_at_risk desc, (2) unnamed_count desc, (3) spread desc
    ambiguous.sort(key=lambda c: (
        -c["analysis"]["total_mw"],
        -c["analysis"]["unnamed_count"],
        -c["analysis"]["spread_km"],
    ))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(f'data/reconciliation/ambiguous_pltp_full_review_{ts}.md')
    lines = []
    lines.append(f"# AMBIGUOUS PLTP Clusters — Full Manual Review ({len(ambiguous)} clusters)")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Cluster radius: {CLUSTER_RADIUS_KM} km")
    lines.append("")
    lines.append("Sorted by review priority:")
    lines.append("1. Highest potential double-counting capacity (total_mw)")
    lines.append("2. Highest number of unnamed features")
    lines.append("3. Largest spatial spread")
    lines.append("")
    lines.append("Decision options per cluster:")
    lines.append("- `MERGE_AS_ONE_COMPLEX` — treat semua features as single complex")
    lines.append("- `KEEP_SEPARATE` — distinct plants, tidak perlu action")
    lines.append("- `PARTIAL_MERGE` — merge subset (mis. existing only, planned terpisah)")
    lines.append("- `NEED_MORE_EVIDENCE` — perlu data source tambahan / PDF verification")
    lines.append("")
    lines.append("**Recommended decision advisory only — jangan apply otomatis.**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Priority summary table")
    lines.append("")
    lines.append("| # | Cluster | Region | Features | Total MW | Unnamed | Spread km | Recommendation |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |")
    for i, c in enumerate(ambiguous, 1):
        a = c["analysis"]
        lines.append(f"| {i} | **{c['name']}** | {c['members'][0]['region']} | "
                      f"{len(c['members'])} | {a['total_mw']:.1f} | "
                      f"{a['unnamed_count']} | {a['spread_km']:.2f} | "
                      f"`{a['recommended_decision']}` |")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, c in enumerate(ambiguous, 1):
        a = c["analysis"]
        members = c["members"]
        lines.append(f"## {i}. {c['name']}")
        lines.append("")
        lines.append(f"- **Cluster ID**: `{c['cluster_id'][:20]}`")
        lines.append(f"- **Region**: {members[0]['region']}")
        lines.append(f"- **Total features**: {len(members)} ({a['unnamed_count']} unnamed)")
        lines.append(f"- **Total capacity**: {a['total_mw']:.1f} MW")
        lines.append(f"- **Spatial spread**: {a['spread_km']:.2f} km (max pairwise)")
        lines.append(f"- **Operators**: {a['operators'] or '{none tagged}'}")
        lines.append(f"- **Common name stem**: {a['common_stem'] or '(no common)'}")
        lines.append("")
        # Feature table
        lines.append("| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |")
        lines.append("| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |")
        for j, m in enumerate(members, 1):
            planned_tag = "planned" if m["is_planned"] else "existing"
            src = m["osm_id"] or m["ruptl_id"] or "—"
            lines.append(f"| {j} | `{m['id']}` | {m['name']} | {m['type']} | "
                          f"{m['capacity_mw'] or '—'} | "
                          f"{m['lat']:.4f},{m['lon']:.4f} | "
                          f"{planned_tag}/{m['status'] or '—'} | "
                          f"{m['operator'] or '—'} | `{src}` | "
                          f"{m['target_cod'] or '—'} |")
        lines.append("")
        lines.append(f"**Why AMBIGUOUS:**")
        for reason in a["reasons"]:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append(f"**Risk if MERGED:**")
        if a["risk_merge"]:
            for r in a["risk_merge"]:
                lines.append(f"- {r}")
        else:
            lines.append("- Low risk (evidence supports merge)")
        lines.append("")
        lines.append(f"**Risk if KEPT SEPARATE:**")
        if a["risk_separate"]:
            for r in a["risk_separate"]:
                lines.append(f"- {r}")
        else:
            lines.append("- Low risk (evidence supports separation)")
        lines.append("")
        lines.append(f"**Recommended decision (advisory only)**: `{a['recommended_decision']}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Full review report → {out}")
    print(f"  {len(ambiguous)} AMBIGUOUS clusters covered")
    return out


if __name__ == "__main__":
    main()
