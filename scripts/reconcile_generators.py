#!/usr/bin/env python3
"""Reconcile IPM baseline generator dataset ↔ RUPTL Rincian pembangkit.

Input:
  --ipm       data/processed/generator_master_{region}.csv  (baseline OSM)
  --ruptl     data/processed/ruptl_generators_{region}.csv  (RUPTL row extract)
  --overrides data/overrides/generator_matches.csv          (manual decisions)

Output:
  --out       data/processed/generator_master_reconciled_{region}.csv
  --report    data/reconciliation/report_{region}_{ts}.md

Cascade (adapt dari `big_pembangkit_integrasi.py`, adjust ke konteks IPM):

    1. Filter min-mw pada RUPTL rows (default 1 MW)
    2. Aglomerasi unit → tapak (nama_stem + tipe + jarak ≤ gabung-km)
    3. Match ke IPM baseline:
       a. Coord ≤ 2 km + same type + capacity ±20%  → CONFIRMED_MATCH
       b. Nama-stem sama, jarak ≤ 15 km             → PROBABLE_MATCH
       c. Nama-stem sama, jarak 15–40 km + same type → PROBABLE_MATCH (flagged)
       d. Same type ≤ 15 km, no name overlap         → NEEDS_REVIEW (ambiguous)
       e. Same type ≤ 2 km, capacity conflict > 30%  → CONFLICT
    4. Sisa IPM tanpa RUPTL counterpart              → UNMATCHED_IPM
    5. Sisa RUPTL tanpa IPM match                    → UNMATCHED_RUPTL

Semua thresholds configurable via CLI. Override CSV di-apply LAST (win over
auto-decision). Dry-run default; `--write` untuk simpan hasil.

Prinsip:
  - Tidak overwrite silently: kolom kanonik SELALU punya `_source` companion,
    dan nilai original dari sumber lain disimpan di `capacity_mw_ipm`,
    `capacity_mw_ruptl`, dst.
  - Conflict flags (has_capacity_conflict, has_type_conflict, ...) dibiarkan
    True walau match dianggap CONFIRMED — reviewer bisa filter belakangan.
  - Override adalah source of truth: reconciliation deterministik dari raw + override.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

# Repo-relative imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import (  # noqa: E402
    plant_name_stem, plant_name_tokens, infer_plant_type,
    haversine_km, capacity_diff_pct, normalize,
)


# -----------------------------------------------------------------------
# Match classification tiers (nilai kolom `match_tier` di output CSV)
# -----------------------------------------------------------------------
TIER_CONFIRMED = "CONFIRMED_MATCH"       # coord + type + capacity semuanya cocok
TIER_PROBABLE = "PROBABLE_MATCH"          # nama sama + within tolerance
TIER_AMBIGUOUS = "AMBIGUOUS"              # multiple candidates match, need pick
TIER_UNMATCHED_IPM = "UNMATCHED_IPM"      # IPM row without RUPTL counterpart
TIER_UNMATCHED_RUPTL = "UNMATCHED_RUPTL"  # RUPTL row without IPM counterpart
TIER_CONFLICT = "CONFLICT"                # matched but attributes disagree strongly

# Score untuk sorting (higher = more confident). Bukan probability, cuma ordering.
TIER_SCORE = {
    TIER_CONFIRMED: 1.00,
    TIER_PROBABLE: 0.80,
    TIER_AMBIGUOUS: 0.50,
    TIER_CONFLICT: 0.40,
    TIER_UNMATCHED_IPM: 0.10,
    TIER_UNMATCHED_RUPTL: 0.10,
}


# -----------------------------------------------------------------------
# I/O helpers
# -----------------------------------------------------------------------
def read_csv_dict(path: Path) -> list[dict]:
    """Read CSV as list of dict, blank string for empty cells."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_dict(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})


