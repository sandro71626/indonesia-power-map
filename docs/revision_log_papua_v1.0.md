# PAPUA v1.0 Revision Log

**Tanggal:** 2026-05-30
**Scope:** Dataset Papua (generator only)
**Sebelum:** 16 generator
**Sesudah:** 21 generator (+5)

## Catatan interpretasi

User spec di section 1 "Remove GEN-PAP-0001" dan section 2 "Replace
GEN-PAP-0001 dengan PLTD Kota Sorong" — diinterpretasikan sebagai
**update-in-place**, bukan delete-then-create. ID GEN-PAP-0001
dipertahankan dengan metadata baru (name + cap update). Saat inventory,
GEN-PAP-0001 sudah named "PLTD Kota Sorong" (existing), jadi hanya
capacity yang ter-update ke 40,37 MW.

---

## 1. Removed assets (0)

Tidak ada removal aktual (lihat catatan interpretasi).

## 2. Renamed / updated assets (4 entries)

| ID | Nama (current sudah benar) | Type | Capacity (MW / MWp) |
|----|-----------|:---:|---:|
| GEN-PAP-0001 | PLTD Kota Sorong | PLTD | **40,37 MW** |
| GEN-PAP-0005 | PLTD Fakfak | PLTD | **8,8 MW** |
| GEN-PAP-0010 | PLTS Sara | PLTS | **0,020 MWp** |
| GEN-PAP-0009 | PLTS Werua | PLTS | **0,020 MWp** |

4 name overrides ditambahkan ke `generator_name_overrides.csv` (107 → 111
entries) untuk persistence.

## 3. Newly added assets (5 entries)

`review_flag=MANUAL_ADD_v1.0`, `source_id=manual_revision_v1.0`,
`osm_id=(kosong)`.

### Wamena area (Pegunungan Tengah Papua) — 2 entries

| ID | Nama | Type | Capacity (MW) | Koord |
|----|------|:---:|---:|-------|
| GEN-PAP-0017 | PLTD Sinakma | PLTD | 6,0 | -4,1017; 138,9312 |
| GEN-PAP-0018 | PLTMH Walesi | PLTMH | 3,85 | -4,1284; 138,9567 |

### Kaimana area (Bird's Tail Papua Barat) — 3 entries

| ID | Nama | Type | Capacity | Koord |
|----|------|:---:|---|-------|
| GEN-PAP-0019 | PLTS Pulau Namatota | PLTS | 0,063 MWp | -3,6492; 133,5684 |
| GEN-PAP-0020 | PLTS Kampung Maimai | PLTS | 0,040 MWp (midpoint 30–50 kWp) ⚠️ | -3,6761; 133,6711 |
| GEN-PAP-0021 | PLTD Kaimana | PLTD | 8,8 MW | -3,6558; 133,7663 |

## 4. Capacity updates summary

| Type | Count | Range |
|------|------:|---|
| PLTD | 4 entries | 6 - 40,37 MW |
| PLTMH | 1 entry | 3,85 MW |
| PLTS | 4 entries | 0,020 - 0,063 MWp |

## 5. Capacity formatting rule

Kolom `capacity_unit` ditambahkan. Total **6 row PLTS** ber-`MWp`
(termasuk 2 PLTS baru manual-added). Sisanya `MW`.

## 6. Unresolved items (perlu manual review)

| Item | Issue | Status |
|------|-------|--------|
| **GEN-PAP-0020 (PLTS Kampung Maimai)** | Capacity user di-spec sebagai range "30–50 kWp" tanpa nilai definitif. | Saya pakai midpoint 0,040 MWp (= 40 kWp), `review_flag` di-set `MANUAL_ADD_v1.0;CAPACITY_RANGE_30-50_kWp_review`. Verifikasi capacity definitif perlu via sumber sekunder (PLN report, vendor datasheet). |

## Files updated

- `data/processed/generator_master_papua.csv` (21 rows, was 16; +1 kolom `capacity_unit`)
- `data/processed/generators_papua.geojson` (re-built)
- `data/overrides/generator_name_overrides.csv` (107 → 111 entries; +4 Papua v1.0)
- `web/data_papua.js` (re-bundled)

## Summary

- **Removed:** 0 (interpretasi "Remove + Replace" sebagai update-in-place)
- **Renamed / updated:** 4 entries (PLTD Kota Sorong cap 40,37 MW; PLTD Fakfak cap 8,8 MW; PLTS Werua/Sara cap 0,020 MWp each)
- **Newly added:** 5 entries (PLTD Sinakma 6 MW Wamena; PLTMH Walesi 3,85 MW; PLTS Pulau Namatota 0,063 MWp; PLTS Kampung Maimai 0,040 MWp flagged; PLTD Kaimana 8,8 MW)
- **Capacity updates:** 9 entries total (4 updated + 5 new)
- **Status changes:** none
- **Schema:** +1 kolom `capacity_unit` (6 PLTS ber-MWp)
- **Unresolved:** 1 entry (GEN-PAP-0020 PLTS Kampung Maimai capacity range)
