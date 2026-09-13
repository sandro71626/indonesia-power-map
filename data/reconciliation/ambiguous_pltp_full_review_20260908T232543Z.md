# AMBIGUOUS PLTP Clusters — Full Manual Review (11 clusters)

Generated: 2026-09-08T23:25:43.855656+00:00
Cluster radius: 3.0 km

Sorted by review priority:
1. Highest potential double-counting capacity (total_mw)
2. Highest number of unnamed features
3. Largest spatial spread

Decision options per cluster:
- `MERGE_AS_ONE_COMPLEX` — treat semua features as single complex
- `KEEP_SEPARATE` — distinct plants, tidak perlu action
- `PARTIAL_MERGE` — merge subset (mis. existing only, planned terpisah)
- `NEED_MORE_EVIDENCE` — perlu data source tambahan / PDF verification

**Recommended decision advisory only — jangan apply otomatis.**

---

## Priority summary table

| # | Cluster | Region | Features | Total MW | Unnamed | Spread km | Recommendation |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | **Dieng (FTP2)** | jamali | 8 | 415.0 | 0 | 0.00 | `PARTIAL_MERGE` |
| 2 | **Sorik Marapi (FTP2)** | sumatra | 2 | 338.0 | 0 | 0.00 | `PARTIAL_MERGE` |
| 3 | **Lumut Balai (FTP2) #2** | sumatra | 4 | 275.0 | 0 | 0.00 | `PARTIAL_MERGE` |
| 4 | **Baturaden (FTP2)** | jamali | 3 | 220.0 | 0 | 0.00 | `MERGE_AS_ONE_COMPLEX` |
| 5 | **Bedugul** | jamali | 4 | 175.0 | 0 | 0.00 | `MERGE_AS_ONE_COMPLEX` |
| 6 | **Medco Energi Geothermal** | jamali | 6 | 110.0 | 0 | 2.12 | `KEEP_SEPARATE` |
| 7 | **Rantau Dedap (FTP2)** | sumatra | 2 | 108.0 | 0 | 0.00 | `PARTIAL_MERGE` |
| 8 | **PLTP Lahendong III & IV** | sulawesi | 2 | 80.0 | 0 | 2.48 | `NEED_MORE_EVIDENCE` |
| 9 | **PLTP Ulumbu** | ntt | 3 | 50.0 | 0 | 0.00 | `PARTIAL_MERGE` |
| 10 | **Tangkuban Perahu (FTP2)** | jamali | 2 | 40.0 | 0 | 0.00 | `MERGE_AS_ONE_COMPLEX` |
| 11 | **Sokoria (FTP2)** | ntt | 3 | 30.0 | 0 | 0.00 | `PARTIAL_MERGE` |

---

