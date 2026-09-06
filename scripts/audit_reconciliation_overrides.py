#!/usr/bin/env python3
"""Cross-type audit untuk override reconciliation.

Baca 3 override CSV (generator/substation/transmission), validate, cek
stale, dan report:
  - jumlah override valid/invalid per type
  - decision distribution
  - stale (baseline_id / ruptl_id tidak ditemukan)
  - unresolved suspicious cases (dari existing reconciliation report)

Skrip ini TIDAK menjalankan reconciler — cuma inspect override state.
Untuk verifikasi realized applied count, lihat reconciliation report
individual per region (yang di-append audit section otomatis).

Usage:
    python3 scripts/audit_reconciliation_overrides.py
    python3 scripts/audit_reconciliation_overrides.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared import overrides as ovr  # noqa: E402


REGIONS = ['jamali','sumatra','kalimantan','sulawesi','maluku','papua','ntb','ntt']

# Override files per object type
OVR_FILES = {
    'generator':    ('generator_reconciliation_overrides.csv', 'gen'),
    'substation':   ('substation_reconciliation_overrides.csv', 'sub'),
    'transmission': ('transmission_reconciliation_overrides.csv', 'trm'),
}


def collect_ids(project_root: Path) -> dict[str, dict[str, set[str]]]:
    """Return {object_type: {'baseline': set, 'ruptl': set}} untuk stale
    detection. Aggregate ID dari semua region."""
    ids = {'gen': {'baseline': set(), 'ruptl': set()},
           'sub': {'baseline': set(), 'ruptl': set()},
           'trm': {'baseline': set(), 'ruptl': set()}}
    proc = project_root / "data/processed"
    for region in REGIONS:
        # Generator
        gen_b = proc / f"generator_master_{region}.csv"
        gen_r = proc / f"ruptl_generators_{region}.csv"
        if gen_b.exists():
            with gen_b.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    ids['gen']['baseline'].add(row.get("id", "").strip())
        if gen_r.exists():
            with gen_r.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    ids['gen']['ruptl'].add(row.get("id", "").strip())
        # Substation
        sub_b = proc / f"substation_master_{region}.csv"
        sub_r = proc / f"ruptl_substations_{region}.csv"
        if sub_b.exists():
            with sub_b.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    ids['sub']['baseline'].add(row.get("id", "").strip())
        if sub_r.exists():
            with sub_r.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    ids['sub']['ruptl'].add(row.get("id", "").strip())
        # Transmission — baseline uses osm_id in feature.properties
        trm_gj = proc / f"transmission_{region}.geojson"
        if trm_gj.exists():
            import json
            gj = json.loads(trm_gj.read_text(encoding="utf-8"))
            for f in gj.get("features", []):
                p = f.get("properties") or {}
                oid = (p.get("osm_id") or p.get("id") or "").strip()
                if oid:
                    ids['trm']['baseline'].add(oid)
        trm_r = proc / f"ruptl_transmission_{region}.csv"
        if trm_r.exists():
            with trm_r.open(encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    ids['trm']['ruptl'].add(row.get("id", "").strip())
    return ids


def audit(region_filter: str = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    all_ids = collect_ids(project_root)

    print(f"{'=' * 60}")
    print(f"  RECONCILIATION OVERRIDE AUDIT")
    if region_filter:
        print(f"  Filtered to region: {region_filter}")
    print(f"{'=' * 60}\n")

    total_applied_hint = 0
    for label, (fname, otype) in OVR_FILES.items():
        path = project_root / "data/overrides" / fname
        print(f"── {label.upper()} ({fname}) ──")
        if not path.exists():
            print(f"  file tidak ada — no manual overrides untuk {label}\n")
            continue
        result = ovr.load_overrides(path, object_type=otype)
        if region_filter:
            result.valid = [o for o in result.valid if o.region == region_filter.lower()]
        ovr.detect_stale(result, all_ids[otype]['baseline'], all_ids[otype]['ruptl'])

        print(f"  Valid:   {len(result.valid)}")
        print(f"  Invalid: {len(result.invalid)}")
        if result.invalid:
            for o, err in result.invalid[:5]:
                print(f"    - {o.override_id or f'row {o.source_row}'}: {err}")
            if len(result.invalid) > 5:
                print(f"    - (+{len(result.invalid) - 5} more)")
        # Decision distribution
        c = Counter(o.decision for o in result.valid)
        for dec in sorted(c):
            print(f"  {dec:<18} {c[dec]:>4}")
        # Stale
        stale_bl = result.stale_missing_baseline
        stale_ru = result.stale_missing_ruptl
        if stale_bl:
            print(f"  ⚠ Stale (baseline_id not found): {len(stale_bl)}")
            for o in stale_bl[:5]:
                print(f"    - {o.override_id}: baseline_id={o.baseline_id}")
        if stale_ru:
            print(f"  ⚠ Stale (ruptl_id not found): {len(stale_ru)}")
            for o in stale_ru[:5]:
                print(f"    - {o.override_id}: ruptl_id={o.ruptl_id}")
        # Note: applied_ids populated hanya kalau kita run reconciler.
        # Cross-type audit ini cuma inspect state — untuk realized
        # applied count, lihat reconciliation report region.
        print()

    print(f"{'=' * 60}")
    print(f"NOTE: 'Applied' count per override baru ada di reconciliation")
    print(f"report per region (di-append otomatis section 'Override audit').")
    print(f"Contoh: data/reconciliation/report_jamali_*.md")
    print(f"{'=' * 60}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", help="Filter overrides ke region tertentu")
    opts = ap.parse_args()
    return audit(opts.region)


if __name__ == "__main__":
    raise SystemExit(main())
