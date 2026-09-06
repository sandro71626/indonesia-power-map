#!/usr/bin/env python3
"""Apply interconnector curation ke transmission reconciled GeoJSON.

Reads: data/overrides/interconnectors_curated.csv
For each row:
  - Resolve endpoint substations by from_sub_id/to_sub_id (cari across
    ALL region baselines)
  - If sub_id tidak ada di baseline, fallback ke explicit from_lat/lon
    dan to_lat/lon di CSV (manual coord dengan attribution)
  - Create LineString feature dengan geometry from-to
  - Append feature ke transmission_{region}.reconciled.geojson untuk
    kedua region endpoint (agar visible di kedua region filter)
  - Feature deduplicate at frontend load via interconnector_id

Properties yang di-set:
  id                  RUPTL/curated ID (unique)
  interconnector_id   sama seperti id (untuk frontend dedup)
  name                dari CSV
  from_sub_id, to_sub_id
  from_region, to_region
  voltage_kv, voltage_class
  status              existing / planned
  technology          submarine cable / overhead / HVDC / dll
  match_tier          BASELINE (existing) or PLANNED_RUPTL (planned)
  source, source_url  attribution
  is_interconnector   true
  action_norm         NEW (default untuk interconnector)
  status_norm         PLANNED / OPERATIONAL

Idempotent — sebelum append, drop existing interconnector dengan id sama.

Usage:
    python3 scripts/apply_interconnectors.py
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CURATION_PATH = ROOT / "data/overrides/interconnectors_curated.csv"
PROC = ROOT / "data/processed"
REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']


def load_curation():
    if not CURATION_PATH.exists():
        return []
    with CURATION_PATH.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_sub_index():
    """Return {id: {region, name, lat, lon}} across all regions."""
    idx = {}
    for r in REGIONS:
        # Baseline substation master CSV
        p = PROC / f"substation_master_{r}.csv"
        if p.exists():
            with p.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    rid = row.get("id", "").strip()
                    try:
                        lat = float(row.get("lat") or "")
                        lon = float(row.get("lon") or "")
                    except ValueError:
                        continue
                    if rid:
                        idx[rid] = {"region": r, "name": row.get("name", ""),
                                     "lat": lat, "lon": lon}
        # Reconciled sub GeoJSON (includes NEW_BUILD planned)
        gj_path = PROC / f"substations_{r}.reconciled.geojson"
        if gj_path.exists():
            gj = json.loads(gj_path.read_text())
            for f in gj.get("features", []):
                props = f.get("properties", {})
                rid = props.get("id", "").strip()
                if rid in idx: continue
                geom = f.get("geometry", {})
                if geom.get("type") != "Point": continue
                coords = geom.get("coordinates", [])
                if len(coords) < 2: continue
                idx[rid] = {"region": r, "name": props.get("name", ""),
                             "lat": coords[1], "lon": coords[0]}
    return idx


def apply_interconnectors():
    rows = load_curation()
    if not rows:
        print(f"[apply_interconnectors] no curation rows in {CURATION_PATH}")
        return

    sub_idx = build_sub_index()
    print(f"[apply_interconnectors] loaded {len(rows)} interconnectors, "
          f"{len(sub_idx)} substation index entries")

    # For each interconnector, resolve endpoints + build feature
    to_append = defaultdict(list)  # region → [feature]
    stats = {"resolved": 0, "unresolved": 0, "duplicated_across_regions": 0}
    for r in rows:
        ic_id = r.get("interconnector_id", "").strip()
        if not ic_id:
            print(f"  ⚠ Skip row without interconnector_id: {r}")
            continue

        # Resolve from endpoint
        from_id = r.get("from_sub_id", "").strip()
        to_id = r.get("to_sub_id", "").strip()
        from_pin = sub_idx.get(from_id)
        to_pin = sub_idx.get(to_id)

        # Fallback: explicit coord dari CSV
        def maybe_manual(pin_dict, prefix):
            if pin_dict:
                return pin_dict, "resolved"
            try:
                lat = float(r.get(prefix + "_lat", ""))
                lon = float(r.get(prefix + "_lon", ""))
                return ({"region": r.get(prefix + "_region", "").strip().lower() or "manual",
                         "name": r.get(prefix + "_name", "").strip() or f"({prefix} manual)",
                         "lat": lat, "lon": lon}, "manual")
            except (ValueError, TypeError):
                return None, "missing"

        from_pin, from_src = maybe_manual(from_pin, "from")
        to_pin, to_src = maybe_manual(to_pin, "to")

        if not from_pin or not to_pin:
            print(f"  ⚠ {ic_id}: unresolved endpoint(s) — from={from_src}, to={to_src}")
            stats["unresolved"] += 1
            continue

        voltage_kv = r.get("voltage_kv", "").strip()
        status = (r.get("status", "").strip().lower() or "planned")
        is_existing = status == "existing"
        # Feature properties
        props = {
            "id": ic_id,
            "interconnector_id": ic_id,
            "is_interconnector": True,
            "name": r.get("name", ""),
            "from_sub_id": from_id,
            "to_sub_id": to_id,
            "from_region": from_pin["region"],
            "to_region": to_pin["region"],
            "from_name": from_pin["name"],
            "to_name": to_pin["name"],
            "voltage_kv": voltage_kv,
            "voltage_class": (voltage_kv + " kV") if voltage_kv else "",
            "voltage_kv_max": voltage_kv,
            "status": status,
            "status_norm": "OPERATIONAL" if is_existing else "PLANNED",
            "technology": r.get("technology", ""),
            "match_tier": "BASELINE" if is_existing else "PLANNED_RUPTL",
            "action_type": r.get("action_type", "New" if not is_existing else ""),
            "action_norm": "NEW" if not is_existing else "",
            "source": r.get("evidence", ""),
            "source_url": r.get("source_url", ""),
            "source_id": r.get("evidence", ""),
            "target_cod_year": r.get("target_cod_year", ""),
            "target_cod_year_ruptl": r.get("target_cod_year", "") if not is_existing else "",
            "endpoint_confidence": "both",
            "from_id": from_id,
            "to_id": to_id,
            "circuit_from_name": from_pin["name"],
            "circuit_to_name": to_pin["name"],
            "curated_by": r.get("curated_by", ""),
            "curated_date": r.get("curated_date", ""),
            "from_endpoint_source": from_src,
            "to_endpoint_source": to_src,
        }
        # Compute length (haversine) for display
        from math import sin, cos, sqrt, asin, pi
        p = pi / 180
        h = (sin((to_pin["lat"] - from_pin["lat"]) * p / 2) ** 2
             + cos(from_pin["lat"] * p) * cos(to_pin["lat"] * p)
             * sin((to_pin["lon"] - from_pin["lon"]) * p / 2) ** 2)
        length_km = 2 * 6371.0088 * asin(sqrt(max(0.0, h)))
        props["length_km"] = round(length_km, 2)

        feat = {
            "type": "Feature",
            "geometry": {"type": "LineString",
                          "coordinates": [[from_pin["lon"], from_pin["lat"]],
                                          [to_pin["lon"], to_pin["lat"]]]},
            "properties": props,
        }
        # Append to BOTH endpoint regions (untuk visibility di filter region)
        target_regions = {from_pin["region"], to_pin["region"]}
        for tr in target_regions:
            if tr in REGIONS:
                to_append[tr].append(feat)
        stats["resolved"] += 1
        if len(target_regions) > 1:
            stats["duplicated_across_regions"] += 1

    # Apply to each region's transmission reconciled GeoJSON
    for region, feats in to_append.items():
        gj_path = PROC / f"transmission_{region}.reconciled.geojson"
        if not gj_path.exists():
            print(f"  ⚠ Region {region}: transmission GeoJSON missing, skip {len(feats)} features")
            continue
        gj = json.loads(gj_path.read_text())
        existing = gj.get("features", [])
        # Idempotent: drop existing interconnectors dengan interconnector_id yang di-apply
        ic_ids_to_apply = {f["properties"]["interconnector_id"] for f in feats}
        existing = [f for f in existing
                    if not (f.get("properties", {}).get("is_interconnector")
                             and f["properties"].get("interconnector_id") in ic_ids_to_apply)]
        existing.extend(feats)
        gj["features"] = existing
        gj_path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
        print(f"  {region}: appended {len(feats)} interconnector feature(s)")

    print(f"\n  Resolved: {stats['resolved']}, Unresolved: {stats['unresolved']}, "
          f"Cross-region dup: {stats['duplicated_across_regions']}")


if __name__ == "__main__":
    apply_interconnectors()
