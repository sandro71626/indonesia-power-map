#!/usr/bin/env python3
"""Audit PLTP / unnamed clustered generator features.

Detect kandidat generator yang mungkin bagian dari satu plant complex:
  1. Load semua generator dari 8 region reconciled GeoJSON
  2. Filter kandidat: unnamed / generic name + type PLTP (atau near PLTP)
  3. Spatial cluster within radius (default 3 km)
  4. Contextual validation per cluster:
     - Ada named plant dalam radius? → likely satellite/subunit
     - Multiple unnamed within cluster? → likely one complex mapped as multi
     - Capacity consistency
     - Shared OSM tags/source

Output klasifikasi:
  CONFIDENT_COMPLEX  — clear evidence (1 named + N unnamed nearby, same tech)
  PROBABLE_COMPLEX   — multiple unnamed within radius, likely single complex
  AMBIGUOUS          — mixed signals, needs manual review
  KEEP_SEPARATE      — distinct plants that happen to be close (rare)

Tidak modify data — audit only. Report ditulis ke
data/reconciliation/pltp_cluster_audit_{ts}.md
"""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import sin, cos, sqrt, asin, pi
from pathlib import Path

REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']
PROC = Path(__file__).resolve().parents[1] / "data/processed"

# PLTP-related types (bisa jadi ada BESS/BES/dll di plant complex geothermal)
GEOTHERMAL_TYPES = {"PLTP", "PLTPB", "?"}  # ? kadang PLTP salah recognize

# Cluster radius — 3 km cukup untuk geothermal field (Kamojang, Salak, Wayang Windu clusters)
CLUSTER_RADIUS_KM = 3.0


