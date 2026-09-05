#!/usr/bin/env python3
"""Render RUPTL planned transmission rows sebagai GeoJSON LineString.

Untuk tiap baris RUPTL transmisi (dari `data/processed/ruptl_transmission_{region}.csv`):
  1. Cari endpoint coord: from_bus dan to_bus di-lookup ke substation_master
     via name-stem match (dalam provinsi yang sama).
  2. Kalau kedua endpoint ketemu → draw straight LineString antara keduanya.
  3. Kalau salah satu tidak ketemu → skip (dan hitung sebagai
     `endpoint_unresolved` untuk audit). Rows ini tetap ada di CSV untuk
     manual endpoint resolution nanti.

Output:
    data/processed/transmission_{region}.reconciled.geojson — merge baseline
    OSM transmission features + RUPTL planned lines (baru), non-destructive
    ke baseline `.geojson`.

Frontend backward-compat: baseline features tetap punya property yang sama
plus tambahan `match_tier=BASELINE`. Planned RUPTL features punya
`match_tier=PLANNED_RUPTL` + property RUPTL lengkap (from_bus, to_bus,
voltage_kv, target_cod_year, dll).

Endpoint lookup pakai algoritma sama dengan
`scripts/geocode_ruptl_generators.py`: token overlap ≥ 0.5.

Usage:
    python3 scripts/render_ruptl_transmission_geojson.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import plant_name_tokens  # noqa: E402


# ------------------------------------------------------------
# Bus-name specific stopwords (extend base stopwords).
# ------------------------------------------------------------
# Kata-kata yang muncul di bus name RUPTL/baseline tapi bukan bagian dari
# tempat sebenarnya. Contoh: "Inc." (increment), "Tx." (transformer/tap),
# "SUTT", "KTT" (kabel tegangan tinggi).
BUS_STOPWORDS = frozenset({
    "inc", "tx", "sutt", "sktt", "sutet", "sklt", "ktt", "tap",
    "eksisting", "existing", "eksisiting",  # sic — typo di RUPTL
})


def bus_tokens(s: str) -> set[str]:
    """Token set untuk bus/substation name, exclude bus-specific noise."""
    return plant_name_tokens(s) - BUS_STOPWORDS


# ------------------------------------------------------------
# Substation gazetteer
# ------------------------------------------------------------
def load_substation_gazetteer(path: Path) -> list[dict]:
    """Load substation baseline sebagai list of {tokens, lat, lon, prov, id, name}."""
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8-sig") as f:
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
                "tokens": bus_tokens(name),
                "lat": lat, "lon": lon,
                "prov": (r.get("province") or "").strip().lower(),
                "id": (r.get("id") or "").strip(),
                "name": name,
            })
    return out


def lookup_bus(bus_name: str, province: str,
                gazetteer: list[dict]) -> Optional[dict]:
    """Cari substation di gazetteer yang match bus_name.

    Threshold: minimal 1 token match + score ≥ 0.5 (mayoritas token).
    """
    tokens = bus_tokens(bus_name)
    if not tokens:
        return None
    prov_norm = province.lower()
    best = None
    best_score = 0.0
    for pin in gazetteer:
        if pin["prov"] != prov_norm:
            continue
        common = tokens & pin["tokens"]
        if not common:
            continue
        score = len(common) / max(len(tokens), 1)
        if score > best_score:
            best_score = score
            best = pin
    if best and best_score >= 0.5:
        return best
    return None


# ------------------------------------------------------------
# Main merge
# ------------------------------------------------------------
def render(region: str, project_root: Path) -> int:
    processed = project_root / "data/processed"
    base_gj_path = processed / f"transmission_{region}.geojson"
    ruptl_csv_path = processed / f"ruptl_transmission_{region}.csv"
    sub_csv_path = processed / f"substation_master_{region}.csv"
    out_path = processed / f"transmission_{region}.reconciled.geojson"

    if not base_gj_path.exists():
        print(f"[render_trm] missing: {base_gj_path}", file=sys.stderr)
        return 2
    if not ruptl_csv_path.exists():
        print(f"[render_trm] missing: {ruptl_csv_path}", file=sys.stderr)
        return 2
    if not sub_csv_path.exists():
        print(f"[render_trm] missing: {sub_csv_path}", file=sys.stderr)
        return 2

    print(f"[render_trm] region={region}")

    # Load baseline GeoJSON
    baseline = json.loads(base_gj_path.read_text(encoding="utf-8"))
    features = baseline.get("features", [])
    print(f"  baseline transmission features: {len(features)}")

    # Tag baseline features sebagai match_tier=BASELINE
    for f in features:
        props = f.setdefault("properties", {})
        props.setdefault("match_tier", "BASELINE")
        props.setdefault("source", "osm")

    # Load substation gazetteer
    gazetteer = load_substation_gazetteer(sub_csv_path)
    print(f"  substation gazetteer: {len(gazetteer)} pins")

    # Load RUPTL transmisi rows
    with ruptl_csv_path.open(encoding="utf-8-sig") as f:
        ruptl_rows = list(csv.DictReader(f))
    print(f"  RUPTL transmission rows: {len(ruptl_rows)}")

    added = 0
    partial_endpoints = 0
    unresolved = 0
    for r in ruptl_rows:
        prov = r.get("province", "")
        from_pin = lookup_bus(r.get("from_bus", ""), prov, gazetteer)
        to_pin = lookup_bus(r.get("to_bus", ""), prov, gazetteer)

        if not from_pin and not to_pin:
            unresolved += 1
            continue
        if not from_pin or not to_pin:
            partial_endpoints += 1
            continue

        # Draw straight LineString between endpoints (planned, tidak
        # mengikuti terrain — user should read as approx route indicator)
        coords = [[from_pin["lon"], from_pin["lat"]],
                  [to_pin["lon"], to_pin["lat"]]]

        props = {
            "id": "RUPTL:" + r.get("id", ""),
            "ruptl_id": r.get("id", ""),
            "name": r.get("name", ""),
            "from_bus": r.get("from_bus", ""),
            "to_bus": r.get("to_bus", ""),
            "from_id": from_pin["id"],
            "to_id": to_pin["id"],
            "voltage_kv": r.get("voltage_kv", ""),
            "voltage_class": (r.get("voltage_kv", "") + " kV").strip(),
            "action_type": r.get("action_type", ""),
            "circuits": r.get("circuits", ""),
            "line_type": r.get("line_type", ""),
            "length_km": r.get("length_km", ""),
            "target_cod_year": r.get("target_cod_year", ""),
            "status": r.get("status", ""),
            "province": r.get("province", ""),
            "match_tier": "PLANNED_RUPTL",
            "source": "ruptl",
            "source_page": r.get("source_page", ""),
            "source_table": r.get("source_table", ""),
        }

        feat = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": props,
        }
        features.append(feat)
        added += 1

    print(f"\n  added {added} PLANNED_RUPTL LineString features "
          f"(endpoints resolved from substation gazetteer)")
    print(f"  {partial_endpoints} rows with 1 endpoint unresolved (skipped)")
    print(f"  {unresolved} rows with both endpoints unresolved (skipped)")
    print(f"  → total in output: {len(features)} features")

    baseline["features"] = features
    out_path.write_text(json.dumps(baseline, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\n  wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    opts = ap.parse_args()
    return render(opts.region, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
