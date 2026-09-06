#!/usr/bin/env python3
"""Apply plant complex curation ke generators reconciled GeoJSON.

Reads: data/overrides/plant_complex_curation.csv
For each row:
  - Parse child_feature_ids (semicolon-separated)
  - For each child feature in generators_{region}.reconciled.geojson:
    - Tag properties: complex_id, complex_name, is_complex_child=true
    - For unnamed children: also tag is_hidden_by_complex=true supaya
      frontend/audit tools bisa skip di visual rendering
  - Preserve raw feature (do not delete/merge geometry)

Provenance preserved: raw source data (OSM ID, RUPTL row) tetap ada,
cuma tag complex metadata ditambahkan sebagai overlay.

Usage:
    python3 scripts/apply_plant_complex.py --region jamali
    python3 scripts/apply_plant_complex.py --all
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURATION_PATH = ROOT / "data/overrides/plant_complex_curation.csv"
PROC = ROOT / "data/processed"
REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']


def load_curation():
    if not CURATION_PATH.exists():
        return []
    with CURATION_PATH.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def is_unnamed(name):
    if not name: return True
    n = name.strip().lower()
    return n in ("", "(unnamed)", "unnamed", "n/a", "-", "?")


def apply_region(region: str, complexes: list[dict]) -> dict:
    """Apply relevant complex rows to region's reconciled GeoJSON."""
    region_complexes = [c for c in complexes if c.get("region", "").strip().lower() == region]
    if not region_complexes:
        return {"region": region, "applied": 0, "children_tagged": 0, "hidden": 0}

    gj_path = PROC / f"generators_{region}.reconciled.geojson"
    if not gj_path.exists():
        return {"region": region, "error": "GeoJSON missing"}
    gj = json.loads(gj_path.read_text())
    features = gj.get("features", [])

    # Index by ID for fast lookup
    by_id = {f["properties"].get("id", ""): f for f in features}

    stats = {"region": region, "applied": 0, "children_tagged": 0, "hidden": 0,
             "missing_ids": []}
    for c in region_complexes:
        cid = c.get("complex_id", "").strip()
        cname = c.get("complex_name", "").strip()
        child_ids = [x.strip() for x in c.get("child_feature_ids", "").split(";") if x.strip()]
        for child_id in child_ids:
            feat = by_id.get(child_id)
            if not feat:
                stats["missing_ids"].append(child_id)
                continue
            props = feat["properties"]
            props["complex_id"] = cid
            props["complex_name"] = cname
            props["is_complex_child"] = True
            # Hide unnamed children (visual only — data preserved)
            if is_unnamed(props.get("name", "")):
                props["is_hidden_by_complex"] = True
                stats["hidden"] += 1
            stats["children_tagged"] += 1
        stats["applied"] += 1

    gj_path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--region", help="single region key")
    g.add_argument("--all", action="store_true", help="all 8 regions")
    opts = ap.parse_args()

    complexes = load_curation()
    print(f"[apply_plant_complex] loaded {len(complexes)} complex definitions from {CURATION_PATH}")
    if not complexes:
        print("  (empty curation file — nothing to apply)")
        return

    regions = REGIONS if opts.all else [opts.region]
    for r in regions:
        stats = apply_region(r, complexes)
        if stats.get("applied", 0) > 0 or stats.get("missing_ids"):
            print(f"  {r:<11} complexes={stats.get('applied',0)}  "
                  f"children_tagged={stats.get('children_tagged',0)}  "
                  f"hidden={stats.get('hidden',0)}"
                  + (f"  missing={stats['missing_ids']}" if stats.get('missing_ids') else ""))


if __name__ == "__main__":
    main()
