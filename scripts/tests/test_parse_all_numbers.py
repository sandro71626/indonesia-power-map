#!/usr/bin/env python3
"""Regression tests untuk parse_all_numbers.

Historical bugs:
  - "120.0" salah di-parse jadi 1200 (rev 2026-09-05)
    Root cause: naive .replace(".", "") tanpa detect English decimal.
    Fix: smart detection (1-2 digit fraction = decimal, 3-digit = thousands).

Test dijalankan manual:
  python3 scripts/tests/test_parse_all_numbers.py

Return code non-zero kalau ada failure — cocok untuk CI integration.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from extract_ruptl_generators import parse_all_numbers

CASES = [
    # (input, expected, description)
    # ==== Baseline formats ====
    ('120', [120.0], 'plain int'),
    ('1200', [1200.0], '4-digit int (thousand)'),
    ('105', [105.0], '3-digit int'),
    ('45', [45.0], '2-digit int'),
    ('0', [0.0], 'zero'),

    # ==== English decimal (period as decimal) ====
    ('120.0', [120.0], 'english decimal .0 fraction'),
    ('120.5', [120.5], 'english decimal 1-digit fraction'),
    ('120.50', [120.5], 'english decimal 2-digit fraction trailing zero'),
    ('45.5', [45.5], 'small english decimal'),
    ('7.5', [7.5], 'single-digit english decimal'),
    ('0.4', [0.4], 'sub-unit english decimal'),
    ('0.05', [0.05], '3-digit-total english decimal'),
    ('12.30', [12.3], 'trailing zero preserve value'),
    ('1.5', [1.5], 'single-digit english decimal'),

    # ==== Indonesian format (period thousands, comma decimal) ====
    ('1.234', [1234.0], 'thousands separator'),
    ('1.234.567', [1234567.0], 'million with thousands separator'),
    ('12.345.678', [12345678.0], 'ten-million with thousands'),
    ('10.000', [10000.0], 'ten thousand'),
    ('100.000', [100000.0], 'hundred thousand'),
    ('105.000', [105000.0], '105 thousand'),
    ('1.234,56', [1234.56], 'thousands + decimal comma'),
    ('45,5', [45.5], 'indonesian decimal comma'),
    ('7,5', [7.5], 'single-digit decimal comma'),
    ('0,4', [0.4], 'sub-unit indonesian decimal'),
    ('10,000', [10.0], 'ambiguous: only comma → decimal (10.0)'),

    # ==== Multi-value cells (multi-unit) ====
    ('45 43', [45.0, 43.0], 'multi-unit space-separated'),
    ('2x15', [2.0, 15.0], 'multi-unit x-separated'),
    ('100 50 25', [100.0, 50.0, 25.0], 'three units'),

    # ==== Annotation noise ====
    ('* 105', [105.0], 'leading asterisk footnote'),
    ('105*', [105.0], 'trailing asterisk'),
    ('105 *', [105.0], 'asterisk with space'),

    # ==== Empty / edge ====
    ('', [], 'empty string'),
    ('   ', [], 'whitespace only'),
    ('n/a', [], 'no number'),
]


def run():
    fails = []
    for inp, expected, desc in CASES:
        got = parse_all_numbers(inp)
        if got != expected:
            fails.append((inp, expected, got, desc))
            print(f'  FAIL  "{inp}" → {got} (expected {expected}) — {desc}')
    print()
    total = len(CASES)
    passed = total - len(fails)
    print(f'  {passed}/{total} pass')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(run())
