#!/usr/bin/env python3
"""Apply interconnector curation ke transmission reconciled GeoJSON.

Reads: data/overrides/interconnectors_curated.csv
Two modes berdasarkan `existing_osm_id` column:

  A. TAG_EXISTING_OSM (preferred when OSM has real cable/line geometry):
     - Find OSM way di transmission_{region}.reconciled.geojson dengan
       osm_id matching CSV.existing_osm_id
     - Add interconnector metadata sebagai overlay properties ke feature
       existing tersebut. Real multi-point geometry preserved.
     - No new feature appended.

  B. MANUAL_STRAIGHT (fallback when OSM tidak punya cable, mis. Selat Bali):
     - Resolve endpoints via sub_id (baseline) atau explicit lat/lon
     - Create straight LineString feature dengan explicit provenance:
         geometry_source = 'manual_straight'
         geometry_confidence = 'low'
         topology_confidence = <curated value>
     - Append feature ke transmission_{region}.reconciled.geojson

Idempotent — semua feature dengan `is_interconnector=true` + matching
`interconnector_id` di-drop dulu sebelum apply (baik tag maupun manual
mode). Ini juga bersih up any stale interconnector dari run sebelumnya
yang sudah tidak ada di curation CSV.

Confidence field distinction:
  geometry_confidence  = akurasi shape line (osm_way high, manual_straight low)
  topology_confidence  = akurasi endpoint↔network connection
                          (both sub_id valid + OSM way present → high;
                           satu manual coord → low; approximation → low)

Usage:
    python3 scripts/apply_interconnectors.py
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from collections import defaultdict
from math import sin, cos, sqrt, asin, pi

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


def base_props(row, from_pin=None, to_pin=None, from_src="", to_src=""):
    """Common interconnector metadata dari CSV row."""
    ic_id = row.get("interconnector_id", "").strip()
    voltage_kv = row.get("voltage_kv", "").strip()
    status = (row.get("status", "").strip().lower() or "planned")
    is_existing = status == "existing"
    props = {
        "id": ic_id,
        "interconnector_id": ic_id,
        "is_interconnector": True,
        "name": row.get("name", ""),
        "voltage_kv": voltage_kv,
        "voltage_class": (voltage_kv + " kV") if voltage_kv else "",
        "voltage_kv_max": voltage_kv,
        "status": status,
        "status_norm": "OPERATIONAL" if is_existing else "PLANNED",
        "technology": row.get("technology", ""),
        "match_tier": "BASELINE" if is_existing else "PLANNED_RUPTL",
        "action_type": row.get("action_type", "New" if not is_existing else ""),
        "action_norm": "NEW" if not is_existing else "",
        "source": row.get("evidence", ""),
        "source_url": row.get("source_url", ""),
        "target_cod_year": row.get("target_cod_year", ""),
        "target_cod_year_ruptl": row.get("target_cod_year", "") if not is_existing else "",
        "geometry_source": row.get("geometry_source", ""),
        "geometry_confidence": row.get("geometry_confidence", ""),
        "topology_confidence": row.get("topology_confidence", ""),
        "curated_by": row.get("curated_by", ""),
        "curated_date": row.get("curated_date", ""),
    }
    # Endpoint metadata
    if from_pin:
        props["from_sub_id"] = row.get("from_sub_id", "").strip()
        props["from_region"] = from_pin.get("region", row.get("from_region",""))
        props["from_name"] = from_pin.get("name") or row.get("from_name","")
        props["from_endpoint_source"] = from_src
        props["from_id"] = row.get("from_sub_id", "").strip()
        props["circuit_from_name"] = from_pin.get("name") or row.get("from_name","")
    if to_pin:
        props["to_sub_id"] = row.get("to_sub_id", "").strip()
        props["to_region"] = to_pin.get("region", row.get("to_region",""))
        props["to_name"] = to_pin.get("name") or row.get("to_name","")
        props["to_endpoint_source"] = to_src
        props["to_id"] = row.get("to_sub_id", "").strip()
        props["circuit_to_name"] = to_pin.get("name") or row.get("to_name","")
    return props


def resolve_endpoint(row, prefix, sub_idx):
    """Resolve endpoint via sub_id + fallback manual coord."""
    sid = row.get(f"{prefix}_sub_id", "").strip()
    if sid and sid in sub_idx:
        return sub_idx[sid], "resolved"
    try:
        lat = float(row.get(f"{prefix}_lat", ""))
        lon = float(row.get(f"{prefix}_lon", ""))
        return ({"region": row.get(f"{prefix}_region", "").strip().lower() or "manual",
                  "name": row.get(f"{prefix}_name", "").strip() or f"({prefix} manual)",
                  "lat": lat, "lon": lon}, "manual")
    except (ValueError, TypeError):
        return None, "missing"


def haversine_km(lon1, lat1, lon2, lat2):
    p = pi / 180
    h = (sin((lat2-lat1)*p/2)**2 + cos(lat1*p)*cos(lat2*p)*sin((lon2-lon1)*p/2)**2)
    return 2 * 6371.0088 * asin(sqrt(max(0.0, h)))


def clean_stale_tags(features, ic_ids_active):
    """Untuk mode TAG_EXISTING_OSM: kalau feature punya is_interconnector=true
    tapi interconnector_id-nya tidak ada di curation aktif → un-tag feature.
    Idempotent — supaya OSM way tidak carry stale interconnector metadata
    dari run sebelumnya.
    """
    IC_KEYS = ['interconnector_id', 'is_interconnector', 'geometry_source',
                'geometry_confidence', 'topology_confidence',
                'from_endpoint_source', 'to_endpoint_source',
                'curated_by', 'curated_date']
    unstaled = 0
    for f in features:
        p = f.get('properties', {})
        if p.get('is_interconnector') and p.get('interconnector_id') not in ic_ids_active:
            # This feature was previously tagged but no longer in curation
            for k in IC_KEYS:
                p.pop(k, None)
            # Restore basic props if osm_id present (this was originally OSM baseline)
            if p.get('osm_id'):
                # Not a synthetic feature — was OSM baseline that got tagged
                unstaled += 1
    return unstaled


def apply():
    rows = load_curation()
    if not rows:
        print(f"[apply_interconnectors] no curation rows in {CURATION_PATH}")
        return

    sub_idx = build_sub_index()
    print(f"[apply_interconnectors] loaded {len(rows)} interconnectors, "
          f"{len(sub_idx)} substation index entries")

    active_ic_ids = {r.get("interconnector_id","").strip() for r in rows}

    # Process each region separately — load, drop synthetic straight-line IC
    # features (mode B), un-tag stale OSM overlays, then apply active rows.
    region_gj_cache = {}
    for r in REGIONS:
        p = PROC / f"transmission_{r}.reconciled.geojson"
        if p.exists():
            region_gj_cache[r] = json.loads(p.read_text())

    # STAGE 1: cleanup — drop synthetic + untag stale OSM
    for r, gj in region_gj_cache.items():
        feats = gj.get("features", [])
        # Drop synthetic features (2-point straight line dengan is_interconnector tag)
        before = len(feats)
        feats = [f for f in feats if not (
            f.get('properties',{}).get('is_interconnector')
            and not f.get('properties',{}).get('osm_id')
        )]
        drops = before - len(feats)
        # Un-tag OSM overlays whose IC id not in active set
        unstale = clean_stale_tags(feats, active_ic_ids)
        gj['features'] = feats
        if drops or unstale:
            print(f"  cleanup {r}: dropped {drops} synthetic features, un-tagged {unstale} stale overlays")

    # STAGE 2: apply active rows
    stats = {"tagged_osm": 0, "created_synthetic": 0, "unresolved": 0}
    for row in rows:
        ic_id = row.get("interconnector_id","").strip()
        if not ic_id:
            print(f"  skip empty ic_id row")
            continue
        osm_id = (row.get("existing_osm_id","") or "").strip()

        if osm_id:
            # MODE A: Tag existing OSM way
            # Find in ALL regions (interconnector could be in any bundle)
            tagged_regions = []
            for r, gj in region_gj_cache.items():
                for f in gj.get("features", []):
                    fp = f.get("properties", {})
                    if fp.get("osm_id") == osm_id:
                        # Overlay tag
                        from_pin, from_src = resolve_endpoint(row, "from", sub_idx)
                        to_pin, to_src = resolve_endpoint(row, "to", sub_idx)
                        overlay = base_props(row, from_pin, to_pin, from_src, to_src)
                        # Preserve real OSM geometry & existing baseline properties
                        # (voltage_kv_max, length_km, etc). Overlay adds tags.
                        for k, v in overlay.items():
                            fp[k] = v
                        # Force is_interconnector semantic
                        fp["is_interconnector"] = True
                        fp["geometry_source"] = "osm_way"
                        tagged_regions.append(r)
            if tagged_regions:
                print(f"  {ic_id}: TAG_EXISTING_OSM → tagged osm_id={osm_id} in regions {tagged_regions}")
                stats["tagged_osm"] += 1
            else:
                print(f"  ⚠ {ic_id}: existing_osm_id={osm_id} NOT FOUND in any region bundle")
                stats["unresolved"] += 1
        else:
            # MODE B: Manual straight-line
            from_pin, from_src = resolve_endpoint(row, "from", sub_idx)
            to_pin, to_src = resolve_endpoint(row, "to", sub_idx)
            if not from_pin or not to_pin:
                print(f"  ⚠ {ic_id}: MANUAL_STRAIGHT unresolved endpoints "
                      f"from={from_src} to={to_src}")
                stats["unresolved"] += 1
                continue
            props = base_props(row, from_pin, to_pin, from_src, to_src)
            props["endpoint_confidence"] = "both"
            # Length haversine
            length_km = haversine_km(from_pin["lon"], from_pin["lat"],
                                       to_pin["lon"], to_pin["lat"])
            props["length_km"] = round(length_km, 2)
            props["geometry_source"] = row.get("geometry_source","manual_straight")
            feat = {
                "type": "Feature",
                "geometry": {"type": "LineString",
                              "coordinates": [[from_pin["lon"], from_pin["lat"]],
                                              [to_pin["lon"], to_pin["lat"]]]},
                "properties": props,
            }
            target_regions = {from_pin["region"], to_pin["region"]} & set(REGIONS)
            for tr in target_regions:
                region_gj_cache[tr]["features"].append(feat)
            print(f"  {ic_id}: MANUAL_STRAIGHT → appended to regions {sorted(target_regions)} "
                  f"(length={length_km:.2f}km, geom_conf={props['geometry_confidence']}, "
                  f"topo_conf={props['topology_confidence']})")
            stats["created_synthetic"] += 1

    # STAGE 3: write back
    for r, gj in region_gj_cache.items():
        p = PROC / f"transmission_{r}.reconciled.geojson"
        p.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Tagged existing OSM ways: {stats['tagged_osm']}")
    print(f"  Created synthetic (manual straight): {stats['created_synthetic']}")
    print(f"  Unresolved: {stats['unresolved']}")


if __name__ == "__main__":
    apply()
