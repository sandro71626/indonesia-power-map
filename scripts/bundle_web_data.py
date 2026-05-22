"""
Bundle 3 GeoJSON layer (substations/generators/transmission) sebuah region
jadi:
  - web/data_<region>.js   — standalone JS bundle (window.<REGION>_DATA = {...})
  - update inline data di web/preview_<region>.html

Generic untuk semua region. Pakai:
    python3 scripts/bundle_web_data.py jamali
    python3 scripts/bundle_web_data.py sumatra

Tujuan: konsisten antara data/processed/*.geojson dan apa yang di-render di
preview. Jalankan setiap habis re-run extractor.

Pakai compact JSON (separators=(',',':')) supaya file kecil. Marker inline
data di HTML: baris 'window.<REGION>_DATA = {' sampai '};'.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GJ_DIR = ROOT / "data/processed"
WEB = ROOT / "web"

LAYERS = ["substations", "generators", "transmission"]


def load_compact(path: Path) -> str:
    """Load JSON, dump compact (tanpa spasi) jadi 1 baris string."""
    data = json.loads(path.read_text())
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/bundle_web_data.py <region>")
        print("  contoh: python3 scripts/bundle_web_data.py sumatra")
        sys.exit(1)

    region = sys.argv[1].strip().lower()
    region_var = region.upper()  # window.SUMATRA_DATA

    # Resolve source files. GeoJSON layer dinamai <layer-singular>_<region>.geojson:
    #   substations -> substations_<region>.geojson
    #   generators  -> generators_<region>.geojson
    #   transmission-> transmission_<region>.geojson
    sources = {}
    for layer in LAYERS:
        p = GJ_DIR / f"{layer}_{region}.geojson"
        if not p.exists():
            raise FileNotFoundError(f"Missing: {p}")
        sources[layer] = p

    payloads = {}
    for layer in LAYERS:
        payloads[layer] = load_compact(sources[layer])
        n = len(json.loads(payloads[layer]).get('features', []))
        print(f"  {layer:<13} {n:>5} features  ({sources[layer].stat().st_size:>9} bytes)")

    # --- 1. Write web/data_<region>.js ---
    js_path = WEB / f"data_{region}.js"
    lines = [f"window.{region_var}_DATA = {{"]
    for layer in LAYERS:
        lines.append(f"  {layer}: {payloads[layer]},")
    lines.append("};")
    js_path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {js_path} ({js_path.stat().st_size} bytes)")

    # --- 2. Patch web/preview_<region>.html inline data block ---
    html_path = WEB / f"preview_{region}.html"
    if not html_path.exists():
        print(f"WARNING: {html_path} tidak ada — skip patch HTML.")
        print("Done (data JS saja).")
        return

    html_lines = html_path.read_text().split('\n')
    marker = f"window.{region_var}_DATA = {{"
    start = None
    for i, line in enumerate(html_lines):
        if line.strip().startswith(marker):
            start = i
            break
    if start is None:
        raise RuntimeError(f"Marker '{marker}' tidak ditemukan di {html_path.name}")

    end = None
    for j in range(start + 1, len(html_lines)):
        if html_lines[j].strip() == "};":
            end = j
            break
    if end is None:
        raise RuntimeError(f"Closing '}};' tidak ditemukan setelah marker di {html_path.name}")

    new_block = [f"  {layer}: {payloads[layer]}," for layer in LAYERS]
    html_lines = html_lines[:start + 1] + new_block + html_lines[end:]
    html_path.write_text('\n'.join(html_lines))
    print(f"Patched {html_path} (block baris {start + 2}..{end})")

    print(f"\nDone. Buka web/preview_{region}.html di browser untuk lihat hasil.")


if __name__ == '__main__':
    main()