def haversine_km(lon1, lat1, lon2, lat2):
    p = pi / 180
    h = (sin((lat2 - lat1) * p / 2) ** 2
         + cos(lat1 * p) * cos(lat2 * p) * sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371.0088 * asin(sqrt(max(0.0, h)))


def is_unnamed(name):
    if not name: return True
    n = name.strip().lower()
    return n in ("", "(unnamed)", "unnamed", "n/a", "-", "?", "?")


def load_generators():
    """Load semua generator features dari 8 region."""
    all_feats = []
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
            all_feats.append({
                "region": r,
                "id": props.get("id", ""),
                "name": props.get("name", ""),
                "type": props.get("type", ""),
                "capacity_mw": props.get("capacity_mw", ""),
                "operator": props.get("operator", ""),
                "source_id": props.get("source_id", ""),
                "osm_id": props.get("osm_id", ""),
                "match_tier": props.get("match_tier", ""),
                "lon": coords[0],
                "lat": coords[1],
            })
    return all_feats


def find_clusters(feats):
    """Simple radius-based clustering — dua feature dalam radius = same cluster.
    Union-find lightweight.
    """
    parent = {f["id"]: f["id"] for f in feats}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb

    # Only PLTP or Unnamed-near-PLTP considered for clustering
    for i in range(len(feats)):
        for j in range(i+1, len(feats)):
            a, b = feats[i], feats[j]
            d = haversine_km(a["lon"], a["lat"], b["lon"], b["lat"])
            if d > CLUSTER_RADIUS_KM: continue
            # Cluster kalau: both geothermal-related type, ATAU both unnamed
            a_geo = a["type"] in GEOTHERMAL_TYPES
            b_geo = b["type"] in GEOTHERMAL_TYPES
            if a_geo and b_geo:
                union(a["id"], b["id"])
            elif (a_geo and is_unnamed(b["name"])) or (b_geo and is_unnamed(a["name"])):
                union(a["id"], b["id"])

    clusters = defaultdict(list)
    for f in feats:
        clusters[find(f["id"])].append(f)
    # Filter: only clusters with 2+ members
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def classify_cluster(members):
    """Return (tier, reasoning)."""
    named = [m for m in members if not is_unnamed(m["name"]) and m["type"] in GEOTHERMAL_TYPES]
    unnamed = [m for m in members if is_unnamed(m["name"])]
    pltp = [m for m in members if m["type"] == "PLTP"]

    # CONFIDENT: 1 clearly named PLTP + all others unnamed nearby
    if len(named) >= 1 and len(unnamed) >= 1 and len(pltp) >= 2:
        # Same operator hint / same source
        operators = set(m["operator"] for m in members if m["operator"])
        if len(operators) <= 1:
            return ("CONFIDENT_COMPLEX",
                    f"1 named PLTP + {len(unnamed)} unnamed within {CLUSTER_RADIUS_KM}km, "
                    f"same operator ({list(operators) or 'unknown'})")
        return ("PROBABLE_COMPLEX",
                f"1 named PLTP + {len(unnamed)} unnamed, multiple operators: {operators}")

    # PROBABLE: multiple unnamed clustered, all PLTP
    if len(named) == 0 and len(pltp) >= 2:
        return ("PROBABLE_COMPLEX",
                f"{len(pltp)} unnamed PLTP within {CLUSTER_RADIUS_KM}km — likely one field")

    # AMBIGUOUS: multiple named PLTP nearby (real distinct plants?)
    if len(named) >= 2:
        return ("AMBIGUOUS",
                f"{len(named)} named PLTP within {CLUSTER_RADIUS_KM}km — could be distinct or same field")

    return ("KEEP_SEPARATE",
            f"Mixed / unclear pattern ({len(named)} named, {len(unnamed)} unnamed)")


def audit():
    feats = load_generators()
    unnamed_all = [f for f in feats if is_unnamed(f["name"])]
    unnamed_pltp = [f for f in unnamed_all if f["type"] in GEOTHERMAL_TYPES]

    clusters = find_clusters(feats)

    tiered = defaultdict(list)
    total_cluster_members = 0
    resolvable_unnamed = 0
    for cid, members in clusters.items():
        tier, reasoning = classify_cluster(members)
        tiered[tier].append({
            "cluster_id": cid,
            "members": members,
            "reasoning": reasoning,
        })
        total_cluster_members += len(members)
        if tier in ("CONFIDENT_COMPLEX", "PROBABLE_COMPLEX"):
            resolvable_unnamed += sum(1 for m in members if is_unnamed(m["name"]))

    # Total capacity per cluster (double-count risk check)
    total_pltp_capacity_all = sum(float(f["capacity_mw"] or 0) for f in feats if f["type"] == "PLTP")
    cluster_pltp_capacity = 0
    for cid, ms in clusters.items():
        for m in ms:
            if m["type"] == "PLTP":
                cluster_pltp_capacity += float(m["capacity_mw"] or 0)

    # Write report
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).resolve().parents[1] / f"data/reconciliation/pltp_cluster_audit_{ts}.md"
    lines = []
    lines.append(f"# PLTP / Unnamed Generator Cluster Audit — {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append(f"Cluster radius: {CLUSTER_RADIUS_KM} km")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total generator features scanned: {len(feats)}")
    lines.append(f"- Unnamed features total: {len(unnamed_all)}")
    lines.append(f"- Unnamed PLTP/geothermal features: {len(unnamed_pltp)}")
    lines.append(f"- Candidate clusters (≥2 members): {len(clusters)}")
    lines.append(f"- Features in some cluster: {total_cluster_members}")
    lines.append(f"- Unnamed features resolvable via CONFIDENT/PROBABLE cluster: {resolvable_unnamed}")
    lines.append(f"- Total PLTP capacity dataset: {total_pltp_capacity_all:.1f} MW")
    lines.append(f"- PLTP capacity inside clusters: {cluster_pltp_capacity:.1f} MW")
    lines.append(f"- Double-counting risk: {cluster_pltp_capacity/max(total_pltp_capacity_all,1)*100:.1f}% of PLTP capacity is in cluster candidates")
    lines.append("")
    lines.append("## Cluster classification")
    lines.append("")
    lines.append(f"| Tier | Cluster count |")
    lines.append(f"| --- | ---: |")
    for tier in ("CONFIDENT_COMPLEX", "PROBABLE_COMPLEX", "AMBIGUOUS", "KEEP_SEPARATE"):
        lines.append(f"| {tier} | {len(tiered.get(tier, []))} |")
    lines.append("")

    for tier in ("CONFIDENT_COMPLEX", "PROBABLE_COMPLEX", "AMBIGUOUS", "KEEP_SEPARATE"):
        items = tiered.get(tier, [])
        if not items: continue
        lines.append(f"## {tier} ({len(items)})")
        lines.append("")
        # Sort by member count desc (biggest complex first)
        items.sort(key=lambda x: -len(x["members"]))
        for entry in items[:20]:
            members = entry["members"]
            # Suggest a parent name — use named PLTP or largest capacity
            named = [m for m in members if not is_unnamed(m["name"])]
            parent_name = named[0]["name"] if named else f"(cluster {entry['cluster_id'][:12]})"
            total_cap = sum(float(m["capacity_mw"] or 0) for m in members)
            lines.append(f"### Cluster: **{parent_name}** ({members[0]['region']}) — {len(members)} features, {total_cap:.1f} MW total")
            lines.append(f"_{entry['reasoning']}_")
            lines.append("")
            lines.append("| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |")
            lines.append("| --- | --- | --- | ---: | --- | --- | --- |")
            for m in members:
                lines.append(f"| `{m['id']}` | {m['name'] or '(unnamed)'} | {m['type']} | "
                              f"{m['capacity_mw'] or '—'} | {m['lat']:.4f}, {m['lon']:.4f} | "
                              f"{m['operator'][:30]} | `{m['osm_id']}` |")
            lines.append("")
        if len(items) > 20:
            lines.append(f"_(+{len(items) - 20} more)_")
        lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[audit_pltp_clusters] Report written → {out}")
    print()
    print(f"Summary:")
    print(f"  Unnamed features total: {len(unnamed_all)}")
    print(f"  Unnamed PLTP: {len(unnamed_pltp)}")
    print(f"  Cluster candidates: {len(clusters)}")
    print(f"  Resolvable via CONFIDENT/PROBABLE: {resolvable_unnamed}")
    print(f"  Tier breakdown: {dict((t, len(v)) for t, v in tiered.items())}")


if __name__ == "__main__":
    audit()