## 1. Dieng (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-JAMALI-P`
- **Region**: jamali
- **Total features**: 8 (0 unnamed)
- **Total capacity**: 415.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {'Geo Dipa Energi'}
- **Common name stem**: dieng

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-JMB-0119` | PLTP Dieng | PLTP | 70.0 | -7.2263,109.8973 | existing/existing | Geo Dipa Energi | `way/1189922860` | — |
| 2 | `RUPTL:RUPTL-JAMALI-P-0123` | Dieng (FTP2) | PLTP | 55.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0123` | 2027 |
| 3 | `RUPTL:RUPTL-JAMALI-P-0126` | Dieng (FTP2) | PLTP | 35.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0126` | 2028 |
| 4 | `RUPTL:RUPTL-JAMALI-P-0130` | Dieng (FTP2) | PLTP | 55.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0130` | 2030 |
| 5 | `RUPTL:RUPTL-JAMALI-P-0131` | Dieng (FTP2) | PLTP | 55.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0131` | 2030 |
| 6 | `RUPTL:RUPTL-JAMALI-P-0149` | Dieng (FTP2) | PLTP | 55.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0149` | 2033 |
| 7 | `RUPTL:RUPTL-JAMALI-P-0150` | Dieng (FTP2) | PLTP | 55.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0150` | 2033 |
| 8 | `RUPTL:RUPTL-JAMALI-P-0151` | Dieng (FTP2) | PLTP | 35.0 | -7.2263,109.8973 | planned/Construction | — | `RUPTL-JAMALI-P-0151` | 2033 |

**Why AMBIGUOUS:**
- 8 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'dieng' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---

## 2. Sorik Marapi (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-SUMATRA-`
- **Region**: sumatra
- **Total features**: 2 (0 unnamed)
- **Total capacity**: 338.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: sorik

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-SMT-0072` | PLTP Sorik Marapi | PLTP | 240.0 | 0.7151,99.5707 | existing/existing | — | `way/938146456` | — |
| 2 | `RUPTL:RUPTL-SUMATRA-P-0027` | Sorik Marapi (FTP2) | PLTP | 98.0 | 0.7150,99.5707 | planned/Construction | — | `RUPTL-SUMATRA-P-0027` | 2025 |

**Why AMBIGUOUS:**
- 2 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'sorik' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---

## 3. Lumut Balai (FTP2) #2

- **Cluster ID**: `RUPTL:RUPTL-SUMATRA-`
- **Region**: sumatra
- **Total features**: 4 (0 unnamed)
- **Total capacity**: 275.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: lumut

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-SMT-0067` | PLTP Lumut Balai | PLTP | 110.0 | -4.1979,103.6486 | existing/existing | — | `way/931931104` | — |
| 2 | `RUPTL:RUPTL-SUMATRA-P-0102` | Lumut Balai (FTP2) #2 | PLTP | 55.0 | -4.1979,103.6486 | planned/Construction | — | `RUPTL-SUMATRA-P-0102` | 2025 |
| 3 | `RUPTL:RUPTL-SUMATRA-P-0115` | Lumut Balai (FTP2) #3 | PLTP | 55.0 | -4.1979,103.6486 | planned/Construction | — | `RUPTL-SUMATRA-P-0115` | 2033 |
| 4 | `RUPTL:RUPTL-SUMATRA-P-0116` | Lumut Balai (FTP2) #4 | PLTP | 55.0 | -4.1979,103.6486 | planned/Construction | — | `RUPTL-SUMATRA-P-0116` | 2033 |

**Why AMBIGUOUS:**
- 4 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'lumut' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---

## 4. Baturaden (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-JAMALI-P`
- **Region**: jamali
- **Total features**: 3 (0 unnamed)
- **Total capacity**: 220.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: baturaden

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `RUPTL:RUPTL-JAMALI-P-0138` | Baturaden (FTP2) | PLTP | 110.0 | -7.3148,109.2295 | planned/Proposed | — | `RUPTL-JAMALI-P-0138` | 2031 |
| 2 | `RUPTL:RUPTL-JAMALI-P-0139` | Baturaden (FTP2) | PLTP | 75.0 | -7.3148,109.2295 | planned/Proposed | — | `RUPTL-JAMALI-P-0139` | 2031 |
| 3 | `RUPTL:RUPTL-JAMALI-P-0143` | Baturaden (FTP2) | PLTP | 35.0 | -7.3148,109.2295 | planned/Proposed | — | `RUPTL-JAMALI-P-0143` | 2032 |

**Why AMBIGUOUS:**
- 3 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant

**Risk if MERGED:**
- Low risk (evidence supports merge)

**Risk if KEPT SEPARATE:**
- Nama share common stem 'baturaden' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `MERGE_AS_ONE_COMPLEX`

---

## 5. Bedugul

