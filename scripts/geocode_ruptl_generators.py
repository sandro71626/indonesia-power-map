#!/usr/bin/env python3
"""Enrich RUPTL Rincian pembangkit rows dengan lat/lon.

Strategy multi-tier dengan confidence tracking, TANPA panggilan API
eksternal (deterministik, reproducible):

  1. **gazetteer_generator** — token match ke `generator_master_{region}.csv`
     dalam provinsi yang sama. Confidence tinggi (both are pembangkit).
  2. **gazetteer_substation** — token match ke `substation_master_{region}.csv`
     dalam provinsi yang sama. Confidence medium (subs biasa dekat pembangkit
     tapi tidak identik).
  3. **province_centroid** — fallback ke centroid provinsi + jitter deterministik.
     Confidence low. Rows ini tidak akan trigger CONFIRMED di reconciler
     (jarak ke IPM real bakal >5km hampir selalu).

Output: overwrite `data/processed/ruptl_generators_{region}.csv` dengan
tambahan kolom `lat, lon, coord_source, coord_confidence`.

Usage:
    python3 scripts/geocode_ruptl_generators.py --region jamali

Design constraints:
- Idempotent: jalan berulang menghasilkan output identik.
- Tidak overwrite hasil manual (kalau `lat`/`lon` sudah non-empty dari
  edit manual, skip).
- No API calls, no network dependencies.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import plant_name_tokens  # noqa: E402


# ------------------------------------------------------------
# Province centroids (WGS84 lon/lat).
# Sumber: Wikipedia / BIG portal, dibulatkan ke 4 desimal.
# ------------------------------------------------------------
PROVINCE_CENTROID: dict[str, tuple[float, float]] = {
    # Jamali
    "dki jakarta":                 (106.8451, -6.2088),
    "banten":                      (106.1500, -6.4058),
    "jawa barat":                  (107.6191, -6.9147),
    "jawa tengah":                 (110.4203, -7.1509),
    "daerah istimewa yogyakarta":  (110.4494, -7.7956),
    "jawa timur":                  (112.7500, -7.5361),
    "bali":                        (115.1889, -8.4095),
    # Sumatera
    "aceh":                        (96.7494, 4.6951),
    "sumatera utara":              (98.7085, 2.1154),
    "sumatera barat":              (100.8000, -0.7893),
    "riau":                        (101.7068, 0.2933),
    "kepulauan riau":              (108.1428, 3.9457),
    "kepulauan bangka belitung":   (106.4406, -2.7411),
    "sumatera selatan":            (103.9137, -3.3194),
    "jambi":                       (103.6131, -1.6101),
    "bengkulu":                    (102.2655, -3.7928),
    "lampung":                     (105.4068, -4.5586),
    # Kalimantan
    "kalimantan barat":            (111.4753, -0.2787),
    "kalimantan tengah":           (113.3823, -1.6815),
    "kalimantan selatan":          (115.2838, -3.0926),
    "kalimantan timur":            (116.4194, 0.5387),
    "kalimantan utara":            (116.7091, 3.0731),
    # Sulawesi
    "sulawesi utara":              (124.8420, 0.6247),
    "sulawesi tengah":             (120.6522, -1.4300),
    "sulawesi selatan":            (119.9740, -3.6688),
    "sulawesi tenggara":           (121.9573, -4.1451),
    "gorontalo":                   (122.4467, 0.6999),
    "sulawesi barat":              (119.2321, -2.8441),
    # Maluku/Papua
    "maluku":                      (129.4526, -3.2385),
    "maluku utara":                (127.8087, 1.5709),
    "papua":                       (138.0804, -4.2699),
    "papua barat":                 (132.3009, -1.3361),
    "papua tengah":                (136.4318, -3.8949),
    "papua selatan":               (139.8000, -7.0000),
    "papua barat daya":            (131.2500, -1.0000),
    "papua pegunungan":            (138.9500, -4.1000),
    # Nusa Tenggara
    "nusa tenggara barat":         (117.3616, -8.6529),
    "nusa tenggara timur":         (121.0794, -8.6574),
}


# ------------------------------------------------------------
# Deterministic jitter untuk province-centroid rows
# ------------------------------------------------------------
def deterministic_jitter(seed_str: str, radius_km: float = 25.0
                          ) -> tuple[float, float]:
    """Return (dlon, dlat) jitter berbasis hash string, radius km.

    Deterministik: same seed → same offset. Tujuan: rows berbeda dengan
    province centroid yang sama tidak tumpuk satu titik di map.
    """
    h = hashlib.md5(seed_str.encode()).digest()
    # 2 signed bytes untuk lat, 2 untuk lon → range [-1, 1)
    dx = ((h[0] << 8) | h[1]) / 32768.0 - 1.0
    dy = ((h[2] << 8) | h[3]) / 32768.0 - 1.0
    # Convert km ke degree: 1 deg lat ≈ 111 km, 1 deg lon ≈ 111 * cos(lat)
    # Simplification: pakai 111 km/deg konstant (Indonesia dekat equator).
    dlat = dy * radius_km / 111.0
    dlon = dx * radius_km / 111.0
    return dlon, dlat


# ------------------------------------------------------------
# Gazetteer loading
# ------------------------------------------------------------
def load_gazetteer(csv_path: Path, name_field: str, prov_field: str,
                    id_field: str) -> list[dict]:
    """Load pin list dari IPM baseline CSV.

    Return list of {tokens: set, lat: float, lon: float, prov: str, id: str,
    name: str}. Skip rows tanpa coord.
    """
    out = []
    if not csv_path.exists():
        return out
    with csv_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r.get("lat") or "")
                lon = float(r.get("lon") or "")
            except ValueError:
                continue
            name = (r.get(name_field) or "").strip()
            if not name:
                continue
            out.append({
                "tokens": plant_name_tokens(name),
                "lat": lat, "lon": lon,
                "prov": (r.get(prov_field) or "").strip().lower(),
                "id": (r.get(id_field) or "").strip(),
                "name": name,
            })
    return out


def match_gazetteer(row_tokens: set[str], row_prov: str,
                     gazetteer: list[dict]) -> Optional[dict]:
    """Cari pin dengan token overlap terbesar dalam provinsi yang sama.

    Threshold: minimal 1 token match. Skor: |intersection| / |row_tokens|.
    Pin dengan skor >= 0.5 dianggap match (mayoritas token RUPTL cocok).
    """
    if not row_tokens:
        return None
    prov_norm = row_prov.lower()
    best = None
    best_score = 0.0
    for pin in gazetteer:
        if pin["prov"] != prov_norm:
            continue
        common = row_tokens & pin["tokens"]
        if not common:
            continue
        score = len(common) / max(len(row_tokens), 1)
        if score > best_score:
            best_score = score
            best = pin
    if best and best_score >= 0.5:
        return best
    return None


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
NEW_COLS = ["lat", "lon", "coord_source", "coord_confidence"]


def enrich(region: str, project_root: Path) -> int:
    ruptl_path = project_root / f"data/processed/ruptl_generators_{region}.csv"
    gen_path = project_root / f"data/processed/generator_master_{region}.csv"
    sub_path = project_root / f"data/processed/substation_master_{region}.csv"

    if not ruptl_path.exists():
        print(f"[geocode] missing input: {ruptl_path}", file=sys.stderr)
        return 2

    print(f"[geocode] region={region}")
    print(f"  RUPTL: {ruptl_path.name}")

    # Load gazetteers
    gen_gaz = load_gazetteer(gen_path, "name", "province", "id")
    sub_gaz = load_gazetteer(sub_path, "name", "province", "id")
    print(f"  gazetteer: {len(gen_gaz)} generators, {len(sub_gaz)} substations")

    with ruptl_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("  (empty input)")
        return 1

    # Determine output columns (preserve existing + append new if missing)
    orig_cols = list(rows[0].keys())
    out_cols = list(orig_cols)
    for c in NEW_COLS:
        if c not in out_cols:
            out_cols.append(c)

    stats = {"gen": 0, "sub": 0, "centroid": 0, "existing": 0, "unknown": 0}

    for r in rows:
        # Skip kalau sudah ada coord manual (idempotent)
        existing_lat = (r.get("lat") or "").strip()
        existing_lon = (r.get("lon") or "").strip()
        if existing_lat and existing_lon:
            r.setdefault("coord_source", "manual")
            r.setdefault("coord_confidence", "high")
            stats["existing"] += 1
            continue

        name = r.get("name", "")
        prov = r.get("province", "")
        tokens = plant_name_tokens(name)

        # Tier 1: match ke generator gazetteer
        hit = match_gazetteer(tokens, prov, gen_gaz)
        if hit:
            r["lat"] = f"{hit['lat']:.6f}"
            r["lon"] = f"{hit['lon']:.6f}"
            r["coord_source"] = f"gazetteer_generator:{hit['id']}"
            r["coord_confidence"] = "high"
            stats["gen"] += 1
            continue

        # Tier 2: match ke substation gazetteer
        hit = match_gazetteer(tokens, prov, sub_gaz)
        if hit:
            r["lat"] = f"{hit['lat']:.6f}"
            r["lon"] = f"{hit['lon']:.6f}"
            r["coord_source"] = f"gazetteer_substation:{hit['id']}"
            r["coord_confidence"] = "medium"
            stats["sub"] += 1
            continue

        # Tier 3: province centroid + jitter
        centroid = PROVINCE_CENTROID.get(prov.lower())
        if centroid:
            dlon, dlat = deterministic_jitter(r.get("id", "") or name)
            r["lat"] = f"{centroid[1] + dlat:.6f}"
            r["lon"] = f"{centroid[0] + dlon:.6f}"
            r["coord_source"] = "province_centroid"
            r["coord_confidence"] = "low"
            stats["centroid"] += 1
        else:
            r["lat"] = ""
            r["lon"] = ""
            r["coord_source"] = "unknown"
            r["coord_confidence"] = "none"
            stats["unknown"] += 1

    # Write back
    with ruptl_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in out_cols})

    print(f"\n  {stats['gen']:>4} matched via generator gazetteer (high conf)")
    print(f"  {stats['sub']:>4} matched via substation gazetteer (medium conf)")
    print(f"  {stats['centroid']:>4} fallback province centroid (low conf)")
    print(f"  {stats['existing']:>4} already had coord (skipped)")
    print(f"  {stats['unknown']:>4} unknown province (no coord)")
    print(f"\n  updated {ruptl_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True,
                    help="region key (jamali/sumatra/kalimantan/…)")
    opts = ap.parse_args()
    return enrich(opts.region, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
