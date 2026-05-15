"""
Bundle 3 GeoJSON Jamali (substations/generators/transmission) jadi:
  - web/data_jamali.js — standalone JS bundle (window.JAMALI_DATA = {...})
  - update inline data di web/preview_jamali.html (line 245-247)

Tujuan: konsisten antara processed/*.geojson dan apa yang di-render di preview.

Pakai compact JSON (separators=(',',':')) supaya file kecil. Format embed
sengaja sama dengan struktur existing biar git diff cuma di payload, bukan
struktur — gampang di-review.

Jalankan setiap habis re-run extractor.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GJ_DIR = ROOT / "data/processed"
WEB = ROOT / "web"

SOURCES = [
    ("substations",  GJ_DIR / "substations_jamali.geojson"),
    ("generators",   GJ_DIR / "generators_jamali.geojson"),
    ("transmission", GJ_DIR / "transmission_jamali.geojson"),
]


def load_compact(path: Path) -> str:
    """Load JSON, dump compact (no spaces) jadi 1 string baris."""
    data = json.loads(path.read_text())
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def main():
    payloads = {}
    for key, p in SOURCES:
        if not p.exists():
            raise FileNotFoundError(f"Missing: {p}")
        payloads[key] = load_compact(p)
        n = json.loads(payloads[key]).get('features', [])
        print(f"  {key:<13} {len(n):>5} features  ({p.stat().st_size:>8} bytes)")

    # --- 1. Write web/data_jamali.js ---
    js_path = WEB / "data_jamali.js"
    lines = ["window.JAMALI_DATA = {"]
    for key, _ in SOURCES:
        lines.append(f"  {key}: {payloads[key]},")
    lines.append("};")
    js_path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {js_path} ({js_path.stat().st_size} bytes)")

    # --- 2. Patch web/preview_jamali.html inline data block ---
    html_path = WEB / "preview_jamali.html"
    html_lines = html_path.read_text().split('\n')

    # Cari baris "window.JAMALI_DATA = {" lalu replace baris-baris key sampai "};"
    start = None
    for i, line in enumerate(html_lines):
        if line.strip().startswith("window.JAMALI_DATA = {"):
            start = i
            break
    if start is None:
        raise RuntimeError("Marker 'window.JAMALI_DATA = {' tidak ditemukan di preview HTML")

    # Cari closing "};"
    end = None
    for j in range(start + 1, len(html_lines)):
        if html_lines[j].strip() == "};":
            end = j
            break
    if end is None:
        raise RuntimeError("Closing '};' tidak ditemukan setelah marker JAMALI_DATA")

    # Replace [start+1 .. end-1] dengan baris payload baru
    new_block = [f"  {key}: {payloads[key]},"
                 for key, _ in SOURCES]
    html_lines = html_lines[:start + 1] + new_block + html_lines[end:]
    html_path.write_text('\n'.join(html_lines))
    print(f"Patched {html_path} (block lines {start+2}..{end})")

    print("\nDone. Buka web/preview_jamali.html di browser untuk lihat hasil.")


if __name__ == '__main__':
    main()
