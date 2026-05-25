"""Scratchpad: cari kandidat OSM untuk GI Hative Besar (Ambon) yang
tidak ter-fuzzy-match. Prefix '_' = bukan extractor shipped."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
gj = json.load(open(ROOT / "data/geojson/indonesia_substations.geojson"))

# bbox C7 Maluku
lat0, lon0, lat1, lon1 = -8.80, 125.00, -2.65, 135.80
print("OSM substations bernama dalam bbox C7 Maluku:")
for f in gj["features"]:
    g = f.get("geometry")
    if not g or g["type"] != "Point":
        continue
    lon, lat = g["coordinates"][:2]
    if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
        p = f.get("properties", {})
        nm = p.get("name") or p.get("name:en") or "(no name)"
        print(f"  {nm:<40} ({lat:.4f},{lon:.4f})  {p.get('@id','')}")

print("\nNama mengandung hative/laha/ambon/wayame (se-Indonesia):")
for f in gj["features"]:
    p = f.get("properties", {})
    nm = p.get("name") or p.get("name:en") or ""
    if any(k in nm.lower() for k in ["hative", "laha", "ambon", "wayame"]):
        g = f.get("geometry")
        c = g["coordinates"][:2] if g and g["type"] == "Point" else None
        print(f"  {nm:<40} {c}  {p.get('@id','')}")