- **Cluster ID**: `RUPTL:RUPTL-JAMALI-P`
- **Region**: jamali
- **Total features**: 4 (0 unnamed)
- **Total capacity**: 175.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: bedugul

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `RUPTL:RUPTL-JAMALI-P-0272` | Bedugul | PLTP | 5.0 | -8.2848,115.1713 | planned/Proposed | — | `RUPTL-JAMALI-P-0272` | 2028 |
| 2 | `RUPTL:RUPTL-JAMALI-P-0273` | Bedugul | PLTP | 60.0 | -8.2848,115.1713 | planned/Proposed | — | `RUPTL-JAMALI-P-0273` | 2030 |
| 3 | `RUPTL:RUPTL-JAMALI-P-0274` | Bedugul | PLTP | 55.0 | -8.2848,115.1713 | planned/Planned | — | `RUPTL-JAMALI-P-0274` | 2033 |
| 4 | `RUPTL:RUPTL-JAMALI-P-0275` | Bedugul | PLTP | 55.0 | -8.2848,115.1713 | planned/Planned | — | `RUPTL-JAMALI-P-0275` | 2033 |

**Why AMBIGUOUS:**
- 4 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant

**Risk if MERGED:**
- Low risk (evidence supports merge)

**Risk if KEPT SEPARATE:**
- Nama share common stem 'bedugul' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `MERGE_AS_ONE_COMPLEX`

---

## 6. Medco Energi Geothermal

- **Cluster ID**: `GEN-JMB-0131`
- **Region**: jamali
- **Total features**: 6 (0 unnamed)
- **Total capacity**: 110.0 MW
- **Spatial spread**: 2.12 km (max pairwise)
- **Operators**: {'Medco Cahaya Geothermal'}
- **Common name stem**: (no common)

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-JMB-0126` | Medco Energi Geothermal | PLTP | — | -8.0625,114.1565 | existing/existing | — | `way/1218099429` | 2027 |
| 2 | `GEN-JMB-0127` | Medco Energi Geothermal | PLTP | — | -8.0677,114.1750 | existing/existing | — | `way/1218099430` | — |
| 3 | `GEN-JMB-0128` | Medco Energi Geothermal | PLTP | — | -8.0664,114.1728 | existing/existing | — | `way/1218099431` | — |
| 4 | `GEN-JMB-0129` | Medco Energi Geothermal | PLTP | — | -8.0612,114.1705 | existing/existing | — | `way/1218099432` | — |
| 5 | `GEN-JMB-0130` | PLTP Blawan Ijen | PLTP | 110.0 | -8.0566,114.1675 | existing/existing | Medco Cahaya Geothermal | `way/1218099433` | — |
| 6 | `GEN-JMB-0131` | Medco Energi Geothermal | PLTP | — | -8.0505,114.1674 | existing/existing | — | `way/1218099434` | — |

**Why AMBIGUOUS:**
- 6 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant

**Risk if MERGED:**
- Nama tidak converge — merge bisa hide distinct plant identity

**Risk if KEPT SEPARATE:**
- Same operator suggests single plant/field

**Recommended decision (advisory only)**: `KEEP_SEPARATE`

---

## 7. Rantau Dedap (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-SUMATRA-`
- **Region**: sumatra
- **Total features**: 2 (0 unnamed)
- **Total capacity**: 108.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: rantau

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-SMT-0004` | PLTP Rantau Dedap | PLTP | 91.0 | -4.2225,103.3825 | existing/existing | — | `relation/19387721` | — |
| 2 | `RUPTL:RUPTL-SUMATRA-P-0108` | Rantau Dedap (FTP2) | PLTP | 17.0 | -4.2225,103.3825 | planned/Committed | — | `RUPTL-SUMATRA-P-0108` | 2030 |

**Why AMBIGUOUS:**
- 2 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'rantau' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---

## 8. PLTP Lahendong III & IV

- **Cluster ID**: `GEN-SLW-0021`
- **Region**: sulawesi
- **Total features**: 2 (0 unnamed)
- **Total capacity**: 80.0 MW
- **Spatial spread**: 2.48 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: lahendong

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-SLW-0004` | PLTP Lahendong I & II | PLTP | 40.0 | 1.2546,124.8221 | existing/existing | — | `way/101264872` | — |
| 2 | `GEN-SLW-0021` | PLTP Lahendong III & IV | PLTP | 40.0 | 1.2720,124.8361 | existing/existing | — | `way/424006224` | — |

**Why AMBIGUOUS:**
- 2 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant

