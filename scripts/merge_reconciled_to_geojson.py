#!/usr/bin/env python3
"""Merge reconciled generator CSV into baseline GeoJSON.

Ambil `data/processed/generators_{region}.geojson` (baseline OSM features)
+ `data/processed/generator_master_reconciled_{region}.csv` (superset
dengan provenance + conflict flags), lalu produce
`data/processed/generators_{region}.reconciled.geojson` yang berisi:

  1. Baseline features yang di-enrich dengan match_tier, _source companions,
     _ruptl audit originals, dan conflict flags.
  2. UNMATCHED_RUPTL rows sebagai fitur baru (Point), pakai lat/lon dari
     geocoded RUPTL CSV. Ditandai `is_placeholder=true` kalau coord berasal
     dari province centroid (low confidence) supaya frontend bisa toggle
     visibility.

Non-destructive: baseline GeoJSON tidak di-modify. `bundle_web_data.py`
akan prefer `.reconciled.geojson` bila ada (patch di script terpisah).

Usage:
    python3 scripts/merge_reconciled_to_geojson.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional


# ------------------------------------------------------------
# Column groups yang dari reconciled CSV di-inject ke feature.properties
# ------------------------------------------------------------
MATCH_META_COLS = ["match_tier", "match_score", "match_reason", "ruptl_id"]

# Canonical status → uppercase enum untuk future year/status filter.
# Bahasa Indonesia + English inputs sama-sama di-map.
STATUS_NORM_MAP = {
    "planned": "PLANNED", "rencana": "PLANNED",
    "construction": "CONSTRUCTION", "konstruksi": "CONSTRUCTION",
    "kontruksi": "CONSTRUCTION",  # typo umum di RUPTL PDF
    "procurement": "PROCUREMENT", "pengadaan": "PROCUREMENT",
    "committed": "COMMITTED", "ppa": "COMMITTED",
    "proposed": "PROPOSED", "eksplorasi": "PROPOSED",
    "existing": "OPERATIONAL", "operational": "OPERATIONAL",
}


def norm_status(s: str) -> str:
    if not s:
        return ""
    key = str(s).strip().lower()
    return STATUS_NORM_MAP.get(key, key.upper())

SOURCE_COLS = [
    "name_source", "capacity_mw_source", "type_source", "role_source",
    "operator_source", "status_source", "coord_source",
]

AUDIT_COLS = [
    "capacity_mw_ipm", "capacity_mw_ruptl",
    "type_ipm", "type_ruptl",
    "role_ipm", "role_ruptl",
]

CONFLICT_COLS = [
    "has_capacity_conflict", "has_type_conflict",
    "has_role_conflict", "has_location_conflict",
]

# Kolom untuk UNMATCHED_RUPTL feature baru
UNMATCHED_FEATURE_COLS = [
    "id", "name", "type", "capacity_mw", "province", "system", "status",
    "role", "operator", "match_tier", "match_score", "match_reason",
    "ruptl_id", "coord_source",
] + AUDIT_COLS


# ------------------------------------------------------------
# Load helpers
# ------------------------------------------------------------
def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"missing: {path}")
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_float(v) -> Optional[float]:
    try:
        s = str(v or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


# ------------------------------------------------------------
# Main merge
# ------------------------------------------------------------
def merge(region: str, project_root: Path) -> int:
    processed = project_root / "data/processed"
    base_gj_path = processed / f"generators_{region}.geojson"
    recon_csv_path = processed / f"generator_master_reconciled_{region}.csv"
    ruptl_csv_path = processed / f"ruptl_generators_{region}.csv"
    out_path = processed / f"generators_{region}.reconciled.geojson"

    if not base_gj_path.exists():
        print(f"[merge] missing: {base_gj_path}", file=sys.stderr)
        return 2
    if not recon_csv_path.exists():
        print(f"[merge] missing: {recon_csv_path} — run reconcile_generators --write first",
              file=sys.stderr)
        return 2

    print(f"[merge] region={region}")

    # Load base GeoJSON
    baseline = json.loads(base_gj_path.read_text(encoding="utf-8"))
    features = baseline.get("features", [])
    print(f"  baseline features: {len(features)}")

    # Index reconciled by IPM id (for matched enrichment) and by ruptl_id
    recon_rows = load_csv(recon_csv_path)
    by_ipm_id: dict[str, dict] = {}
    unmatched_ruptl_rows: list[dict] = []
    for r in recon_rows:
        tier = r.get("match_tier", "")
        ipm_id = r.get("ipm_id", "").strip()
        if ipm_id:
            by_ipm_id[ipm_id] = r
        if tier == "UNMATCHED_RUPTL":
            unmatched_ruptl_rows.append(r)
    print(f"  reconciled rows: {len(recon_rows)}")
    print(f"    matched to IPM id: {len(by_ipm_id)}")
    print(f"    unmatched RUPTL:   {len(unmatched_ruptl_rows)}")

    # Load RUPTL geocoded CSV for coord_confidence + source_page/table lookup
    # (fields yang tidak ada di reconciled CSV, penting untuk popup context).
    coord_conf_by_ruptl_id: dict[str, str] = {}
    ruptl_extra_by_id: dict[str, dict] = {}
    if ruptl_csv_path.exists():
        for r in load_csv(ruptl_csv_path):
            rid = r.get("id", "").strip()
            if rid:
                coord_conf_by_ruptl_id[rid] = (r.get("coord_confidence") or "").strip()
                ruptl_extra_by_id[rid] = {
                    "source_page": r.get("source_page", ""),
                    "source_table": r.get("source_table", ""),
                    "target_cod_year": r.get("target_cod_year", ""),
                    "developer": r.get("developer", ""),
                }

    # Enrich matched baseline features
    enriched_count = 0
    for feat in features:
        props = feat.get("properties") or {}
        fid = props.get("id", "")
        rec = by_ipm_id.get(fid)
        if not rec:
            # IPM feature yang tidak muncul di reconciled → UNMATCHED_IPM tapi
            # tidak di-tag di CSV (karena reconciler emit UNMATCHED_IPM sebagai
            # baris terpisah). Set tag default supaya frontend seragam.
            props["match_tier"] = "UNMATCHED_IPM"
            props["match_score"] = ""
            props["match_reason"] = ""
            props["ruptl_id"] = ""
            for c in SOURCE_COLS:
                props.setdefault(c, "ipm_osm")
            for c in AUDIT_COLS:
                props.setdefault(c, "")
            for c in CONFLICT_COLS:
                props.setdefault(c, "false")
            props["is_placeholder"] = False
            props["status_norm"] = norm_status(props.get("status", ""))
            props["action_norm"] = ""
            props.setdefault("target_cod_year_ruptl", "")
            continue

        # Enrich dengan match metadata + provenance
        for c in MATCH_META_COLS + SOURCE_COLS + AUDIT_COLS + CONFLICT_COLS:
            v = rec.get(c, "")
            if v != "":
                props[c] = v
        # Canonical temporal + status/action untuk enriched baseline features:
        # cross-lookup ke ruptl_extra_by_id (via ruptl_id) untuk grab
        # target_cod_year, status, action dari raw RUPTL row.
        rup_id = rec.get("ruptl_id", "").strip()
        if rup_id and rup_id in ruptl_extra_by_id:
            rx = ruptl_extra_by_id[rup_id]
            for k in ("target_cod_year", "status", "action_type",
                       "source_page", "source_table"):
                if rx.get(k) and not props.get(k + "_ruptl"):
                    props[k + "_ruptl"] = rx[k]
            props["status_norm"] = norm_status(rx.get("status", ""))
        else:
            props["status_norm"] = norm_status(props.get("status", ""))
        # Baseline generator tidak punya action (semua "existing operational").
        props["action_norm"] = ""
        # target_cod_year (canonical) — untuk baseline default kosong;
        # kalau ada RUPTL match, mirror ke target_cod_year_ruptl.
        # (Feature filter nanti baca target_cod_year || target_cod_year_ruptl.)
        props["is_placeholder"] = False
        enriched_count += 1

    print(f"  enriched: {enriched_count} features")

    # Add UNMATCHED_RUPTL sebagai fitur Point baru.
    # SKIP `coord_confidence=low` rows (province centroid + jitter, bukan
    # geolokasi real) supaya map tidak dipenuhi cluster di 7 titik centroid.
    # Rows tetap ada di CSV `generator_master_reconciled_{region}.csv` untuk
    # review manual + geocoding future.
    added = 0
    skipped_no_coord = 0
    skipped_placeholder = 0
    for r in unmatched_ruptl_rows:
        lat = parse_float(r.get("lat"))
        lon = parse_float(r.get("lon"))
        if lat is None or lon is None:
            skipped_no_coord += 1
            continue

        ruptl_id = r.get("ruptl_id", "")
        coord_conf = coord_conf_by_ruptl_id.get(ruptl_id, "unknown")
        is_placeholder = coord_conf == "low"
        if is_placeholder:
            skipped_placeholder += 1
            continue

        props = {}
        for c in UNMATCHED_FEATURE_COLS:
            props[c] = r.get(c, "")
        # Force source columns to "ruptl" untuk transparansi
        for c in SOURCE_COLS:
            if not props.get(c):
                props[c] = "ruptl"
        for c in CONFLICT_COLS:
            props[c] = "false"
        props["ipm_id"] = ""  # explicit: tidak ada IPM baseline pair
        props["coord_confidence"] = coord_conf
        props["is_placeholder"] = is_placeholder
        # Inject source_page/table + target_cod_year dari raw RUPTL CSV
        # (fields yang di-drop di reconciled CSV tapi useful untuk popup).
        extra = ruptl_extra_by_id.get(ruptl_id, {})
        for k, v in extra.items():
            if v and not props.get(k):
                props[k] = v
        # Canonical enum fields — PLANNED generator: action always NEW,
        # status di-normalize dari RUPTL row status field.
        props["action_norm"] = "NEW"
        props["status_norm"] = norm_status(props.get("status", ""))
        props.setdefault("target_cod_year", extra.get("target_cod_year", ""))
        props.setdefault("target_cod_year_ruptl", "")
        # Ensure numeric-ish fields casted properly
        cap = parse_float(props.get("capacity_mw"))
        if cap is not None:
            props["capacity_mw"] = cap

        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        }
        features.append(feat)
        added += 1

    print(f"  added {added} UNMATCHED_RUPTL features with real coord")
    if skipped_placeholder:
        print(f"  skipped {skipped_placeholder} placeholder RUPTL rows "
              f"(coord_confidence=low, tersedia di CSV untuk geocoding manual)")
    if skipped_no_coord:
        print(f"  skipped {skipped_no_coord} RUPTL rows without coord")

    # Write out
    baseline["features"] = features
    out_path.write_text(json.dumps(baseline, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\n  wrote {out_path} ({out_path.stat().st_size} bytes, {len(features)} features)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    opts = ap.parse_args()
    return merge(opts.region, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
