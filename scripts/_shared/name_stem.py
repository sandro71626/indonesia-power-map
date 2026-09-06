"""Nama-plant normalization + type inference + haversine.

Diporting dari `indonesia-100gw-solar-study/tools/big_pembangkit_integrasi.py`
(function `nama_dasar`, `tipe_dari`, `hav`) dan
`indonesia-100gw-solar-study/tools/ruptl_extract.py` (function `norm`,
`token_set`). Fungsi-fungsi ini murni dan tidak bergantung ke path/data
manapun, jadi aman di-reuse cross-pipeline.

Design:
- `plant_name_stem(s)` — strip PLT prefix, unit numbers, boilerplate operator.
  Menghasilkan nama-inti yang bisa dibandingkan antara sumber (mis. RUPTL
  "PLTU Cirebon Unit 1" ↔ OSM "PLTU Cirebon 1" ↔ IPM "PLTU Cirebon Unit 1"
  semua → "cirebon").
- `plant_name_tokens(s)` — token set (stopword-filtered) untuk multi-token match.
- `infer_plant_type(name, fuel_hint)` — tebak jenis PLT dari prefix nama atau
  petunjuk energi primer. Fallback ke '?' kalau tidak jelas.
- `haversine_km(a, b)` — jarak great-circle antara dua koordinat.

Semua konstanta (mapping fuel→PLT type, stopwords) dikonfigurasi di module
level supaya bisa di-override dari test atau iterasi tuning.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Iterable, Optional


# -----------------------------------------------------------------------
# Type / fuel mapping — reuse konvensi PLN + tambahkan fuel dari BIG.
# -----------------------------------------------------------------------
# Prefix PLT yang dikenali dalam nama. Ordering penting: yang lebih spesifik
# di-cek dulu (PLTGU sebelum PLTG, PLTMG sebelum PLTM/PLTG).
PLT_PREFIXES: tuple[str, ...] = (
    "PLTGU", "PLTMG", "PLTMH", "PLTBm", "PLTBg", "PLTSa",
    "PLTU", "PLTG", "PLTD", "PLTA", "PLTM", "PLTP", "PLTS", "PLTB", "PLTN",
    "PLTAL",  # arus laut (tidal)
    "BESS",   # storage — bukan pembangkit tapi sering di kolom Jenis RUPTL
)

# Uppercase → canonical (mixed-case) mapping supaya output extractor
# konsisten dengan PLANT_COLORS/PLANT_LABEL di frontend (yang pakai
# case sesuai konvensi PLN, mis. "PLTBm" bukan "PLTBM").
CANONICAL_PLT_TYPE: dict[str, str] = {p.upper(): p for p in PLT_PREFIXES}
# Alias tambahan (typo umum di RUPTL / variasi penulisan):
CANONICAL_PLT_TYPE.update({
    "PLTBM": "PLTBm",       # biomassa uppercase → canonical mixed
    "PLTBG": "PLTBg",       # biogas
    "PLTSA": "PLTSa",       # sampah
    "PLTMH": "PLTMH",       # mikrohidro
    "PLTM": "PLTM",         # minihidro
})

# Petunjuk energi primer (BIG `enrgprmr`, OSM `plant:source`, RUPTL `Jenis`
# textual) → PLT type. Comparison lowercase substring.
ENERGY_TO_TYPE: dict[str, str] = {
    "air": "PLTA", "hydro": "PLTA", "hidro": "PLTA",
    "surya": "PLTS", "solar": "PLTS", "photovoltaic": "PLTS", "pv": "PLTS",
    "angin": "PLTB", "bayu": "PLTB", "wind": "PLTB",
    "panas bumi": "PLTP", "geothermal": "PLTP",
    "batubara": "PLTU", "coal": "PLTU", "steam": "PLTU",
    "gas": "PLTG",  # default gas → open cycle; combined_cycle detect di caller
    "combined": "PLTGU", "combined cycle": "PLTGU", "gas dan uap": "PLTGU",
    "mesin gas": "PLTMG", "gas engine": "PLTMG",
    "biomassa": "PLTBm", "biomass": "PLTBm",
    "biogas": "PLTBg",
    "sampah": "PLTSa", "waste": "PLTSa", "wte": "PLTSa",
    "nuklir": "PLTN", "nuclear": "PLTN",
    "diesel": "PLTD", "oil": "PLTD",
}

# Bahan bakar konvensional per PLT type (untuk output CSV `fuel` field bila
# tidak tersedia dari sumber asal).
TYPE_TO_FUEL: dict[str, str] = {
    "PLTU": "coal", "PLTG": "natural_gas", "PLTGU": "natural_gas",
    "PLTMG": "natural_gas", "PLTD": "oil", "PLTA": "hydro",
    "PLTM": "hydro", "PLTMH": "hydro", "PLTP": "geothermal",
    "PLTS": "solar", "PLTB": "wind", "PLTBm": "biomass",
    "PLTBg": "biogas", "PLTSa": "waste", "PLTN": "nuclear",
}

# Stopwords untuk token_set (jangan pakai token generik yang muncul di banyak
# nama). Reuse list dari referensi + tambah beberapa boilerplate khas RUPTL.
NAME_STOPWORDS: frozenset[str] = frozenset({
    "gi", "gitet", "gis", "bess",
    "pltu", "pltgu", "pltg", "pltmg", "plta", "pltm", "pltmh",
    "plts", "pltb", "pltbm", "pltbg", "pltsa", "pltd", "pltn",
    "unit", "eksisting", "baru", "new", "ext", "extension", "upr",
    "upgrading", "mw", "mwp", "kv", "mva", "kva",
    "arah", "sisi", "tersebar", "terpusat", "mpp", "mobile",
    "sewa", "ipp", "pln", "pt", "persero", "tbk",
    # Cardinal directions yang sering muncul di RUPTL row Lokasi
    "utara", "selatan", "barat", "timur", "tengah",
    "north", "south", "east", "west", "central",
    # Province & pulau names — muncul sebagai generic label di RUPTL
    # ("Banten (Kuota) II", "Jawa-Bali Tersebar", "Sumatera Kuota").
    # Nama plant proper biasanya specific ke lokasi (Suralaya, Cirata),
    # bukan ke provinsi.
    "jawa", "bali", "banten", "sumatera", "sumatra",
    "kalimantan", "sulawesi", "papua", "maluku",
    "aceh", "riau", "jambi", "bengkulu", "lampung",
    "gorontalo", "yogyakarta",
    # RUPTL aggregate/placeholder terms
    "kuota", "quota", "ftp",
})


# -----------------------------------------------------------------------
# Public helpers
# -----------------------------------------------------------------------
def normalize(s: Optional[str]) -> str:
    """NFKD strip diacritic, lowercase, keep alphanumeric + space.

    Reuse dari `ruptl_extract.norm`. Idempotent untuk multiple calls.
    Return string kosong untuk None/empty.
    """
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return " ".join(s.split())


def plant_name_stem(s: Optional[str]) -> str:
    """Nama-inti plant tanpa prefix teknologi/unit/boilerplate operator.

    Reuse dari `big_pembangkit_integrasi.nama_dasar`. Contoh:
      "PLTU Cirebon Unit 1"      → "cirebon"
      "PLTGU Muara Karang #01"   → "muara karang"
      "PT PLN PLTA Cirata"       → "cirata"
      "PLTS Bawean Terpusat"     → "bawean"

    Return string kosong bila input None/empty.
    """
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    # Buang nomor unit dengan variasi kata "unit"
    s = re.sub(r"#\s*\d+", " ", s)
    s = re.sub(r"\bunit\s*[0-9ivx]+\b", " ", s)
    # Buang prefix PLT (case-insensitive, whole-word)
    s = re.sub(
        r"\b(?:plt(?:u|g|gu|mg|d|a|m|mh|p|s|b|bm|bg|sa|n))\b",
        " ", s,
    )
    # Buang boilerplate operator/status
    s = re.sub(
        r"\b(?:terpusat|tersebar|mpp|mobile|sewa|ipp|pln|pt|persero|tbk)\b",
        " ", s,
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def plant_name_tokens(s: Optional[str]) -> set[str]:
    """Set token untuk multi-token equality/subset match.

    Reuse dari `ruptl_extract.token_set`. Menghapus stopwords + token pendek
    (< 3 char). Berguna untuk kasus urutan kata berbeda:
      "Cirebon Unit 1"     → {"cirebon"}
      "Unit 1 Cirebon"     → {"cirebon"}
      → same set, matchable
    """
    return {
        t for t in normalize(s).split()
        if t not in NAME_STOPWORDS and len(t) > 2
    }


def infer_plant_type(name: Optional[str], fuel_hint: Optional[str] = None) -> str:
    """Tentukan jenis PLT dari prefix nama; fallback ke petunjuk energi primer.

    Contoh:
      infer_plant_type("PLTU Suralaya #01")      → "PLTU"
      infer_plant_type("Gili Air PV", "solar")   → "PLTS"
      infer_plant_type("Sarwadadi", "hydro")     → "PLTA"

    Return "?" bila tidak bisa ditentukan.
    """
    s = re.sub(r"[^A-Za-z]", "", str(name or "")).upper()
    for prefix in PLT_PREFIXES:
        if s.startswith(prefix.upper()):
            return prefix
    hint = str(fuel_hint or "").lower()
    for keyword, plt_type in ENERGY_TO_TYPE.items():
        if keyword in hint:
            return plt_type
    # Kalau petunjuk bahan bakar mengandung HSD/MFO/B30 → diesel
    if any(k in hint for k in ("hsd", "mfo", "b30")):
        return "PLTD"
    return "?"


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Jarak great-circle antara dua koordinat (lon, lat) dalam kilometer.

    Reuse dari `big_pembangkit_integrasi.hav`. Input: tuple (lon, lat).
    Radius bumi standar 6371.0088 km.
    """
    R = 6371.0088
    P = math.pi / 180
    lon1, lat1 = float(a[0]), float(a[1])
    lon2, lat2 = float(b[0]), float(b[1])
    h = (
        math.sin((lat2 - lat1) * P / 2) ** 2
        + math.cos(lat1 * P) * math.cos(lat2 * P)
        * math.sin((lon2 - lon1) * P / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(max(0.0, h)))


def capacity_diff_pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Selisih kapasitas relatif terhadap rata-rata.

    Return None kalau salah satu None atau nol. Selisih dalam pecahan 0..∞.
    0.0 = identik, 0.2 = 20% selisih, dst.
    """
    if a is None or b is None:
        return None
    try:
        af, bf = float(a), float(b)
    except (TypeError, ValueError):
        return None
    if af <= 0 or bf <= 0:
        return None
    return abs(af - bf) / ((af + bf) / 2)
