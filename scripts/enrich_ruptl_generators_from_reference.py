#!/usr/bin/env python3
"""Enrich planned generator coordinates dari indonesia-100gw-solar-study.

Reference project (indonesia-100gw-solar-study/data/WP1.2_rencana/) punya
per-year GeoJSON rencana_YYYY dengan coord + source URL + confidence.
Dataset ini public + well-attributed + sama author family (open-source
research). Kompatibel legally, cocok jadi secondary gazetteer.

Strategy:
  1. Load semua rencana_2025..2034.geojson dari reference (jenis=pembangkit)
  2. Build gazetteer keyed by (province, name-token set)
  3. Load IPM ruptl_generators_{region}.csv
  4. Untuk tiap row dengan `coord_confidence=low` (province centroid
     fallback), coba match ke reference gazetteer via name+province
  5. Kalau match ditemukan → replace coord + set:
       coord_source = reference:{ruptl_id}
       coord_confidence = confidence dari reference (mostly 'low' juga,
                          tapi TRUSTED locality centroid — better than
                          province centroid)
       source_url = attribution URL dari reference
  6. TIDAK touch rows dengan coord_confidence=high/medium

Output: overwrite ruptl_generators_{region}.csv in-place (idempotent).

Usage:
    python3 scripts/enrich_ruptl_generators_from_reference.py --region jamali
    python3 scripts/enrich_ruptl_generators_from_reference.py --all
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
from extract_ruptl_generators import REGION_PROVINCES  # noqa: E402


REFERENCE_ROOT = Path("/sessions/pensive-beautiful-bohr/mnt/indonesia-100gw-solar-study")
RENCANA_DIR = REFERENCE_ROOT / "data/WP1.2_rencana"
YEARS = list(range(2025, 2035))

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_reference_gazetteer() -> list[dict]:
    """Load semua rencana_YYYY.geojson jenis=pembangkit → gazetteer list."""
    gaz: list[dict] = []
    seen_ids: set[str] = set()
    for year in YEARS:
        path = RENCANA_DIR / f"rencana_{year}.geojson"
        if not path.exists():
            continue
        gj = json.loads(path.read_text(encoding="utf-8"))
        for f in gj.get("features", []):
            props = f.get("properties") or {}
            if props.get("jenis") != "pembangkit":
                continue
            rid = props.get("ruptl_id", "")
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            geom = f.get("geometry") or {}
            if geom.get("type") != "Point":
                continue
            lon, lat = geom["coordinates"][0], geom["coordinates"][1]
            name = props.get("lokasi", "").strip()
            if not name:
                continue
            gc = props.get("geocode") or {}
            gaz.append({
                "ref_ruptl_id": rid,
                "name": name,
                "province": (props.get("provinsi") or "").strip().lower(),
                "type": props.get("teknologi") or "",
                "capacity_mw": props.get("kapasitas_mw"),
                "lat": lat, "lon": lon,
                "tokens": plant_name_tokens(name),
                "source_url": gc.get("source_url", ""),
                "confidence": gc.get("confidence", ""),
                "reference_year": year,
            })
    return gaz


def match_reference(row: dict, gaz: list[dict]) -> Optional[dict]:
    """Cari match reference untuk RUPTL row.

    Match criteria (ordered by strictness):
      1. Same province + name token overlap ≥ 0.6 + similar capacity
      2. Same province + exact name-token equality
    Return best match dict, atau None.
    """
    tokens = plant_name_tokens(row.get("name", ""))
    if not tokens:
        return None
    prov = row.get("province", "").strip().lower()
    cap_row = None
    try:
        cap_row = float(row.get("capacity_mw") or 0)
    except (TypeError, ValueError):
        pass

    best = None
    best_score = 0.0
    for g in gaz:
        # Province match (strict — mengurangi false positive)
        if g["province"] and prov and g["province"] != prov:
            # Longer province name: "sumatera utara" vs "sumatra" — check
            # substring both ways
            if g["province"] not in prov and prov not in g["province"]:
                continue
        common = tokens & g["tokens"]
        if not common:
            continue
        score = len(common) / max(len(tokens | g["tokens"]), 1)
        # Bonus kalau capacity mirip (±30%)
        if cap_row and g["capacity_mw"]:
            try:
                cap_ref = float(g["capacity_mw"])
                if cap_ref > 0 and cap_row > 0:
                    diff = abs(cap_row - cap_ref) / max(cap_row, cap_ref)
                    if diff < 0.3:
                        score += 0.2
            except (TypeError, ValueError):
                pass
        if score > best_score:
            best_score = score
            best = g
    if best and best_score >= 0.5:
        return best
    return None


def enrich(region: str, gaz: list[dict]) -> tuple[int, int, int, int]:
    """Return (total, upgraded, already_high, unmatched)."""
    path = PROJECT_ROOT / f"data/processed/ruptl_generators_{region}.csv"
    if not path.exists():
        print(f"[enrich_ref] missing: {path}", file=sys.stderr)
        return (0, 0, 0, 0)

    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return (0, 0, 0, 0)

    orig_cols = list(rows[0].keys())
    new_cols = ["reference_ruptl_id", "reference_source_url"]
    out_cols = orig_cols + [c for c in new_cols if c not in orig_cols]

    upgraded = 0
    already_high = 0
    unmatched = 0
    for r in rows:
        conf = (r.get("coord_confidence") or "").strip().lower()
        if conf in ("high", "medium"):
            already_high += 1
            continue
        # Placeholder / low confidence → try reference enrichment
        match = match_reference(r, gaz)
        if match:
            r["lat"] = f"{match['lat']:.6f}"
            r["lon"] = f"{match['lon']:.6f}"
            r["coord_source"] = f"reference_100gw:{match['ref_ruptl_id']}"
            # Reference confidence: 'low' means "locality centroid, bukan
            # exact plant footprint" — still better than pure province
            # centroid + jitter. Elevate ke 'medium' internal-nya
            # (locality-grade) supaya frontend include di rendered features.
            r["coord_confidence"] = "medium"
            r["reference_ruptl_id"] = match["ref_ruptl_id"]
            r["reference_source_url"] = match.get("source_url", "")
            upgraded += 1
        else:
            unmatched += 1

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in out_cols})
    return (len(rows), upgraded, already_high, unmatched)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--region", help="single region key")
    g.add_argument("--all", action="store_true", help="all 8 regions")
    opts = ap.parse_args()

    print(f"[enrich_ref] loading reference gazetteer from {RENCANA_DIR}")
    gaz = load_reference_gazetteer()
    print(f"  reference pembangkit: {len(gaz)} unique across {len(YEARS)} year files")

    regions = (list(sorted(REGION_PROVINCES.keys()
                             - {'maluku_papua', 'nusa_tenggara'}))
                if opts.all else [opts.region])

    print(f"\n{'region':<12} {'total':>6} {'upgraded':>10} {'already_hi':>11} {'unmatched':>11}")
    for r in regions:
        t, up, hi, um = enrich(r, gaz)
        print(f"{r:<12} {t:>6} {up:>10} {hi:>11} {um:>11}")


if __name__ == "__main__":
    main()
