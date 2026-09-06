#!/usr/bin/env python3
"""Run full reconciliation pipeline untuk 1 region atau semua.

Stages:
  1. extract_ruptl_generators
  2. extract_ruptl_substations
  3. extract_ruptl_transmission
  4. geocode_ruptl_generators
  5. reconcile_generators (--write)
  6. merge_reconciled_to_geojson (generators)
  7. detect_substation_delta (--write)
  8. enrich_transmission_endpoints
  9. merge_transmission_circuits
  10. reconcile_transmission (--write)
  11. bundle_web_data

Setiap stage skip-able via CLI flag. Kalau region-nya kecil (papua, ntb, ntt)
runtime cukup pendek. Sumatra/Jamali paling lama.

Usage:
    # Satu region
    python3 scripts/run_region_pipeline.py --region sumatra
    # Semua region
    python3 scripts/run_region_pipeline.py --all
    # Skip re-extract (kalau CSV udah ada)
    python3 scripts/run_region_pipeline.py --region jamali --skip-extract
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


# Per-region default page ranges (RUPTL Lampiran A/B/C in PDF).
# Wide-ish untuk safety — extractor filter by province anyway.
REGION_PAGE_RANGES: dict[str, tuple[int, int]] = {
    "sumatra":    (595, 815),
    "kalimantan": (720, 820),
    "jamali":     (811, 950),
    "sulawesi":   (950, 1055),
    "maluku":     (1050, 1105),
    "papua":      (1100, 1155),
    "ntb":        (1150, 1170),
    "ntt":        (1165, 1200),
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = PROJECT_ROOT / "data/raw/sources/RUPTL-2025-2034.pdf"


def run(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    """Execute subprocess, return (returncode, tail_stdout)."""
    print(f"\n$ {' '.join(cmd)}")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(PROJECT_ROOT), timeout=timeout,
                            capture_output=True, text=True)
        elapsed = time.time() - t0
        tail = "\n".join(r.stdout.strip().split("\n")[-8:])
        print(f"  ({elapsed:.1f}s) rc={r.returncode}")
        if tail:
            print("  " + tail.replace("\n", "\n  "))
        if r.returncode != 0 and r.stderr:
            print(f"  STDERR: {r.stderr[:400]}")
        return r.returncode, tail
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout}s")
        return -1, ""


def run_region(region: str, opts: argparse.Namespace) -> bool:
    """Run all stages for 1 region. Return True kalau semua sukses."""
    print(f"\n{'=' * 72}")
    print(f"  REGION: {region}")
    print(f"{'=' * 72}")

    ps, pe = REGION_PAGE_RANGES.get(region, (595, 1200))
    pages = f"{ps}-{pe}"
    ok = True

    if not opts.skip_extract:
        # Generator extractor
        rc, _ = run(["python3", "scripts/extract_ruptl_generators.py",
                      "--region", region, "--pdf", str(PDF_PATH),
                      "--pages", pages], timeout=300)
        ok = ok and (rc == 0)
        # Substation extractor
        rc, _ = run(["python3", "scripts/extract_ruptl_substations.py",
                      "--region", region, "--pdf", str(PDF_PATH),
                      "--pages", pages], timeout=300)
        ok = ok and (rc == 0)
        # Transmission extractor
        rc, _ = run(["python3", "scripts/extract_ruptl_transmission.py",
                      "--region", region, "--pdf", str(PDF_PATH),
                      "--pages", pages], timeout=300)
        ok = ok and (rc == 0)

    if not opts.skip_generators:
        # Geocode
        rc, _ = run(["python3", "scripts/geocode_ruptl_generators.py",
                      "--region", region])
        ok = ok and (rc == 0)
        # Reconcile generators
        rc, _ = run(["python3", "scripts/reconcile_generators.py",
                      "--region", region, "--write"])
        ok = ok and (rc == 0)
        # Merge reconciled → GeoJSON
        rc, _ = run(["python3", "scripts/merge_reconciled_to_geojson.py",
                      "--region", region])
        ok = ok and (rc == 0)

    if not opts.skip_substations:
        # Substation delta
        rc, _ = run(["python3", "scripts/detect_substation_delta.py",
                      "--region", region, "--write"])
        ok = ok and (rc == 0)
        # Merge substation delta → reconciled GeoJSON (planned GI features)
        rc, _ = run(["python3", "scripts/merge_substation_delta_to_geojson.py",
                      "--region", region])
        ok = ok and (rc == 0)

    if not opts.skip_transmission:
        # Enrich endpoints
        rc, _ = run(["python3", "scripts/enrich_transmission_endpoints.py",
                      "--region", region])
        ok = ok and (rc == 0)
        # Merge circuits
        rc, _ = run(["python3", "scripts/merge_transmission_circuits.py",
                      "--region", region])
        ok = ok and (rc == 0)
        # Reconcile transmission
        rc, _ = run(["python3", "scripts/reconcile_transmission.py",
                      "--region", region, "--write"])
        ok = ok and (rc == 0)
        # Audit
        rc, _ = run(["python3", "scripts/audit_planned_transmission.py",
                      "--region", region,
                      "--csv", f"data/reconciliation/transmission_audit_{region}.csv"])
        # Audit tidak boleh gagal-block

    if not opts.skip_bundle:
        rc, _ = run(["python3", "scripts/bundle_web_data.py", region])
        ok = ok and (rc == 0)

    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--region", help="Region key (sumatra/jamali/…)")
    grp.add_argument("--all", action="store_true",
                     help="Run untuk semua 8 region")
    ap.add_argument("--skip-extract", action="store_true",
                    help="Skip PDF extraction (pakai CSV yang ada)")
    ap.add_argument("--skip-generators", action="store_true")
    ap.add_argument("--skip-substations", action="store_true")
    ap.add_argument("--skip-transmission", action="store_true")
    ap.add_argument("--skip-bundle", action="store_true")
    opts = ap.parse_args()

    if not PDF_PATH.exists():
        print(f"RUPTL PDF not found: {PDF_PATH}", file=sys.stderr)
        return 2

    regions = list(REGION_PAGE_RANGES.keys()) if opts.all else [opts.region]

    results: dict[str, bool] = {}
    for r in regions:
        results[r] = run_region(r, opts)

    print(f"\n{'=' * 72}")
    print("  SUMMARY")
    print(f"{'=' * 72}")
    for r, ok in results.items():
        print(f"  {r:<12} {'OK' if ok else 'FAILED'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
