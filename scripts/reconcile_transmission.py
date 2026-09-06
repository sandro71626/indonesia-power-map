#!/usr/bin/env python3
"""Reconcile RUPTL transmission rows vs baseline (enriched dengan endpoint).

Prerequisite: baseline `transmission_{region}.geojson` sudah di-enrich
oleh `enrich_transmission_endpoints.py` — punya property `from_id`,
`to_id`, `endpoint_confidence`.

Matching logic:
  1. Untuk tiap RUPTL row: cari substation match untuk `from_bus` &
     `to_bus` via name tokens (reuse pattern dari phase 1 renderer).
  2. Lookup baseline line dengan endpoint pair yang cocok (order-insensitive:
     RUPTL A→B match baseline dari_id=A,to_id=B ATAU dari_id=B,to_id=A).
  3. Klasifikasi:
       CONFIRMED_MATCH   — pair match + voltage match + length within 30%
       PROBABLE_MATCH    — pair match, voltage OR length off
       UPRATE_TARGET     — action=Uprate + pair match → baseline butuh upgrade
       UNMATCHED_RUPTL   — no baseline pair — kandidat planned line baru
       UNMATCHED_BASELINE — baseline segment yang endpoint tidak muncul di RUPTL

Output:
  data/processed/transmission_{region}.reconciled.geojson — baseline
  features + tier + audit + planned RUPTL features (dari renderer phase 1)
  data/reconciliation/transmission_delta_{region}_{ts}.md — audit report

Usage:
    # Prereq: sudah run enrich_transmission_endpoints + extract_ruptl_transmission
    python3 scripts/reconcile_transmission.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import plant_name_tokens  # noqa: E402

# Reuse bus lookup dari phase 1 renderer
from render_ruptl_transmission_geojson import (  # noqa: E402
    BUS_STOPWORDS, bus_tokens, load_substation_gazetteer, lookup_bus,
)

# Canonical status/action normalization (mirror pattern dari merge_reconciled)
STATUS_NORM_MAP = {
    "planned": "PLANNED", "rencana": "PLANNED",
    "construction": "CONSTRUCTION", "konstruksi": "CONSTRUCTION",
    "kontruksi": "CONSTRUCTION",  # typo umum di RUPTL PDF
    "procurement": "PROCUREMENT", "pengadaan": "PROCUREMENT",
    "committed": "COMMITTED", "ppa": "COMMITTED",
    "proposed": "PROPOSED", "eksplorasi": "PROPOSED",
}
ACTION_NORM_MAP = {
    "new": "NEW", "baru": "NEW",
    "extension": "EXTENSION", "ext": "EXTENSION",
    "uprate": "UPRATE", "uprating": "UPRATE", "upr": "UPRATE",
}


def norm_status(s: str) -> str:
    if not s:
        return ""
    key = str(s).strip().lower()
    return STATUS_NORM_MAP.get(key, key.upper())


def norm_action(s: str) -> str:
    if not s:
        return ""
    key = str(s).strip().lower()
    return ACTION_NORM_MAP.get(key, "")


# ------------------------------------------------------------
# Tiers
# ------------------------------------------------------------
TIER_CONFIRMED = "CONFIRMED_MATCH"
TIER_PROBABLE = "PROBABLE_MATCH"
TIER_UPRATE = "UPRATE_TARGET"
TIER_UNMATCHED_RUPTL = "UNMATCHED_RUPTL"
TIER_UNMATCHED_BASELINE = "UNMATCHED_BASELINE"
TIER_BASELINE_UNRESOLVED = "BASELINE_UNRESOLVED"  # baseline tanpa endpoint

TIER_ORDER = [
    TIER_CONFIRMED, TIER_PROBABLE, TIER_UPRATE,
    TIER_UNMATCHED_RUPTL, TIER_UNMATCHED_BASELINE, TIER_BASELINE_UNRESOLVED,
]


# ------------------------------------------------------------
# Baseline endpoint index
# ------------------------------------------------------------
def build_baseline_index(features: list[dict]) -> dict[frozenset, list[dict]]:
    """Index baseline features by {from_id, to_id} pair (order-insensitive).

    Return {frozenset({from_id, to_id}): [features]}.
    Features tanpa endpoint kedua tidak dimasukkan.
    """
    idx: dict[frozenset, list[dict]] = {}
    for f in features:
        props = f.get("properties") or {}
        fi = (props.get("from_id") or "").strip()
        ti = (props.get("to_id") or "").strip()
        if not fi or not ti:
            continue
        key = frozenset({fi, ti})
        idx.setdefault(key, []).append(f)
    return idx


# ------------------------------------------------------------
# Value parsers
# ------------------------------------------------------------
def parse_float(v) -> Optional[float]:
    try:
        s = str(v or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


def voltage_match(rup_kv: str, base_kv: str) -> Optional[bool]:
    """Return True/False kalau voltage bisa dibandingkan, None kalau salah
    satu kosong. Extract angka pertama untuk comparison."""
    if not rup_kv or not base_kv:
        return None
    import re
    ra = re.search(r"\d+", str(rup_kv))
    ba = re.search(r"\d+", str(base_kv))
    if not ra or not ba:
        return None
    return int(ra.group()) == int(ba.group())


def length_within(rup_len: Optional[float], base_len: Optional[float],
                   tol: float = 0.30) -> Optional[bool]:
    if rup_len is None or base_len is None:
        return None
    if rup_len <= 0 or base_len <= 0:
        return None
    diff = abs(rup_len - base_len) / max(rup_len, base_len)
    return diff <= tol


# ------------------------------------------------------------
# Reconcile
# ------------------------------------------------------------
def reconcile(region: str, project_root: Path,
               len_tol: float, write: bool) -> int:
    processed = project_root / "data/processed"
    base_gj_path = processed / f"transmission_{region}.geojson"
    ruptl_csv_path = processed / f"ruptl_transmission_{region}.csv"
    sub_csv_path = processed / f"substation_master_{region}.csv"
    out_path = processed / f"transmission_{region}.reconciled.geojson"

    for p in (base_gj_path, ruptl_csv_path, sub_csv_path):
        if not p.exists():
            print(f"[reconcile_trm] missing: {p}", file=sys.stderr)
            return 2

    print(f"[reconcile_trm] region={region}, len_tol={len_tol:.0%}")

    baseline = json.loads(base_gj_path.read_text(encoding="utf-8"))
    features = baseline.get("features", [])
    print(f"  baseline LineStrings: {len(features)}")

    gazetteer = load_substation_gazetteer(sub_csv_path)
    print(f"  substation gazetteer: {len(gazetteer)} pins")

    with ruptl_csv_path.open(encoding="utf-8-sig") as f:
        ruptl_rows = list(csv.DictReader(f))
    print(f"  RUPTL rows: {len(ruptl_rows)}")

    baseline_index = build_baseline_index(features)
    print(f"  baseline endpoint pairs (unique): {len(baseline_index)}")

    # Track baseline features that matched
    matched_baseline_ids: set[str] = set()

    # Process RUPTL rows
    ruptl_results = []  # list of {rup, tier, base_match, reason}
    tier_counts: Counter = Counter()

    for r in ruptl_rows:
        prov = r.get("province", "")
        from_pin = lookup_bus(r.get("from_bus", ""), prov, gazetteer)
        to_pin = lookup_bus(r.get("to_bus", ""), prov, gazetteer)
        action = (r.get("action_type") or "").strip()
        rup_kv = r.get("voltage_kv", "")
        rup_len = parse_float(r.get("length_km"))

        base_match = None
        tier = TIER_UNMATCHED_RUPTL
        reason = "endpoint pair tidak resolvable atau tidak ada baseline yang match"

        if from_pin and to_pin:
            key = frozenset({from_pin["id"], to_pin["id"]})
            candidates = baseline_index.get(key, [])
            if candidates:
                # Pilih baseline candidate berdasarkan voltage+length terbaik
                best = None
                best_score = -1
                for c in candidates:
                    cp = c.get("properties", {})
                    v_ok = voltage_match(rup_kv, cp.get("voltage_class") or
                                          str(cp.get("voltage_kv_max") or ""))
                    base_len = parse_float(cp.get("length_km"))
                    l_ok = length_within(rup_len, base_len, len_tol)
                    score = (1 if v_ok else 0) + (1 if l_ok else 0)
                    if score > best_score:
                        best_score = score
                        best = c
                base_match = best
                cp = best.get("properties", {})
                v_ok = voltage_match(rup_kv, cp.get("voltage_class") or
                                      str(cp.get("voltage_kv_max") or ""))
                base_len = parse_float(cp.get("length_km"))
                l_ok = length_within(rup_len, base_len, len_tol)

                # Note: base_len adalah panjang SEGMENT OSM (bisa 1-5km),
                # bukan panjang line utuh. RUPTL len adalah total line.
                # Length comparison bikin salah — kita fokus pada voltage
                # match + endpoint pair sebagai criteria CONFIRMED.
                if action == "Uprate":
                    tier = TIER_UPRATE
                    reason = (f"endpoint pair match ({from_pin['name']} — "
                              f"{to_pin['name']}), action=Uprate")
                elif v_ok is True:
                    tier = TIER_CONFIRMED
                    reason = (f"pair match ({from_pin['name']} — "
                              f"{to_pin['name']}), voltage={rup_kv} matches")
                elif v_ok is False:
                    tier = TIER_PROBABLE
                    reason = (f"pair match, voltage RUPTL={rup_kv} vs "
                              f"baseline={cp.get('voltage_class')}")
                else:
                    tier = TIER_PROBABLE
                    reason = f"pair match, voltage undeterminable (RUPTL={rup_kv or 'empty'})"

                matched_baseline_ids.add(id(best))

        ruptl_results.append({
            "rup": r, "tier": tier, "base_match": base_match,
            "reason": reason,
            "from_pin": from_pin, "to_pin": to_pin,
        })
        tier_counts[tier] += 1

    # Now classify baseline features
    baseline_tier_counts: Counter = Counter()
    for f in features:
        props = f.setdefault("properties", {})
        # Init canonical temporal + enum fields (kosong kalau tidak ada RUPTL).
        props.setdefault("target_cod_year_ruptl", "")
        props.setdefault("action_type_ruptl", "")
        props.setdefault("action_norm", "")
        props.setdefault("status_norm", "OPERATIONAL")
        endpoint_conf = props.get("endpoint_confidence", "none")
        if endpoint_conf != "both":
            props["match_tier"] = TIER_BASELINE_UNRESOLVED
            baseline_tier_counts[TIER_BASELINE_UNRESOLVED] += 1
        elif id(f) in matched_baseline_ids:
            # tier already set later per matching RUPTL row
            props["match_tier"] = TIER_CONFIRMED  # placeholder, updated below
        else:
            props["match_tier"] = TIER_UNMATCHED_BASELINE
            baseline_tier_counts[TIER_UNMATCHED_BASELINE] += 1

    # Enrich matched baseline with RUPTL info (use highest-tier RUPTL match)
    baseline_meta: dict[int, dict] = {}  # id(feature) → best result
    for res in ruptl_results:
        b = res["base_match"]
        if b is None:
            continue
        cur = baseline_meta.get(id(b))
        tier_rank = {TIER_CONFIRMED: 3, TIER_UPRATE: 2, TIER_PROBABLE: 1}
        if cur is None or tier_rank.get(res["tier"], 0) > tier_rank.get(cur["tier"], 0):
            baseline_meta[id(b)] = res

    for f in features:
        res = baseline_meta.get(id(f))
        if not res:
            continue
        r = res["rup"]
        props = f["properties"]
        props["match_tier"] = res["tier"]
        props["match_reason"] = res["reason"]
        props["ruptl_id"] = r.get("id", "")
        props["voltage_kv_ruptl"] = r.get("voltage_kv", "")
        props["length_km_ruptl"] = r.get("length_km", "")
        props["target_cod_year_ruptl"] = r.get("target_cod_year", "")
        props["action_type_ruptl"] = r.get("action_type", "")
        props["status_ruptl"] = r.get("status", "")
        props["action_norm"] = norm_action(r.get("action_type", ""))
        # Untuk baseline yang tag CONFIRMED/PROBABLE (line existing yang
        # muncul di RUPTL rencana): status baseline = OPERATIONAL, RUPTL
        # merefleksikan planned work (uprate/ext). status_norm tetap
        # OPERATIONAL karena baseline udah ada.
        props["status_norm"] = "OPERATIONAL"
        baseline_tier_counts[res["tier"]] += 1

    # Print tier summaries
    print("\n== RUPTL row classification ==")
    for t in TIER_ORDER:
        n = tier_counts.get(t, 0)
        if n:
            print(f"  {t:<25} {n:>5}")
    print(f"  {'TOTAL':<25} {sum(tier_counts.values()):>5}")

    print("\n== Baseline feature classification ==")
    for t in TIER_ORDER:
        n = baseline_tier_counts.get(t, 0)
        if n:
            print(f"  {t:<25} {n:>5}")
    print(f"  {'TOTAL':<25} {sum(baseline_tier_counts.values()):>5}")

    if not write:
        print("\n(dry-run — pass --write to update .reconciled.geojson + report)")
        return 0

    # Append PLANNED_RUPTL features (RUPTL rows with UNMATCHED_RUPTL + endpoints resolvable).
    # Skip rows dengan endpoint generic (Inc./Tx./Tersebar/Eksisting/Kuota) —
    # itu bukan real substation, gazetteer match jadi salah dan garis
    # digambar random. Tetap ada di CSV untuk manual review.
    import re as _re
    GENERIC_ENDPOINT_TOKENS_LOCAL = frozenset({
        "inc", "tx", "kuota", "tersebar", "eksisting", "eksisiting",
        "existing", "tap",
    })

    def _is_generic(name: str) -> bool:
        if not name:
            return True
        n = name.lower()
        return any(_re.search(rf"\b{tok}\b", n)
                   for tok in GENERIC_ENDPOINT_TOKENS_LOCAL)

    added_planned = 0
    skipped_generic = 0
    for res in ruptl_results:
        if res["tier"] != TIER_UNMATCHED_RUPTL:
            continue
        fp = res["from_pin"]
        tp = res["to_pin"]
        if not fp or not tp:
            continue
        r = res["rup"]
        if _is_generic(r.get("from_bus", "")) or _is_generic(r.get("to_bus", "")):
            skipped_generic += 1
            continue
        coords = [[fp["lon"], fp["lat"]], [tp["lon"], tp["lat"]]]
        planned_feat = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "id": "RUPTL:" + r.get("id", ""),
                "ruptl_id": r.get("id", ""),
                "name": r.get("name", ""),
                "from_bus": r.get("from_bus", ""),
                "to_bus": r.get("to_bus", ""),
                "from_id": fp["id"],
                "to_id": tp["id"],
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
                # Canonical enum (uppercase) untuk year/status filter
                "action_norm": norm_action(r.get("action_type", "")),
                "status_norm": norm_status(r.get("status", "")),
                # target_cod_year_ruptl kosong (PLANNED punya target_cod_year langsung)
                "target_cod_year_ruptl": "",
            },
        }
        features.append(planned_feat)
        added_planned += 1

    print(f"\n  added {added_planned} PLANNED_RUPTL features (new lines)")
    if skipped_generic:
        print(f"  skipped {skipped_generic} rows dengan endpoint generic "
              f"(Inc./Tx./Kuota/Tersebar) — tersedia di CSV untuk review")

    baseline["features"] = features
    out_path.write_text(json.dumps(baseline, ensure_ascii=False),
                        encoding="utf-8")
    print(f"  wrote {out_path} ({out_path.stat().st_size} bytes, "
          f"{len(features)} features)")

    # Report
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rep_path = (project_root
                / f"data/reconciliation/transmission_delta_{region}_{ts}.md")
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(rep_path, region, ruptl_results, baseline_tier_counts,
                  len(features), added_planned)
    print(f"  wrote {rep_path}")
    return 0


def write_report(path: Path, region: str, ruptl_results: list[dict],
                  baseline_counts: Counter, total_features: int,
                  added_planned: int) -> None:
    lines = []
    lines.append(f"# Transmission Reconciliation Report — {region}")
    lines.append("")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- Total features (reconciled GeoJSON): {total_features}")
    lines.append(f"- New PLANNED_RUPTL lines added: {added_planned}")
    lines.append("")
    lines.append("## Baseline classification")
    lines.append("")
    for t in TIER_ORDER:
        n = baseline_counts.get(t, 0)
        if n:
            lines.append(f"- **{t}**: {n}")
    lines.append("")
    lines.append("## Sample matches")
    lines.append("")
    by_tier: dict[str, list[dict]] = {}
    for res in ruptl_results:
        by_tier.setdefault(res["tier"], []).append(res)
    for t in [TIER_CONFIRMED, TIER_UPRATE, TIER_PROBABLE]:
        items = by_tier.get(t, [])
        if not items:
            continue
        lines.append(f"### {t} ({len(items)})")
        lines.append("")
        for res in items[:20]:
            r = res["rup"]
            fp = res["from_pin"] or {}
            tp = res["to_pin"] or {}
            lines.append(f"- {r['from_bus']} → {r['to_bus']} "
                          f"({r['voltage_kv']} kV, {r['length_km']} km, COD {r['target_cod_year']}) "
                          f"— {r['action_type']}. "
                          f"Match: {fp.get('id', '?')} ↔ {tp.get('id', '?')}. "
                          f"_{res['reason']}_")
        if len(items) > 20:
            lines.append(f"- _(+{len(items) - 20} more)_")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    ap.add_argument("--len-tol", type=float, default=0.30,
                    help="Toleransi length relatif (default 0.30 = 30%)")
    ap.add_argument("--write", action="store_true",
                    help="Write .reconciled.geojson + report (default dry-run)")
    opts = ap.parse_args()
    return reconcile(opts.region, Path(__file__).resolve().parents[1],
                      opts.len_tol, opts.write)


if __name__ == "__main__":
    raise SystemExit(main())
