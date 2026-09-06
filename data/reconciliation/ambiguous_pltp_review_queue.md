# AMBIGUOUS PLTP Clusters — Manual Review Queue

Generated: 2026-09-06T23:11:43.108312+00:00

Setiap cluster berikut punya multiple named PLTP dalam radius 3 km — bisa jadi:
(a) plants terpisah dalam satu geothermal field yang sama (mis. Wayang Windu 1 vs 2),
(b) same plant dengan naming variant duplicated di baseline.

Analyst decision per cluster:
- **CONFIRM_MERGE**: consolidate ke satu plant complex → add row ke `plant_complex_curation.csv`
- **KEEP_SEPARATE**: real distinct plants, tidak perlu action (default)
- **REJECT_ONE**: salah satu baseline row incorrect → add REJECT to reconciliation overrides

## AMBIGUOUS (11)

### Cluster: **PLTP Dieng** (jamali) — 8 features, 415.0 MW total
_8 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-JMB-0119` | PLTP Dieng | PLTP | 70.0 | -7.2263, 109.8973 | Geo Dipa Energi | `way/1189922860` |
| `RUPTL:RUPTL-JAMALI-P-0123` | Dieng (FTP2) | PLTP | 55.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0126` | Dieng (FTP2) | PLTP | 35.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0130` | Dieng (FTP2) | PLTP | 55.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0131` | Dieng (FTP2) | PLTP | 55.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0149` | Dieng (FTP2) | PLTP | 55.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0150` | Dieng (FTP2) | PLTP | 55.0 | -7.2263, 109.8973 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0151` | Dieng (FTP2) | PLTP | 35.0 | -7.2263, 109.8973 |  | `` |

### Cluster: **Medco Energi Geothermal** (jamali) — 6 features, 110.0 MW total
_6 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-JMB-0126` | Medco Energi Geothermal | PLTP | — | -8.0625, 114.1565 |  | `way/1218099429` |
| `GEN-JMB-0127` | Medco Energi Geothermal | PLTP | — | -8.0677, 114.1750 |  | `way/1218099430` |
| `GEN-JMB-0128` | Medco Energi Geothermal | PLTP | — | -8.0664, 114.1728 |  | `way/1218099431` |
| `GEN-JMB-0129` | Medco Energi Geothermal | PLTP | — | -8.0612, 114.1705 |  | `way/1218099432` |
| `GEN-JMB-0130` | PLTP Blawan Ijen | PLTP | 110.0 | -8.0566, 114.1675 | Medco Cahaya Geothermal | `way/1218099433` |
| `GEN-JMB-0131` | Medco Energi Geothermal | PLTP | — | -8.0505, 114.1674 |  | `way/1218099434` |

### Cluster: **Bedugul** (jamali) — 4 features, 175.0 MW total
_4 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `RUPTL:RUPTL-JAMALI-P-0272` | Bedugul | PLTP | 5.0 | -8.2848, 115.1713 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0273` | Bedugul | PLTP | 60.0 | -8.2848, 115.1713 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0274` | Bedugul | PLTP | 55.0 | -8.2848, 115.1713 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0275` | Bedugul | PLTP | 55.0 | -8.2848, 115.1713 |  | `` |

### Cluster: **PLTP Lumut Balai** (sumatra) — 4 features, 275.0 MW total
_4 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-SMT-0067` | PLTP Lumut Balai | PLTP | 110.0 | -4.1979, 103.6486 |  | `way/931931104` |
| `RUPTL:RUPTL-SUMATRA-P-0102` | Lumut Balai (FTP2) #2 | PLTP | 55.0 | -4.1979, 103.6486 |  | `` |
| `RUPTL:RUPTL-SUMATRA-P-0115` | Lumut Balai (FTP2) #3 | PLTP | 55.0 | -4.1979, 103.6486 |  | `` |
| `RUPTL:RUPTL-SUMATRA-P-0116` | Lumut Balai (FTP2) #4 | PLTP | 55.0 | -4.1979, 103.6486 |  | `` |

### Cluster: **Baturaden (FTP2)** (jamali) — 3 features, 220.0 MW total
_3 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `RUPTL:RUPTL-JAMALI-P-0138` | Baturaden (FTP2) | PLTP | 110.0 | -7.3148, 109.2295 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0139` | Baturaden (FTP2) | PLTP | 75.0 | -7.3148, 109.2295 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0143` | Baturaden (FTP2) | PLTP | 35.0 | -7.3148, 109.2295 |  | `` |

### Cluster: **PLTP Ulumbu** (ntt) — 3 features, 50.0 MW total
_3 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-NTT-0016` | PLTP Ulumbu | PLTP | 10.0 | -8.7261, 120.4355 |  | `way/937059867` |
| `RUPTL:RUPTL-NTT-P-0040` | Ulumbu 5 | PLTP | 20.0 | -8.7261, 120.4355 |  | `` |
| `RUPTL:RUPTL-NTT-P-0045` | Ulumbu 6 | PLTP | 20.0 | -8.7261, 120.4355 |  | `` |

### Cluster: **PLTP Sokoria** (ntt) — 3 features, 30.0 MW total
_3 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-NTT-0018` | PLTP Sokoria | PLTP | 8.0 | -8.7930, 121.7661 |  | `way/1313835498` |
| `RUPTL:RUPTL-NTT-P-0027` | Sokoria (FTP2) | PLTP | 11.0 | -8.7930, 121.7661 |  | `` |
| `RUPTL:RUPTL-NTT-P-0038` | Sokoria (FTP2) | PLTP | 11.0 | -8.7930, 121.7661 |  | `` |

### Cluster: **Tangkuban Perahu (FTP2)** (jamali) — 2 features, 40.0 MW total
_2 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `RUPTL:RUPTL-JAMALI-P-0092` | Tangkuban Perahu (FTP2) | PLTP | 20.0 | -6.7533, 107.6079 |  | `` |
| `RUPTL:RUPTL-JAMALI-P-0093` | Tangkuban Perahu (FTP2) | PLTP | 20.0 | -6.7533, 107.6079 |  | `` |

### Cluster: **PLTP Rantau Dedap** (sumatra) — 2 features, 108.0 MW total
_2 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-SMT-0004` | PLTP Rantau Dedap | PLTP | 91.0 | -4.2225, 103.3825 |  | `relation/19387721` |
| `RUPTL:RUPTL-SUMATRA-P-0108` | Rantau Dedap (FTP2) | PLTP | 17.0 | -4.2225, 103.3825 |  | `` |

### Cluster: **PLTP Sorik Marapi** (sumatra) — 2 features, 338.0 MW total
_2 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-SMT-0072` | PLTP Sorik Marapi | PLTP | 240.0 | 0.7151, 99.5707 |  | `way/938146456` |
| `RUPTL:RUPTL-SUMATRA-P-0027` | Sorik Marapi (FTP2) | PLTP | 98.0 | 0.7150, 99.5707 |  | `` |

### Cluster: **PLTP Lahendong I & II** (sulawesi) — 2 features, 80.0 MW total
_2 named PLTP within 3.0km — could be distinct or same field_

| Feature ID | Name | Type | MW | Coord | Operator | OSM ID |
| --- | --- | --- | ---: | --- | --- | --- |
| `GEN-SLW-0004` | PLTP Lahendong I & II | PLTP | 40.0 | 1.2546, 124.8221 |  | `way/101264872` |
| `GEN-SLW-0021` | PLTP Lahendong III & IV | PLTP | 40.0 | 1.2720, 124.8361 |  | `way/424006224` |


