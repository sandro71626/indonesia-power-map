"""Shared override system untuk reconciliation pipeline.

Manual override adalah source of truth yang persistent dan reproducible.
Setiap kali pipeline dijalankan, override CSV dibaca dan diterapkan ke
hasil auto-matching. Manual > automatic.

Design principles:
  - Raw source data (baseline CSV, RUPTL CSV) TIDAK pernah di-overwrite
  - Override output di-tag di reconciled CSV via `override_applied=true`
    + `override_id` companion columns → downstream tau ini manual
  - Invalid override (baseline_id/ruptl_id tidak ditemukan) → dilaporkan
    sebagai stale, tidak silently ignored
  - Schema seragam untuk 3 object type (gen/sub/trm)

Canonical enum decisions:
  CONFIRM_MATCH     — Endorse auto match (analyst review pass)
  FORCE_MATCH       — Force pair yang algorithm miss
  REJECT_MATCH      — Split auto pair (baseline & ruptl kembali unmatched)
  KEEP_BASELINE     — For CONFLICT: pakai baseline value, ignore RUPTL
  USE_RUPTL_VALUE   — Field-level: apply RUPTL value ke canonical field
  IGNORE_RUPTL_ROW  — Drop RUPTL row entirely (garbage/dup)

CSV schema (semua object type identik):
  override_id, region, baseline_id, ruptl_id, decision,
  field, override_value, reason, reviewed_by, review_date

Kolom required per decision:
  CONFIRM_MATCH    → baseline_id + ruptl_id
  FORCE_MATCH      → baseline_id + ruptl_id
  REJECT_MATCH     → baseline_id + ruptl_id
  KEEP_BASELINE    → baseline_id (field optional)
  USE_RUPTL_VALUE  → ruptl_id + field + override_value
  IGNORE_RUPTL_ROW → ruptl_id
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Optional


# ----------------------------------------------------------------------
# Canonical enum + validation rules
# ----------------------------------------------------------------------
DECISION_CONFIRM_MATCH = "CONFIRM_MATCH"
DECISION_FORCE_MATCH = "FORCE_MATCH"
DECISION_REJECT_MATCH = "REJECT_MATCH"
DECISION_KEEP_BASELINE = "KEEP_BASELINE"
DECISION_USE_RUPTL_VALUE = "USE_RUPTL_VALUE"
DECISION_IGNORE_RUPTL_ROW = "IGNORE_RUPTL_ROW"

VALID_DECISIONS = frozenset({
    DECISION_CONFIRM_MATCH,
    DECISION_FORCE_MATCH,
    DECISION_REJECT_MATCH,
    DECISION_KEEP_BASELINE,
    DECISION_USE_RUPTL_VALUE,
    DECISION_IGNORE_RUPTL_ROW,
})

# Required kolom (non-empty) per decision.
DECISION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    DECISION_CONFIRM_MATCH: ("baseline_id", "ruptl_id"),
    DECISION_FORCE_MATCH: ("baseline_id", "ruptl_id"),
    DECISION_REJECT_MATCH: ("baseline_id", "ruptl_id"),
    DECISION_KEEP_BASELINE: ("baseline_id",),
    DECISION_USE_RUPTL_VALUE: ("ruptl_id", "field", "override_value"),
    DECISION_IGNORE_RUPTL_ROW: ("ruptl_id",),
}

# Legacy decision aliases (untuk backward-compat dengan format lama
# `data/overrides/generator_matches.csv`).
LEGACY_ALIAS: dict[str, str] = {
    "merge": DECISION_FORCE_MATCH,
    "keep_separate": DECISION_REJECT_MATCH,
    "drop_ruptl": DECISION_IGNORE_RUPTL_ROW,
    # `drop_ipm` legacy — not implemented, will raise validation warning.
}

CANONICAL_HEADERS = [
    "override_id", "region", "baseline_id", "ruptl_id", "decision",
    "field", "override_value", "reason", "reviewed_by", "review_date",
]


# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class Override:
    """One override row, normalized."""
    override_id: str
    region: str
    baseline_id: str
    ruptl_id: str
    decision: str
    field: str
    override_value: str
    reason: str
    reviewed_by: str
    review_date: str
    source_row: int  # 1-based line number di CSV (untuk error message)

    def key(self) -> tuple[str, str]:
        """(baseline_id, ruptl_id) sebagai lookup key."""
        return (self.baseline_id, self.ruptl_id)


@dataclass
class OverrideValidationResult:
    """Hasil validasi setelah load override CSV."""
    valid: list[Override] = dc_field(default_factory=list)
    invalid: list[tuple[Override, str]] = dc_field(default_factory=list)
    # Applied vs unused, tracked di runtime pipeline
    applied_ids: set = dc_field(default_factory=set)
    stale_missing_baseline: list[Override] = dc_field(default_factory=list)
    stale_missing_ruptl: list[Override] = dc_field(default_factory=list)

    @property
    def unused(self) -> list[Override]:
        return [o for o in self.valid if o.override_id not in self.applied_ids]


# ----------------------------------------------------------------------
# Loader + validator
# ----------------------------------------------------------------------
def load_overrides(path: Path, object_type: str = "") -> OverrideValidationResult:
    """Load override CSV + validasi setiap baris.

    Return OverrideValidationResult dengan .valid dan .invalid separated.
    - object_type: 'gen'|'sub'|'trm' (untuk error message context saja)
    - Path tidak wajib exist — kalau missing, return empty result (no error)
    """
    result = OverrideValidationResult()
    if not path.exists():
        return result

    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):  # start=2: header di line 1
            # Legacy alias: kalau file lama pakai "decision" nilai lowercase,
            # translate ke canonical enum.
            raw_decision = (row.get("decision") or "").strip()
            decision = LEGACY_ALIAS.get(raw_decision.lower(), raw_decision.upper())

            # Legacy generator override columns: ipm_id → baseline_id;
            # *_override → field/override_value composite (skip untuk sekarang,
            # user harus migrate manual bila mau pakai unified format).
            baseline_id = ((row.get("baseline_id") or row.get("ipm_id")
                             or row.get("baseline") or "").strip())

            ov = Override(
                override_id=(row.get("override_id") or "").strip(),
                region=(row.get("region") or "").strip().lower(),
                baseline_id=baseline_id,
                ruptl_id=(row.get("ruptl_id") or "").strip(),
                decision=decision,
                field=(row.get("field") or "").strip(),
                override_value=(row.get("override_value") or "").strip(),
                reason=(row.get("reason") or "").strip(),
                reviewed_by=(row.get("reviewed_by") or "").strip(),
                review_date=(row.get("review_date")
                              or row.get("reviewed_at") or "").strip(),
                source_row=idx,
            )
            err = _validate_override(ov, object_type)
            if err:
                result.invalid.append((ov, err))
            else:
                result.valid.append(ov)
    return result


def _validate_override(ov: Override, object_type: str) -> Optional[str]:
    """Return error string kalau invalid, None kalau OK."""
    if not ov.override_id:
        return f"missing override_id (row {ov.source_row})"
    if not ov.decision:
        return f"missing decision (row {ov.source_row})"
    if ov.decision not in VALID_DECISIONS:
        return (f"unknown decision '{ov.decision}' — "
                f"valid: {sorted(VALID_DECISIONS)}")
    if not ov.region:
        return f"missing region"
    required = DECISION_REQUIREMENTS[ov.decision]
    for field_name in required:
        val = getattr(ov, field_name)
        if not val:
            return f"decision {ov.decision} requires field '{field_name}'"
    return None


# ----------------------------------------------------------------------
# Stale detection
# ----------------------------------------------------------------------
def detect_stale(result: OverrideValidationResult,
                  baseline_ids: set[str],
                  ruptl_ids: set[str]) -> None:
    """Populate result.stale_missing_baseline + stale_missing_ruptl.

    Panggil ini setelah load_overrides, dengan set ID valid dari
    baseline CSV + RUPTL CSV. Override yang reference ID non-existent
    dianggap stale.
    """
    for ov in result.valid:
        if ov.baseline_id and ov.baseline_id not in baseline_ids:
            result.stale_missing_baseline.append(ov)
        if ov.ruptl_id and ov.ruptl_id not in ruptl_ids:
            result.stale_missing_ruptl.append(ov)


# ----------------------------------------------------------------------
# Lookup helpers — dipakai reconciler untuk cari override yang match
# ----------------------------------------------------------------------
def find_override_by_pair(result: OverrideValidationResult,
                           baseline_id: str, ruptl_id: str) -> Optional[Override]:
    """Cari override dengan baseline_id + ruptl_id yang sama.

    Precedence: exact pair match paling kuat.
    """
    for ov in result.valid:
        if ov.baseline_id == baseline_id and ov.ruptl_id == ruptl_id:
            return ov
    return None


def find_overrides_by_ruptl(result: OverrideValidationResult,
                              ruptl_id: str) -> list[Override]:
    """Semua override yang reference ruptl_id (tanpa baseline_id atau
    dengan baseline_id apapun). Dipakai untuk IGNORE_RUPTL_ROW +
    FORCE_MATCH scenarios.
    """
    return [ov for ov in result.valid if ov.ruptl_id == ruptl_id]


def find_overrides_by_baseline(result: OverrideValidationResult,
                                 baseline_id: str) -> list[Override]:
    """Semua override yang reference baseline_id."""
    return [ov for ov in result.valid if ov.baseline_id == baseline_id]


# ----------------------------------------------------------------------
# Provenance tagging
# ----------------------------------------------------------------------
def tag_row_with_override(row: dict, ov: Override) -> dict:
    """Add provenance columns ke reconciled row.

    Idempotent — kalau row sudah punya override_id, overwrite dengan
    yang baru (chain of overrides skenario).
    """
    row["override_applied"] = "true"
    row["override_id"] = ov.override_id
    row["override_decision"] = ov.decision
    row["override_by"] = ov.reviewed_by
    row["override_date"] = ov.review_date
    row["override_reason"] = ov.reason
    return row


PROVENANCE_COLUMNS = [
    "override_applied", "override_id", "override_decision",
    "override_by", "override_date", "override_reason",
]


# ----------------------------------------------------------------------
# Audit report writer
# ----------------------------------------------------------------------
def format_audit_summary(result: OverrideValidationResult,
                          object_type: str) -> list[str]:
    """Return list of markdown lines untuk audit report section.

    Panggil setelah pipeline selesai (applied_ids sudah populated).
    """
    lines = []
    lines.append(f"### Override audit — {object_type}")
    lines.append("")
    lines.append(f"- Loaded overrides: {len(result.valid)} valid, "
                 f"{len(result.invalid)} invalid")

    from collections import Counter
    decision_counts = Counter(o.decision for o in result.valid)
    for dec in sorted(decision_counts):
        lines.append(f"  - {dec}: {decision_counts[dec]}")

    applied = [o for o in result.valid if o.override_id in result.applied_ids]
    lines.append(f"- Applied: {len(applied)}")
    lines.append(f"- Unused (loaded but not applied): {len(result.unused)}")
    lines.append(f"- Stale (missing baseline_id): {len(result.stale_missing_baseline)}")
    lines.append(f"- Stale (missing ruptl_id):    {len(result.stale_missing_ruptl)}")

    if result.invalid:
        lines.append("")
        lines.append("#### Invalid overrides (dropped, needs fix)")
        for ov, err in result.invalid[:10]:
            lines.append(f"  - `{ov.override_id or f'row {ov.source_row}'}`: {err}")
        if len(result.invalid) > 10:
            lines.append(f"  - _(+{len(result.invalid) - 10} more)_")

    if result.stale_missing_baseline:
        lines.append("")
        lines.append("#### Stale: baseline_id tidak ditemukan")
        for ov in result.stale_missing_baseline[:10]:
            lines.append(f"  - `{ov.override_id}`: baseline_id=`{ov.baseline_id}`")

    if result.stale_missing_ruptl:
        lines.append("")
        lines.append("#### Stale: ruptl_id tidak ditemukan")
        for ov in result.stale_missing_ruptl[:10]:
            lines.append(f"  - `{ov.override_id}`: ruptl_id=`{ov.ruptl_id}`")

    lines.append("")
    return lines


# ----------------------------------------------------------------------
# Template writer — bootstrap empty override CSV
# ----------------------------------------------------------------------
def write_template(path: Path) -> None:
    """Write empty template dengan canonical headers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        w.writeheader()
