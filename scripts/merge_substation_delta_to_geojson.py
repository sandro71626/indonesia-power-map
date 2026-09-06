#!/usr/bin/env python3
"""Merge substation delta ke baseline substation GeoJSON.

Baseline `substations_{region}.geojson` (dari OSM) di-enrich dengan info
delta RUPTL, plus tambah NEW_BUILD planned GI sebagai fitur baru.

Delta classification (dari detect_substation_delta.py):
  EXISTING_EXT      → baseline feature di-tag "planned extension" + RUPTL meta
  EXISTING_UPRATE   → baseline feature di-tag "planned uprate" + RUPTL meta
  RECLASSIFY_NEW    → baseline feature di-tag "planned new (dup?)" + RUPTL meta
  NEW_BUILD         → new Point feature, geocoded via gazetteer

Geocoding NEW_BUILD:
  1. Cari di baseline substation gazetteer (name-token match, same province)
  2. Cari di planned transmission endpoints (from_bus/to_bus RUPTL rows)
  3. Fallback: province centroid + deterministic jitter (low confidence)

Feature yang coord_confidence=low di-SKIP dari render (sama pattern
dengan planned generator) supaya map tidak cluster di province centroids.

Output:
    data/processed/substations_{region}.reconciled.geojson

Canonical temporal fields yang di-populate:
    target_cod_year     — untuk PLANNED_RUPTL features (dari RUPTL row langsung)
    target_cod_year_ruptl — untuk baseline features yang ada delta match

Canonical enum fields (uppercase, untuk future year filter):
    action_norm    — NEW | EXTENSION | UPRATE | ""
    status_norm    — PLANNED | CONSTRUCTION | PROCUREMENT | COMMITTED | PROPOSED | UNKNOWN

Usage:
    python3 scripts/merge_substation_delta_to_geojson.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import plant_name_tokens  # noqa: E402
from geocode_ruptl_generators import (  # noqa: E402
    PROVINCE_CENTROID, deterministic_jitter,
)


# ------------------------------------------------------------
# Status/action normalization ke uppercase enum
# ------------------------------------------------------------
STATUS_NORM_MAP = {
    "planned": "PLANNED",
    "rencana": "PLANNED",
    "construction": "CONSTRUCTION",
    "konstruksi": "CONSTRUCTION",
    "kontruksi": "CONSTRUCTION",  # typo umum di RUPTL PDF
    "procurement": "PROCUREMENT",
    "pengadaan": "PROCUREMENT",
    "committed": "COMMITTED",
    "ppa": "COMMITTED",
    "proposed": "PROPOSED",
    "eksplorasi": "PROPOSED",
}

ACTION_NORM_MAP = {
    "new": "NEW", "baru": "NEW",
    "extension": "EXTENSION", "ext": "EXTENSION",
    "uprate": "UPRATE", "uprating": "UPRATE", "upr": "UPRATE",
}


def norm_status(s: str) -> str:
    if not s:
        return "UNKNOWN"
    key = str(s).strip().lower()
    return STATUS_NORM_MAP.get(key, "UNKNOWN" if not key else key.upper())


def norm_action(s: str) -> str:
    if not s:
        return ""
    key = str(s).strip().lower()
    return ACTION_NORM_MAP.get(key, "")


# ------------------------------------------------------------
# Bus tokens (sub-specific stopwords)
# ------------------------------------------------------------
BUS_STOPWORDS = frozenset({
    "gi", "gis", "gitet", "new", "baru", "ext", "extension", "uprate",
    "switching", "inc", "tx",
})


def bus_tokens(s: str) -> set[str]:
    return plant_name_tokens(s) - BUS_STOPWORDS


# ------------------------------------------------------------
# Gazetteer for NEW_BUILD geocoding
# ------------------------------------------------------------
def load_substation_pins(csv_path: Path) -> list[dict]:
    """Baseline substations sebagai gazetteer (name→coord)."""
    if not csv_path.exists():
        return []
    out = []
    with csv_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r.get("lat") or "")
                lon = float(r.get("lon") or "")
            except ValueError:
                continue
            name = (r.get("name") or "").strip()
            if not name:
                continue
            out.append({
                "id": (r.get("id") or "").strip(),
                "name": name,
                "lat": lat, "lon": lon,
                "prov": (r.get("province") or "").strip().lower(),
                "tokens": bus_tokens(name),
            })
    return out


def load_trm_endpoint_pins(csv_path: Path, sub_gazetteer: list[dict]) -> list[dict]:
    """RUPTL transmisi endpoints sebagai gazetteer tambahan.

    Untuk tiap unique from_bus/to_bus di planning transmisi, cari di sub
    baseline. Kalau ketemu → sudah ke-cover. Kalau baru (belum ada di
    baseline), belum bisa geocode (butuh cross-reference). Skip.

    Return: list gazetteer entries (subset of sub_gazetteer that appear
    as endpoints). Untuk simplicity, kita cukup pakai sub_gazetteer saja.
    """
    return sub_gazetteer  # placeholder — sub_gazetteer already used directly


def match_gazetteer(row_name: str, row_prov: str,
                     gazetteer: list[dict]) -> Optional[dict]:
    """Cari substation dengan token overlap terbesar dalam provinsi sama."""
    tokens = bus_tokens(row_name)
    if not tokens:
        return None
    prov_norm = row_prov.lower()
    best = None
    best_score = 0.0
    for pin in gazetteer:
        if pin["prov"] != prov_norm:
            continue
        common = tokens & pin["tokens"]
        if not common:
            continue
        score = len(common) / max(len(tokens | pin["tokens"]), 1)
        if score > best_score:
            best_score = score
            best = pin
    if best and best_score >= 0.5:
        return best
    return None


# ------------------------------------------------------------
# Main merge
# ------------------------------------------------------------
def merge(region: str, project_root: Path) -> int:
    processed = project_root / "data/processed"
    base_gj_path = processed / f"substations_{region}.geojson"
    delta_csv_path = processed / f"substation_delta_{region}.csv"
    sub_csv_path = processed / f"substation_master_{region}.csv"
    out_path = processed / f"substations_{region}.reconciled.geojson"

    if not base_gj_path.exists():
        print(f"[merge_sub] missing: {base_gj_path}", file=sys.stderr)
        return 2
    if not delta_csv_path.exists():
        print(f"[merge_sub] missing: {delta_csv_path} — "
              f"run detect_substation_delta --write first", file=sys.stderr)
        return 2

    print(f"[merge_sub] region={region}")

    baseline = json.loads(base_gj_path.read_text(encoding="utf-8"))
    features = baseline.get("features", [])
    print(f"  baseline features: {len(features)}")

    # Load delta rows
    with delta_csv_path.open(encoding="utf-8-sig") as f:
        delta_rows = list(csv.DictReader(f))
    print(f"  delta rows: {len(delta_rows)}")

    # Index delta by baseline_id (untuk enrich) dan by ruptl_id
    delta_by_baseline: dict[str, list[dict]] = {}
    new_build_rows: list[dict] = []
    for d in delta_rows:
        cls = d.get("classification", "")
        bid = d.get("baseline_id", "").strip()
        if cls == "NEW_BUILD":
            new_build_rows.append(d)
        elif bid:
            delta_by_baseline.setdefault(bid, []).append(d)

    # Set baseline tier default + enrich yang punya delta match
    enriched = 0
    for feat in features:
        props = feat.setdefault("properties", {})
        fid = (props.get("id") or "").strip()
        props["match_tier"] = "BASELINE"
        props["source"] = props.get("source_id") or "osm"
        # Canonical temporal & enum fields (baseline: kosong kecuali di-enrich)
        props["target_cod_year_ruptl"] = ""
        props["action_norm"] = ""
        props["status_norm"] = ""

        matches = delta_by_baseline.get(fid, [])
        if not matches:
            continue

        # Pilih match berdasarkan classification priority
        priority = {"EXISTING_UPRATE": 3, "EXISTING_EXT": 2, "RECLASSIFY_NEW": 1}
        matches.sort(key=lambda m: -priority.get(m["classification"], 0))
        best = matches[0]
        props["match_tier"] = "PLANNED_" + best["classification"]
        props["ruptl_id"] = best.get("ruptl_id", "")
        props["action_type_ruptl"] = best.get("action_type", "")
        props["action_norm"] = norm_action(best.get("action_type", ""))
        props["status_ruptl"] = best.get("status", "")
        props["status_norm"] = norm_status(best.get("status", ""))
        props["target_cod_year_ruptl"] = best.get("target_cod_year", "")
        props["capacity_mva_ruptl"] = best.get("capacity_mva", "")
        props["voltage_kv_ruptl"] = best.get("voltage_kv", "")
        props["source_page"] = best.get("source_page", "")
        props["source_table"] = best.get("source_table", "")
        enriched += 1

    print(f"  enriched baseline features: {enriched}")

    # Geocode + append NEW_BUILD sebagai fitur baru
    sub_gazetteer = load_substation_pins(sub_csv_path)
    added = 0
    skipped_placeholder = 0
    skipped_dup = 0
    seen_names_geocoded: set[tuple] = set()  # dedup (name.lower(), province)

    for r in new_build_rows:
        name = (r.get("name") or "").strip()
        prov = (r.get("province") or "").strip()
        if not name or not prov:
            continue
        dedup_key = (name.lower(), prov.lower())
        if dedup_key in seen_names_geocoded:
            skipped_dup += 1
            continue
        seen_names_geocoded.add(dedup_key)

        # Geocode: gazetteer → province centroid
        pin = match_gazetteer(name, prov, sub_gazetteer)
        if pin:
            lat, lon = pin["lat"], pin["lon"]
            coord_source = f"gazetteer_substation:{pin['id']}"
            coord_confidence = "medium"
        else:
            centroid = PROVINCE_CENTROID.get(prov.lower())
            if not centroid:
                continue
            dlon, dlat = deterministic_jitter(r.get("ruptl_id", "") or name)
            lon, lat = centroid[0] + dlon, centroid[1] + dlat
            coord_source = "province_centroid"
            coord_confidence = "low"

        if coord_confidence == "low":
            skipped_placeholder += 1
            continue

        # Feature properties — reuse existing sub feature schema sebisa mungkin
        # (id, name, voltage, capacity_mva, province, source_id) + tambah RUPTL meta.
        capacity_mva = r.get("capacity_mva", "")
        voltage_kv = r.get("voltage_kv", "")
        props = {
            "id": "RUPTL:" + r.get("ruptl_id", ""),
            "ruptl_id": r.get("ruptl_id", ""),
            "name": name,
            "voltage": voltage_kv,  # match baseline field name
            "capacity_mva": capacity_mva,
            "province": prov,
            "system": "",
            "source_id": "RUPTL-2025-2034",
            "source_table": r.get("source_table", ""),
            "source_page": r.get("source_page", ""),
            "source": "ruptl",
            "match_tier": "PLANNED_RUPTL",
            "match_source": coord_source,  # match baseline field name
            "coord_source": coord_source,
            "coord_confidence": coord_confidence,
            "is_placeholder": False,
            # Canonical temporal + enum fields
            "target_cod_year": r.get("target_cod_year", ""),
            "target_cod_year_ruptl": "",  # PLANNED: kosong (use target_cod_year)
            "action_type_ruptl": r.get("action_type", ""),
            "action_norm": norm_action(r.get("action_type", "")),
            "status_ruptl": r.get("status", ""),
            "status_norm": norm_status(r.get("status", "")),
        }
        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        }
        features.append(feat)
        added += 1

    print(f"  added {added} PLANNED_RUPTL (NEW_BUILD) features")
    if skipped_dup:
        print(f"  skipped {skipped_dup} duplicate names")
    if skipped_placeholder:
        print(f"  skipped {skipped_placeholder} placeholder-only (province centroid, "
              f"tidak di-render supaya map tetap bersih)")

    baseline["features"] = features
    out_path.write_text(json.dumps(baseline, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\n  wrote {out_path} ({len(features)} features total)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    opts = ap.parse_args()
    return merge(opts.region, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