**Risk if MERGED:**
- Low risk (evidence supports merge)

**Risk if KEPT SEPARATE:**
- Nama share common stem 'lahendong' — mungkin single field yang multi-unit
- Same operator suggests single plant/field

**Recommended decision (advisory only)**: `NEED_MORE_EVIDENCE`

---

## 9. PLTP Ulumbu

- **Cluster ID**: `RUPTL:RUPTL-NTT-P-00`
- **Region**: ntt
- **Total features**: 3 (0 unnamed)
- **Total capacity**: 50.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: ulumbu

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-NTT-0016` | PLTP Ulumbu | PLTP | 10.0 | -8.7261,120.4355 | existing/existing | — | `way/937059867` | — |
| 2 | `RUPTL:RUPTL-NTT-P-0040` | Ulumbu 5 | PLTP | 20.0 | -8.7261,120.4355 | planned/Planned | — | `RUPTL-NTT-P-0040` | 2030 |
| 3 | `RUPTL:RUPTL-NTT-P-0045` | Ulumbu 6 | PLTP | 20.0 | -8.7261,120.4355 | planned/Planned | — | `RUPTL-NTT-P-0045` | 2032 |

**Why AMBIGUOUS:**
- 3 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'ulumbu' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---

## 10. Tangkuban Perahu (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-JAMALI-P`
- **Region**: jamali
- **Total features**: 2 (0 unnamed)
- **Total capacity**: 40.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: tangkuban

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `RUPTL:RUPTL-JAMALI-P-0092` | Tangkuban Perahu (FTP2) | PLTP | 20.0 | -6.7533,107.6079 | planned/Proposed | — | `RUPTL-JAMALI-P-0092` | 2032 |
| 2 | `RUPTL:RUPTL-JAMALI-P-0093` | Tangkuban Perahu (FTP2) | PLTP | 20.0 | -6.7533,107.6079 | planned/Proposed | — | `RUPTL-JAMALI-P-0093` | 2032 |

**Why AMBIGUOUS:**
- 2 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant

**Risk if MERGED:**
- Low risk (evidence supports merge)

**Risk if KEPT SEPARATE:**
- Nama share common stem 'tangkuban' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `MERGE_AS_ONE_COMPLEX`

---

## 11. Sokoria (FTP2)

- **Cluster ID**: `RUPTL:RUPTL-NTT-P-00`
- **Region**: ntt
- **Total features**: 3 (0 unnamed)
- **Total capacity**: 30.0 MW
- **Spatial spread**: 0.00 km (max pairwise)
- **Operators**: {none tagged}
- **Common name stem**: sokoria

| # | Feature ID | Name | Type | MW | Coord | Status | Operator | OSM/RUPTL | COD |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `GEN-NTT-0018` | PLTP Sokoria | PLTP | 8.0 | -8.7930,121.7661 | existing/existing | — | `way/1313835498` | — |
| 2 | `RUPTL:RUPTL-NTT-P-0027` | Sokoria (FTP2) | PLTP | 11.0 | -8.7930,121.7661 | planned/Construction | — | `RUPTL-NTT-P-0027` | 2028 |
| 3 | `RUPTL:RUPTL-NTT-P-0038` | Sokoria (FTP2) | PLTP | 11.0 | -8.7930,121.7661 | planned/Construction | — | `RUPTL-NTT-P-0038` | 2029 |

**Why AMBIGUOUS:**
- 3 named PLTP dalam radius 3.0 km — bisa jadi distinct units atau naming variant
- Mix existing baseline + RUPTL planned features — planned bisa jadi expansion vs entirely new unit

**Risk if MERGED:**
- Planned features punya capacity data terpisah — merge bisa double-count capacity

**Risk if KEPT SEPARATE:**
- Nama share common stem 'sokoria' — mungkin single field yang multi-unit
- Same operator suggests single plant/field
- Spatial spread < 1 km — physically same geothermal field

**Recommended decision (advisory only)**: `PARTIAL_MERGE`

---