def parse_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(str(v).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None


# -----------------------------------------------------------------------
# Domain: build lookup index
# -----------------------------------------------------------------------
def normalize_province(p: Optional[str]) -> str:
    """Fold RUPTL/IPM province spelling → canonical lowercase key.

    RUPTL kadang all-caps, kadang mixed. IPM konsisten mixed-case.
    Normalize supaya bisa dibandingkan.
    """
    if not p:
        return ""
    return normalize(p).replace("d k i ", "dki ").replace(
        "d i ", "di ").strip()


def build_ipm_index(ipm_rows: list[dict]) -> dict:
    """Index IPM baseline untuk fast lookup di cascade.

    Return:
      {
        "by_stem": {stem → [row, ...]},
        "by_prov": {province_key → [row, ...]},
        "rows": [row, ...]  # semua rows, retain original order untuk audit
      }
    """
    by_stem: dict[str, list[dict]] = defaultdict(list)
    by_prov: dict[str, list[dict]] = defaultdict(list)
    for r in ipm_rows:
        r["_stem"] = plant_name_stem(r.get("name"))
        r["_tokens"] = plant_name_tokens(r.get("name"))
        r["_prov_key"] = normalize_province(r.get("province"))
        r["_lon"] = parse_float(r.get("lon"))
        r["_lat"] = parse_float(r.get("lat"))
        r["_mw"] = parse_float(r.get("capacity_mw"))
        if r["_stem"]:
            by_stem[r["_stem"]].append(r)
        if r["_prov_key"]:
            by_prov[r["_prov_key"]].append(r)
    return {"by_stem": by_stem, "by_prov": by_prov, "rows": ipm_rows}


# -----------------------------------------------------------------------
# Cascade matching
# -----------------------------------------------------------------------
def find_match(ruptl_row: dict, index: dict, opts: argparse.Namespace) -> dict:
    """Cari best match IPM untuk satu RUPTL row. Return dict dengan keys:

      tier         — classification (CONFIRMED_MATCH / PROBABLE_MATCH / dst)
      ipm_row      — matched IPM row (or None)
      reason       — human-readable explanation
      candidates   — list of near-matches yang di-consider (untuk audit)
    """
    r_name = ruptl_row.get("name", "")
    r_stem = plant_name_stem(r_name)
    r_tokens = plant_name_tokens(r_name)
    r_type = ruptl_row.get("type") or infer_plant_type(r_name)
    r_prov = normalize_province(ruptl_row.get("province"))
    r_lon = parse_float(ruptl_row.get("lon") or ruptl_row.get("longitude"))
    r_lat = parse_float(ruptl_row.get("lat") or ruptl_row.get("latitude"))
    r_mw = parse_float(ruptl_row.get("capacity_mw"))
    # Gate: coord confidence dari geocode_ruptl_generators.py. Kalau
    # "low" (province centroid + jitter — bukan geolokasi real), jangan
    # trigger CONFIRMED palsu — treat as no coord.
    if (ruptl_row.get("coord_confidence") or "").strip().lower() == "low":
        r_lon = r_lat = None

    # Kandidat: batasi ke provinsi yang sama untuk hindari cross-province match.
    # Fallback: kalau RUPTL tidak punya provinsi, seluruh IPM rows.
    if r_prov:
        pool = index["by_prov"].get(r_prov, [])
    else:
        pool = index["rows"]

    # Skorkan tiap kandidat (jarak, name overlap, type match, capacity diff).
    scored = []
    for cand in pool:
        c_stem = cand.get("_stem", "")
        c_tokens = cand.get("_tokens", set())
        c_type = cand.get("type", "")
        c_lon, c_lat = cand.get("_lon"), cand.get("_lat")
        c_mw = cand.get("_mw")

        # Distance
        dist_km = None
        if r_lon is not None and r_lat is not None \
                and c_lon is not None and c_lat is not None:
            dist_km = haversine_km((r_lon, r_lat), (c_lon, c_lat))

        # Name match strength
        name_exact = bool(r_stem) and r_stem == c_stem
        name_token_equal = bool(r_tokens) and r_tokens == c_tokens
        name_token_overlap = bool(r_tokens & c_tokens) if r_tokens else False

        # Type match
        type_match = bool(r_type) and bool(c_type) and r_type == c_type

        # Capacity diff
        cap_diff = capacity_diff_pct(r_mw, c_mw)

        scored.append({
            "cand": cand,
            "dist_km": dist_km,
            "name_exact": name_exact,
            "name_token_equal": name_token_equal,
            "name_token_overlap": name_token_overlap,
            "type_match": type_match,
            "cap_diff": cap_diff,
        })

    # Cascade decision (mimic reference project's asymmetric-threshold cascade).
    # Order matters: cek yang paling kuat dulu.

    # Tier 1: CONFIRMED — coord ≤ radius + type match + capacity within tolerance
    for s in scored:
        if (s["dist_km"] is not None and s["dist_km"] <= opts.radius
                and s["type_match"]
                and (s["cap_diff"] is None or s["cap_diff"] <= opts.cap_tol)):
            cd = s["cap_diff"]
            cd_str = "n/a" if cd is None else f"{cd*100:.0f}%"
            return {
                "tier": TIER_CONFIRMED,
                "ipm_row": s["cand"],
                "reason": (f"coord {s['dist_km']:.1f} km ≤ {opts.radius}, "
                           f"type={r_type} matches, "
                           f"capacity diff {cd_str} ≤ {opts.cap_tol*100:.0f}%"),
                "candidates": scored,
            }

    # Tier 2a: PROBABLE — same name stem within name-radius
    for s in scored:
        if s["name_exact"] and s["dist_km"] is not None \
                and s["dist_km"] <= opts.radius_name:
            return {
                "tier": TIER_PROBABLE,
                "ipm_row": s["cand"],
                "reason": (f"nama-stem sama ('{r_stem}'), "
                           f"jarak {s['dist_km']:.1f} km"),
                "candidates": scored,
            }

    # Tier 2b: PROBABLE — token set equal
    for s in scored:
        if s["name_token_equal"] and (
                s["dist_km"] is None or s["dist_km"] <= opts.radius_name):
            d_str = "n/a" if s["dist_km"] is None else f"{s['dist_km']:.1f} km"
            return {
                "tier": TIER_PROBABLE,
                "ipm_row": s["cand"],
                "reason": f"token set sama, jarak={d_str}",
                "candidates": scored,
            }

    # Tier 3: AMBIGUOUS — same type nearby but no name overlap
    same_type_near = [
        s for s in scored
        if s["type_match"] and s["dist_km"] is not None
        and s["dist_km"] <= opts.radius_type
    ]
    if len(same_type_near) == 1 and r_mw is not None and r_mw >= opts.doubt_mw:
        # Big plant, no name match, only same-type nearby → NEEDS_REVIEW
        s = same_type_near[0]
        return {
            "tier": TIER_AMBIGUOUS,
            "ipm_row": s["cand"],
            "reason": (f"IPM {r_type} terdekat {s['dist_km']:.1f} km tapi nama "
                       f"berbeda; kapasitas ≥ {opts.doubt_mw:.0f} MW → butuh review"),
            "candidates": scored,
        }
    if len(same_type_near) > 1:
        return {
            "tier": TIER_AMBIGUOUS,
            "ipm_row": None,
            "reason": (f"{len(same_type_near)} kandidat IPM {r_type} "
                       f"dalam {opts.radius_type} km — butuh manual pick"),
            "candidates": scored,
        }

    # Fallthrough: no acceptable match
    return {
        "tier": TIER_UNMATCHED_RUPTL,
        "ipm_row": None,
        "reason": "tidak ada IPM row yang cocok dalam thresholds",
        "candidates": scored,
    }


# -----------------------------------------------------------------------
# Merge decision → reconciled row (canonical field + provenance)
# -----------------------------------------------------------------------
def merge_records(ipm_row: Optional[dict], ruptl_row: Optional[dict],
                  tier: str, reason: str, override: Optional[dict] = None,
                  score: Optional[float] = None) -> dict:
    """Compose reconciled row dengan canonical fields + provenance.

    Aturan:
      - Kalau ada override dengan decision='merge', ambil IPM + RUPTL keduanya.
      - Kalau tier CONFIRMED/PROBABLE dan IPM ada: IPM values dominan
        (baseline is master), RUPTL values disimpan sebagai *_ruptl companion.
      - Kalau UNMATCHED_RUPTL: use RUPTL values as canonical (candidate add).
      - Kalau UNMATCHED_IPM: use IPM values as canonical.
      - Every canonical field gets `_source` companion telling which source.
      - Override values (bila ada override.capacity_override dst.) WIN over auto.
    """
    ipm = ipm_row or {}
    rup = ruptl_row or {}
    ovr = override or {}

    def pick(field: str, ipm_field: Optional[str] = None,
             ruptl_field: Optional[str] = None,
             override_field: Optional[str] = None) -> tuple[str, str]:
        """Return (value, source_label) for one canonical column."""
        override_field = override_field or (field + "_override")
        ipm_field = ipm_field or field
        ruptl_field = ruptl_field or field
        # 1. explicit override wins
        ov = ovr.get(override_field, "")
        if ov not in ("", None):
            return str(ov), "override"
        # 2. IPM baseline preferred when present
        iv = ipm.get(ipm_field, "")
        if iv not in ("", None):
            return str(iv), "ipm_osm"
        # 3. RUPTL fallback
        rv = rup.get(ruptl_field, "")
        if rv not in ("", None):
            return str(rv), "ruptl"
        return "", ""

    name, name_source = pick("name")
    cap, cap_source = pick("capacity_mw")
    typ, typ_source = pick("type")
    role, role_source = pick("role")
    operator, operator_source = pick("operator")
    status, status_source = pick("status")
    method, _ = pick("method")

    # Coord: prefer IPM (osm) even for tier CONFIRMED — RUPTL row extractor
    # may have no coord at all. Kalau IPM null tapi RUPTL punya coord (rare),
    # ambil RUPTL.
    lat_ipm = parse_float(ipm.get("lat"))
    lon_ipm = parse_float(ipm.get("lon"))
    lat_rup = parse_float(rup.get("lat") or rup.get("latitude"))
    lon_rup = parse_float(rup.get("lon") or rup.get("longitude"))
    if lat_ipm is not None and lon_ipm is not None:
        lat, lon, coord_source = lat_ipm, lon_ipm, "ipm_osm"
    elif lat_rup is not None and lon_rup is not None:
        lat, lon, coord_source = lat_rup, lon_rup, "ruptl_geocoded"
    else:
        lat, lon, coord_source = "", "", "unassigned"

    province = ipm.get("province") or rup.get("province") or ""
    system = ipm.get("system") or rup.get("system") or ""

    # Conflict detection between IPM and RUPTL values
    def parse_cap(v):
        return parse_float(v)

    ipm_cap = parse_cap(ipm.get("capacity_mw"))
    rup_cap = parse_cap(rup.get("capacity_mw"))
    cap_conflict = ""
    if ipm_cap is not None and rup_cap is not None:
        diff = capacity_diff_pct(ipm_cap, rup_cap)
        cap_conflict = "true" if (diff is not None and diff > 0.30) else "false"

    type_conflict = ""
    if ipm.get("type") and rup.get("type"):
        type_conflict = ("true" if str(ipm["type"]).strip() != str(rup["type"]).strip()
                         else "false")

    role_conflict = ""
    if ipm.get("role") and rup.get("role"):
        role_conflict = ("true" if str(ipm["role"]).strip() != str(rup["role"]).strip()
                         else "false")

    loc_conflict = ""
    if (lat_ipm is not None and lon_ipm is not None
            and lat_rup is not None and lon_rup is not None):
        d = haversine_km((lon_ipm, lat_ipm), (lon_rup, lat_rup))
        loc_conflict = "true" if d > 5.0 else "false"

    return {
        # Identity
        "id": ipm.get("id") or ("RUPTL:" + str(rup.get("id") or "")),
        "ipm_id": ipm.get("id", ""),
        "ruptl_id": rup.get("id", ""),
        # Canonical fields
        "name": name,
        "type": typ,
        "capacity_mw": cap,
        "province": province,
        "system": system,
        "status": status,
        "role": role,
        "operator": operator,
        "method": method,
        "lat": lat, "lon": lon,
        # Reconciliation metadata
        "match_tier": tier,
        "match_score": f"{score:.2f}" if score is not None else f"{TIER_SCORE.get(tier, 0):.2f}",
        "match_reason": reason,
        # Provenance per field (which source contributed)
        "name_source": name_source,
        "capacity_mw_source": cap_source,
        "type_source": typ_source,
        "role_source": role_source,
        "operator_source": operator_source,
        "status_source": status_source,
        "coord_source": coord_source,
        # Original values for audit (never overwritten)
        "capacity_mw_ipm": ipm.get("capacity_mw", ""),
        "capacity_mw_ruptl": rup.get("capacity_mw", ""),
        "type_ipm": ipm.get("type", ""),
        "type_ruptl": rup.get("type", ""),
        "role_ipm": ipm.get("role", ""),
        "role_ruptl": rup.get("role", ""),
        # Conflict flags
        "has_capacity_conflict": cap_conflict,
        "has_type_conflict": type_conflict,
        "has_role_conflict": role_conflict,
        "has_location_conflict": loc_conflict,
        # Passthrough
        "osm_id": ipm.get("osm_id", ""),
        "osm_source": ipm.get("osm_source", ""),
        "source_id": ipm.get("source_id") or rup.get("source_id", ""),
        "review_flag": ipm.get("review_flag", ""),
    }


# -----------------------------------------------------------------------
# Override reader
# -----------------------------------------------------------------------
def load_overrides(path: Path) -> dict[tuple[str, str], dict]:
    """Load override CSV keyed by (ruptl_id, ipm_id).

    Kalau salah satu id kosong, key-nya masih tuple tapi dengan "" placeholder.
    Reader ini toleran ke schema evolution — kolom baru tidak break.
    """
    ov: dict[tuple[str, str], dict] = {}
    for r in read_csv_dict(path):
        key = (r.get("ruptl_id", "").strip(), r.get("ipm_id", "").strip())
        ov[key] = r
    return ov


# -----------------------------------------------------------------------
# Report writer
# -----------------------------------------------------------------------
def write_report(path: Path, region: str, results: list[dict],
                 opts: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[r["match_tier"]] += 1

    lines = [
        f"# Reconciliation report — {region}",
        "",
        f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        "## Thresholds",
        f"- min-mw = {opts.min_mw}",
        f"- radius (confirm) = {opts.radius} km",
        f"- radius-name = {opts.radius_name} km",
        f"- radius-type = {opts.radius_type} km",
        f"- cap-tol (confirm) = {opts.cap_tol*100:.0f}%",
        f"- doubt-mw = {opts.doubt_mw} MW",
        "",
        "## Tier counts",
    ]
    total = sum(counts.values())
    for tier in [TIER_CONFIRMED, TIER_PROBABLE, TIER_AMBIGUOUS, TIER_CONFLICT,
                 TIER_UNMATCHED_IPM, TIER_UNMATCHED_RUPTL]:
        n = counts.get(tier, 0)
        pct = (n / total * 100) if total else 0
        lines.append(f"- {tier}: {n} ({pct:.1f}%)")
    lines.append("")

    lines.append("## Cases needing manual review")
    review = [r for r in results if r["match_tier"] in
              (TIER_AMBIGUOUS, TIER_CONFLICT, TIER_UNMATCHED_RUPTL)]
    for r in sorted(review, key=lambda x: -parse_float(x.get("capacity_mw")) or 0)[:50]:
        cap = r.get("capacity_mw", "?")
        lines.append(
            f"- **{r['match_tier']}** · {cap} MW · {r.get('name', '(no name)')}"
            f" · {r.get('province', '')}"
        )
        lines.append(f"  - reason: {r.get('match_reason', '')}")
        if r.get("ipm_id"):
            lines.append(f"  - IPM id: `{r['ipm_id']}`")
        if r.get("ruptl_id"):
            lines.append(f"  - RUPTL id: `{r['ruptl_id']}`")
    lines.append("")
    lines.append("Untuk decide, edit `data/overrides/generator_matches.csv`.")
    lines.append("Format kolom: `override_id,decision,ipm_id,ruptl_id,"
                 "capacity_override,type_override,role_override,reason,"
                 "reviewed_by,reviewed_at`.")

    path.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------
OUTPUT_HEADERS = [
    "id", "ipm_id", "ruptl_id",
    "name", "type", "capacity_mw", "province", "system", "status",
    "role", "operator", "method", "lat", "lon",
    "match_tier", "match_score", "match_reason",
    "name_source", "capacity_mw_source", "type_source", "role_source",
    "operator_source", "status_source", "coord_source",
    "capacity_mw_ipm", "capacity_mw_ruptl",
    "type_ipm", "type_ruptl",
    "role_ipm", "role_ruptl",
    "has_capacity_conflict", "has_type_conflict",
    "has_role_conflict", "has_location_conflict",
    "osm_id", "osm_source", "source_id", "review_flag",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True,
                    help="region key (jamali/sumatra/kalimantan/…)")
    ap.add_argument("--ipm", type=Path, default=None,
                    help="IPM baseline CSV (default: data/processed/generator_master_{region}.csv)")
    ap.add_argument("--ruptl", type=Path, default=None,
                    help="RUPTL row CSV (default: data/processed/ruptl_generators_{region}.csv)")
    ap.add_argument("--overrides", type=Path,
                    default=Path("data/overrides/generator_matches.csv"))
    ap.add_argument("--out", type=Path, default=None,
                    help="Output CSV (default: data/processed/generator_master_reconciled_{region}.csv)")
    ap.add_argument("--report", type=Path, default=None,
                    help="Report markdown (default: data/reconciliation/report_{region}_{ts}.md)")
    ap.add_argument("--min-mw", type=float, default=1.0,
                    help="MW; RUPTL rows below this threshold di-skip")
    ap.add_argument("--radius", type=float, default=2.0,
                    help="km; radius untuk tier CONFIRMED match")
    ap.add_argument("--radius-name", type=float, default=15.0,
                    help="km; radius untuk same-name PROBABLE match")
    ap.add_argument("--radius-type", type=float, default=15.0,
                    help="km; radius untuk same-type AMBIGUOUS check")
    ap.add_argument("--cap-tol", type=float, default=0.20,
                    help="fraction; capacity tolerance untuk CONFIRMED tier")
    ap.add_argument("--doubt-mw", type=float, default=100.0,
                    help="MW; large plants tanpa IPM match jadi AMBIGUOUS flag")
    ap.add_argument("--write", action="store_true",
                    help="tanpa ini: dry-run (print summary only, no CSV/report file)")
    opts = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]

    def rel(p: Optional[Path], default_name: str) -> Path:
        if p is None:
            return project_root / "data/processed" / default_name
        if p.is_absolute():
            return p
        return project_root / p

    ipm_path = rel(opts.ipm, f"generator_master_{opts.region}.csv")
    ruptl_path = rel(opts.ruptl, f"ruptl_generators_{opts.region}.csv")
    out_path = rel(opts.out, f"generator_master_reconciled_{opts.region}.csv")
    ovr_path = (opts.overrides if opts.overrides.is_absolute()
                else project_root / opts.overrides)

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    report_path = (opts.report if opts.report else
                   project_root / f"data/reconciliation/report_{opts.region}_{ts}.md")

    print(f"[reconcile] region={opts.region}")
    print(f"  IPM baseline: {ipm_path}")
    print(f"  RUPTL rows:   {ruptl_path}")
    print(f"  Overrides:    {ovr_path}")

    ipm_rows = read_csv_dict(ipm_path)
    ruptl_rows = read_csv_dict(ruptl_path)
    overrides = load_overrides(ovr_path)

    print(f"  → {len(ipm_rows)} IPM rows, {len(ruptl_rows)} RUPTL rows, "
          f"{len(overrides)} overrides")

    if not ipm_rows:
        print("  ! IPM baseline empty — nothing to reconcile against.")
        return 1

    # Step 1: filter RUPTL by min-mw
    filtered = []
    for r in ruptl_rows:
        mw = parse_float(r.get("capacity_mw"))
        if mw is None or mw < opts.min_mw:
            continue
        filtered.append(r)
    if len(filtered) != len(ruptl_rows):
        print(f"  filtered {len(ruptl_rows) - len(filtered)} RUPTL rows "
              f"below {opts.min_mw} MW")

    # Step 2: build index
    index = build_ipm_index(ipm_rows)

    # Step 3: match each RUPTL row
    results = []
    matched_ipm_ids: set[str] = set()

    for rup in filtered:
        m = find_match(rup, index, opts)
        tier = m["tier"]
        ipm_match = m["ipm_row"]

        # Apply override — coba key permutations:
        #   1. (ruptl_id, matched_ipm_id) — exact auto+manual pair
        #   2. (ruptl_id, "") — RUPTL row without expected IPM peer
        #   3. any override with same ruptl_id → force-merge target dari CSV
        rup_id = rup.get("id", "")
        auto_ipm_id = (ipm_match or {}).get("id", "")
        override = (overrides.get((rup_id, auto_ipm_id))
                    or overrides.get((rup_id, ""))
                    or next((o for k, o in overrides.items() if k[0] == rup_id), None))
        if override:
            decision = override.get("decision", "").strip().lower()
            if decision == "merge" and not ipm_match:
                # Manual force-merge: look up IPM by id
                target_ipm_id = override.get("ipm_id", "").strip()
                for r in ipm_rows:
                    if r.get("id") == target_ipm_id:
                        ipm_match = r
                        tier = TIER_CONFIRMED
                        m["reason"] = "manual override: merge"
                        break
            elif decision == "keep_separate":
                tier = TIER_UNMATCHED_RUPTL
                ipm_match = None
                m["reason"] = "manual override: keep separate"
            elif decision == "drop_ruptl":
                # Skip this RUPTL row entirely
                continue

        merged = merge_records(ipm_match, rup, tier, m["reason"], override)
        results.append(merged)
        if ipm_match:
            matched_ipm_ids.add(ipm_match.get("id", ""))

    # Step 4: emit UNMATCHED_IPM for IPM rows not touched by any RUPTL match
    for r in ipm_rows:
        if r.get("id") in matched_ipm_ids:
            continue
        merged = merge_records(r, None, TIER_UNMATCHED_IPM,
                                "tidak ada RUPTL row yang cocok")
        results.append(merged)

    # Print summary
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[r["match_tier"]] += 1
    print("\n== Tier summary ==")
    for tier in [TIER_CONFIRMED, TIER_PROBABLE, TIER_AMBIGUOUS, TIER_CONFLICT,
                 TIER_UNMATCHED_IPM, TIER_UNMATCHED_RUPTL]:
        print(f"  {tier:25} {counts.get(tier, 0):5}")
    print(f"  {'TOTAL':25} {len(results):5}")

    if not opts.write:
        print("\n(dry-run — pass --write untuk simpan output)")
        return 0

    write_csv_dict(out_path, results, OUTPUT_HEADERS)
    write_report(report_path, opts.region, results, opts)
    print(f"\n  wrote {out_path}")
    print(f"  wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
