#!/usr/bin/env python3
"""Audit missing inter-system interconnections.

Known Indonesia inter-system connections (from publicly documented PLN
grid + RUPTL + OSM presence):
  - Jawa-Bali: 150 kV cable via Ketapang-Gilimanuk (existing sejak 1994)
  - Jawa-Madura: 150 kV via Ujung-Kamal (Suramadu adjacent)
  - Sumatera-Batam: 275 kV HVDC (planned/committed di RUPTL)
  - Sumatera-Bangka: 275 kV planned di RUPTL 2025-2034

Check apakah interconnector ini sudah ada di baseline transmission
GeoJSON, dan kalau tidak — cari evidence di RUPTL / OSM untuk source.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

PROC = Path(__file__).resolve().parents[1] / "data/processed"
REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']

# Known interconnectors — search terms untuk endpoint names
KNOWN_INTERCONNECTORS = [
    {
        "name": "Jawa-Bali interconnector",
        "voltage_kv": 150,
        "endpoints": ["Ketapang", "Gilimanuk"],
        "regions": ["jamali"],  # jamali covers both Jawa Timur + Bali
        "status_expected": "existing",
        "source_evidence": "PLN operational — cable submarine Selat Bali since 1994",
    },
    {
        "name": "Jawa-Madura interconnector",
        "voltage_kv": 150,
        "endpoints": ["Ujung", "Kamal"],
        "regions": ["jamali"],
        "status_expected": "existing",
        "source_evidence": "PLN operational — cable/overhead Selat Madura",
    },
    {
        "name": "Sumatera-Batam interconnector",
        "voltage_kv": 275,
        "endpoints": ["Kabil", "Panaran", "Payakumbuh"],
        "regions": ["sumatra"],
        "status_expected": "planned",
        "source_evidence": "RUPTL 2025-2034 committed project",
    },
    {
        "name": "Sumatera-Bangka interconnector",
        "voltage_kv": 150,
        "endpoints": ["Bangka", "Air Anyir", "Sungailiat"],
        "regions": ["sumatra"],
        "status_expected": "planned",
        "source_evidence": "RUPTL planned HVAC crossing Selat Bangka",
    },
]


def collect_endpoint_names():
    """Aggregate all substation names (baseline + planned) across regions."""
    subs = []
    for r in REGIONS:
        p = PROC / f"substations_{r}.reconciled.geojson"
        if not p.exists(): continue
        gj = json.loads(p.read_text())
        for f in gj.get("features", []):
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            if geom.get("type") != "Point": continue
            coords = geom.get("coordinates", [])
            subs.append({
                "region": r,
                "id": props.get("id", ""),
                "name": props.get("name", ""),
                "province": props.get("province", ""),
                "voltage": props.get("voltage", ""),
                "match_tier": props.get("match_tier", ""),
                "lon": coords[0] if coords else None,
                "lat": coords[1] if len(coords) > 1 else None,
            })
    return subs


def find_endpoint(name_query, subs):
    """Cari substation dengan nama mengandung query (case-insensitive)."""
    q = name_query.lower()
    hits = []
    for s in subs:
        if q in (s.get("name", "") or "").lower():
            hits.append(s)
    return hits


def check_existing_transmission_link(from_hits, to_hits):
    """Cek apakah ada transmission LineString yang menghubungkan endpoint pair."""
    from_ids = {h["id"] for h in from_hits}
    to_ids = {h["id"] for h in to_hits}
    for r in REGIONS:
        p = PROC / f"transmission_{r}.reconciled.geojson"
        if not p.exists(): continue
        gj = json.loads(p.read_text())
        for f in gj.get("features", []):
            props = f.get("properties", {})
            fid = props.get("from_id", "")
            tid = props.get("to_id", "")
            # Also check circuit endpoints
            cfid = props.get("circuit_from_id", "")
            ctid = props.get("circuit_to_id", "")
            # Pair check both directions
            for pair_from, pair_to in [(fid, tid), (cfid, ctid)]:
                if not (pair_from and pair_to): continue
                if (pair_from in from_ids and pair_to in to_ids) or \
                   (pair_from in to_ids and pair_to in from_ids):
                    return {"found": True, "region": r,
                            "line_id": props.get("id", "") or props.get("osm_id", ""),
                            "voltage": props.get("voltage_class", ""),
                            "match_tier": props.get("match_tier", "")}
    return {"found": False}


def audit():
    subs = collect_endpoint_names()
    print(f"[audit_interconnectors] loaded {len(subs)} substation features")
    print()

    findings = []
    for ic in KNOWN_INTERCONNECTORS:
        endpoints_data = []
        for ep in ic["endpoints"]:
            hits = find_endpoint(ep, subs)
            endpoints_data.append({"query": ep, "hits": hits})
        # Try pair combinations
        if len(endpoints_data) >= 2:
            link_check = check_existing_transmission_link(
                endpoints_data[0]["hits"], endpoints_data[1]["hits"])
        else:
            link_check = {"found": False}
        findings.append({
            "ic": ic,
            "endpoints_data": endpoints_data,
            "link_check": link_check,
        })

    # Report
    print("=" * 68)
    print("  INTERCONNECTOR AUDIT")
    print("=" * 68)

    for f in findings:
        ic = f["ic"]
        print(f"\n== {ic['name']} ==")
        print(f"  Expected: {ic['voltage_kv']} kV, status={ic['status_expected']}")
        print(f"  Source: {ic['source_evidence']}")
        for ed in f["endpoints_data"]:
            print(f"  Search '{ed['query']}':")
            if not ed["hits"]:
                print(f"    → No substation named '{ed['query']}' found")
            else:
                for h in ed["hits"][:3]:
                    print(f"    → {h['id']} '{h['name']}' ({h['region']}, {h['province']}, "
                          f"{h['voltage']} kV, coord {h['lat']:.4f},{h['lon']:.4f})")
        lc = f["link_check"]
        if lc.get("found"):
            print(f"  ✓ Existing transmission link found: {lc['line_id']} "
                  f"({lc['voltage']}, tier={lc['match_tier']}, region={lc['region']})")
        else:
            print(f"  ⚠ NO transmission link found between endpoints in current dataset")

    # Aggregate summary
    print()
    print("=" * 68)
    print("  SUMMARY")
    print("=" * 68)
    missing = [f for f in findings if not f["link_check"].get("found")]
    print(f"  Total known interconnectors checked: {len(findings)}")
    print(f"  Missing from dataset: {len(missing)}")
    for f in missing:
        ic = f["ic"]
        resolvable = all(ed["hits"] for ed in f["endpoints_data"])
        marker = "endpoints ready" if resolvable else "endpoint gap"
        print(f"    - {ic['name']} ({ic['voltage_kv']} kV, {ic['status_expected']}) — {marker}")


if __name__ == "__main__":
    audit()
