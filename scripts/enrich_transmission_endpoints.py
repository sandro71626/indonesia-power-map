#!/usr/bin/env python3
"""Infer endpoint substation untuk tiap baseline transmission LineString.

Baseline transmisi (dari OSM) hanya berupa LineString tanpa metadata
endpoint. Untuk enable full reconciliation vs RUPTL (yang sebutkan
From/To bus explicit), kita perlu tebak endpoint substation dari
geometri.

Algorithm:
  1. Ambil koordinat pertama & terakhir dari LineString.
  2. Untuk tiap endpoint, cari substation baseline terdekat via haversine.
  3. Kalau jarak ≤ threshold (default 3 km) → attach `from_id`/`to_id` +
     `from_name`/`to_name` ke properties, plus `endpoint_confidence`.
  4. Kalau jarak > threshold → mark unresolved (kosong).

Output: overwrite `data/processed/transmission_{region}.geojson` dengan
tambahan property. IDempotent: run ulang → hasilnya sama.

Property yang ditambahkan:
    from_id, from_name, from_distance_km
    to_id,   to_name,   to_distance_km
    endpoint_confidence  (both / partial / none)

Usage:
    python3 scripts/enrich_transmission_endpoints.py --region jamali
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
from _shared.name_stem import haversine_km  # noqa: E402


# ------------------------------------------------------------
# Load substation gazetteer (with coords)
# ------------------------------------------------------------
def load_substations(path: Path) -> list[dict]:
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
                "id": (r.get("id") or "").strip(),
                "name": name,
                "lat": lat, "lon": lon,
                "voltage": (r.get("voltage") or "").strip(),
            })
    return out


def nearest_substation(lon: float, lat: float,
                        subs: list[dict],
                        max_km: float = 3.0
                        ) -> tuple[Optional[dict], Optional[float]]:
    """Cari substation terdekat ke titik (lon, lat). Return (pin, dist_km)
    atau (None, None) kalau tidak ada yang dalam radius max_km.
    """
    best = None
    best_d = max_km + 1.0
    for s in subs:
        d = haversine_km((lon, lat), (s["lon"], s["lat"]))
        if d < best_d:
            best_d = d
            best = s
    if best is None or best_d > max_km:
        return None, None
    return best, best_d


# ------------------------------------------------------------
# Enrich
# ------------------------------------------------------------
def enrich(region: str, project_root: Path, max_km: float) -> int:
    processed = project_root / "data/processed"
    gj_path = processed / f"transmission_{region}.geojson"
    sub_path = processed / f"substation_master_{region}.csv"

    if not gj_path.exists():
        print(f"[enrich_endpt] missing: {gj_path}", file=sys.stderr)
        return 2
    if not sub_path.exists():
        print(f"[enrich_endpt] missing: {sub_path}", file=sys.stderr)
        return 2

    subs = load_substations(sub_path)
    print(f"[enrich_endpt] region={region}, {len(subs)} substation pins, "
          f"max_km={max_km}")

    gj = json.loads(gj_path.read_text(encoding="utf-8"))
    features = gj.get("features", [])
    print(f"  baseline LineStrings: {len(features)}")

    both = partial = none = 0
    for feat in features:
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if not coords or len(coords) < 2:
            continue

        # First + last coord (LineString: [[lon,lat], [lon,lat], ...])
        first = coords[0]
        last = coords[-1]
        if len(first) < 2 or len(last) < 2:
            continue

        from_pin, from_d = nearest_substation(first[0], first[1], subs, max_km)
        to_pin, to_d = nearest_substation(last[0], last[1], subs, max_km)

        # Kalau from_pin sama dengan to_pin (loop / very short line), skip to_pin
        if from_pin and to_pin and from_pin["id"] == to_pin["id"]:
            to_pin, to_d = None, None

        props = feat.setdefault("properties", {})
        props["from_id"] = from_pin["id"] if from_pin else ""
        props["from_name"] = from_pin["name"] if from_pin else ""
        props["from_distance_km"] = round(from_d, 3) if from_d is not None else ""
        props["to_id"] = to_pin["id"] if to_pin else ""
        props["to_name"] = to_pin["name"] if to_pin else ""
        props["to_distance_km"] = round(to_d, 3) if to_d is not None else ""

        if from_pin and to_pin:
            props["endpoint_confidence"] = "both"
            both += 1
        elif from_pin or to_pin:
            props["endpoint_confidence"] = "partial"
            partial += 1
        else:
            props["endpoint_confidence"] = "none"
            none += 1

    total = len(features)
    print(f"\n  both endpoints resolved:    {both:>4}  ({100*both/total:.1f}%)")
    print(f"  partial (1 endpoint):       {partial:>4}  ({100*partial/total:.1f}%)")
    print(f"  none (isolated segments):   {none:>4}  ({100*none/total:.1f}%)")

    gj_path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"\n  updated {gj_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    ap.add_argument("--max-km", type=float, default=3.0,
                    help="Max jarak (km) dari endpoint ke substation")
    opts = ap.parse_args()
    return enrich(opts.region, Path(__file__).resolve().parents[1],
                   opts.max_km)


if __name__ == "__main__":
    raise SystemExit(main())
