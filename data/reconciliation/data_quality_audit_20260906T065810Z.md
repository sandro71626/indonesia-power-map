# Data Quality Audit — 2026-09-06T06:58:10.779985+00:00

Cross-region inspection of reconciliation results (gen/sub/trm).
Cases classified into 6 categories; each finding lists suggested
action (algorithmic fix, manual override, or no-action).

## Summary

| Category | Total |
| --- | ---: |
| EXTRACTOR_ISSUE | 33 |
| FALSE_POSITIVE | 75 |
| FALSE_NEGATIVE | 440 |
| AMBIGUOUS_DATA | 19 |
| GEOCODING_ISSUE | 8 |
| GENUINELY_UNMATCHED | 285 |

## Per region

| Region | EXTRACTOR | FALSE_POS | FALSE_NEG | AMBIGUOUS | GEOCODING | GENUINELY_UNMATCHED |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| jamali | 10 | 53 | 200 | 14 | 1 | 127 |
| sumatra | 10 | 9 | 160 | 1 | 1 | 79 |
| kalimantan | 8 | 4 | 47 | 0 | 1 | 30 |
| sulawesi | 4 | 5 | 24 | 1 | 1 | 43 |
| maluku | 1 | 0 | 3 | 2 | 1 | 2 |
| papua | 0 | 0 | 4 | 0 | 1 | 1 |
| ntb | 0 | 1 | 1 | 1 | 1 | 3 |
| ntt | 0 | 3 | 1 | 0 | 1 | 0 |

## EXTRACTOR_ISSUE (33)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| sulawesi | trm | `RUPTL-SULAWESI-T-0109` | GITET Kolaka Smelter → GITET Kendari | 420.0 | Length 420.0 km outlier — likely aggregate row or PDF typo | Verify PDF page, potentially IGNORE_RUPTL_ROW |
| jamali | trm | `RUPTL-JAMALI-T-0209` | Tanjung Jati → Rembang | 340.0 | Length 340.0 km outlier — likely aggregate row or PDF typo | Verify PDF page, potentially IGNORE_RUPTL_ROW |
| maluku | trm | `RUPTL-MALUKU-T-0013` | GI Malifut → GI Tobelo | 240.0 | Length 240.0 km outlier — likely aggregate row or PDF typo | Verify PDF page, potentially IGNORE_RUPTL_ROW |
| jamali | trm | `RUPTL-JAMALI-T-0401` | Trenggalek Baru → PLTU Pacitan | 84.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| jamali | trm | `RUPTL-JAMALI-T-0174` | Dieng → Batang New | 71.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| sumatra | trm | `RUPTL-SUMATRA-T-0058` | Kuala → Binjai | 70.0 | Stated 70.0 km < straight-line 110.84 km (impossible) | Check RUPTL PDF row — likely decimal or unit parse bug |
| jamali | trm | `RUPTL-JAMALI-T-0054` | Rangkasbitung Baru → Saketi | 67.6 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| jamali | trm | `RUPTL-JAMALI-T-0170` | Batang New → Comal | 60.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| jamali | trm | `RUPTL-JAMALI-T-0342` | Magetan Baru → Dolopo Baru | 50.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| sulawesi | trm | `RUPTL-SULAWESI-T-0001` | Tanjung Merah → Bitung Baru | 40.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| jamali | trm | `RUPTL-JAMALI-T-0157` | Ungaran → Ampel / Tuntang | 22.0 | Stated 22.0 km < straight-line 39.64 km (impossible) | Check RUPTL PDF row — likely decimal or unit parse bug |
| jamali | trm | `RUPTL-JAMALI-T-0372` | Ngoro → New Porong | 20.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| sulawesi | gen | `RUPTL-SULAWESI-P-0004` | Sulbagut (Kuota) Tersebar Tambahan | 20.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0164` | Kalimantan (Kuota) Tersebar | 17.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0017` | Kalimantan (Kuota) Tersebar | 17.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0175` | Kalimantan (Kuota) Tersebar | 16.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0028` | Kalimantan (Kuota) Tersebar | 16.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sulawesi | trm | `RUPTL-SULAWESI-T-0073` | GITET Daya Baru → Daya Baru | 14.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| jamali | trm | `RUPTL-JAMALI-T-0132` | Sukatani New → Jababeka II / Pamahan | 11.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| sumatra | gen | `RUPTL-SUMATRA-P-0172` | Kalimantan (Kuota) Tersebar | 10.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0219` | Kalimantan (Kuota) Tersebar | 10.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0025` | Kalimantan (Kuota) Tersebar | 10.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0072` | Kalimantan (Kuota) Tersebar | 10.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0159` | Kalimantan (Kuota) Tersebar | 7.5 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0012` | Kalimantan (Kuota) Tersebar | 7.5 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| jamali | trm | `RUPTL-JAMALI-T-0050` | Cikupa New → Curug Switching | 6.0 | Generic endpoint name → cannot geocode reliably | Skip (already skipped in phase 2) OR improve extractor Inc.- |
| sumatra | gen | `RUPTL-SUMATRA-P-0176` | Kalimantan (Kuota) Tersebar | 5.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0029` | Kalimantan (Kuota) Tersebar | 5.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0173` | Kalimantan (Kuota) Tersebar | 4.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0026` | Kalimantan (Kuota) Tersebar | 4.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0023` | Simeulue (Kuota) Tersebar | 3.0 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| sumatra | gen | `RUPTL-SUMATRA-P-0177` | Kalimantan (Kuota) Tersebar | 1.2 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0030` | Kalimantan (Kuota) Tersebar | 1.2 | Type = '?' (extractor couldn't infer PLT category) | Extend name_stem heuristics or update PLANT_LABEL |

## FALSE_POSITIVE (75)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| sumatra | sub | `RUPTL-SUMATRA-GI-0248 ↔ GI-SMT-0195` | Sribawono ↔ Sribawono | 3000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0065 ↔ GI-JMB-0092` | Cikupa ↔ Cikupa | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0086 ↔ GI-JMB-0091` | Cikande ↔ Cikande | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0314 ↔ GI-JMB-0271` | Ubrug ↔ Ubrug | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0477 ↔ GI-JMB-0149` | Bogor X ↔ Bogor Baru | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0551 ↔ GI-JMB-0352` | Weleri ↔ Weleri | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0562 ↔ GI-JMB-0328` | Purwodadi ↔ Purwodadi | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0594 ↔ GI-JMB-0333` | Rembang ↔ Rembang | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0728 ↔ GI-JMB-0499` | Waru ↔ Waru | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0786 ↔ GI-JMB-0427` | New Ngoro ↔ Ngoro | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0796 ↔ GI-JMB-0485` | Surabaya Selatan ↔ Surabaya Selatan | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0832 ↔ GI-JMB-0499` | Waru ↔ Waru | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0110 ↔ GI-KLM-0077` | GITET Embalut ↔ GI Embalut | 1000.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0042 ↔ GI-SMT-0058` | Galang ↔ Galang | 502.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0694 ↔ GI-JMB-0471` | Bangil ↔ Bangil | 500.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0109 ↔ GI-KLM-0074` | GITET Balikpapan ↔ GI New Balikpapan | 500.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0247 ↔ GI-SMT-0195` | Sribawono ↔ Sribawono | 252.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0063 ↔ GI-SLW-0081` | GITET Malili ↔ Malili | 252.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0943 ↔ GI-JMB-0436` | Blimbing Baru ↔ Blimbing | 180.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0062 ↔ GI-JMB-0048` | Mampang Baru II ↔ Mampang Baru | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0202 ↔ GI-JMB-0270` | Telukjambe II ↔ Telukjambe | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0207 ↔ GI-JMB-0142` | Babakan Baru ↔ Babakan | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0242 ↔ GI-JMB-0246` | Rengasdengklok Baru ↔ Rengasdengklok | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0280 ↔ GI-JMB-0216` | Malangbong Baru ↔ Malangbong | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0294 ↔ GI-JMB-0258` | Sumedang Baru ↔ Sumedang | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0298 ↔ GI-JMB-0165` | Cibinong II ↔ Cibinong | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0323 ↔ GI-JMB-0210` | Kracak Baru ↔ Kracak | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0334 ↔ GI-JMB-0235` | Peruri II ↔ Peruri | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0340 ↔ GI-JMB-0244` | Rancaekek II ↔ Rancaekek | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0474 ↔ GI-JMB-0149` | Bogor X ↔ Bogor Baru | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0762 ↔ GI-JMB-0406` | Caruban Baru ↔ Caruban | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0785 ↔ GI-JMB-0409` | Magetan Baru ↔ Magetan | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0787 ↔ GI-JMB-0427` | New Ngoro ↔ Ngoro | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0868 ↔ GI-JMB-0483` | Sidoarjo II ↔ Sidoarjo | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0993 ↔ GI-JMB-0517` | Pemecutan Kelod II ↔ Pemecutan Kelod | 120.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0024 ↔ GI-JMB-0054` | Muara Karang New ↔ Muara Karang Baru | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0061 ↔ GI-JMB-0065` | Pondok Kelapa II ↔ Pondok Kelapa | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0066 ↔ GI-JMB-0092` | Cikupa New ↔ Cikupa | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0088 ↔ GI-JMB-0091` | Cikande New ↔ Cikande | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0191 ↔ GI-JMB-0238` | Pelabuhan Ratu Baru ↔ PLTU Pelabuhan Rat | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0253 ↔ GI-JMB-0171` | Cikalong ↔ Cikalong | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0277 ↔ GI-JMB-0211` | Kuningan Baru ↔ Kuningan | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0587 ↔ GI-JMB-0349` | PLTP Ungaran ↔ Ungaran | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0699 ↔ GI-JMB-0471` | Bangil New ↔ Bangil | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0729 ↔ GI-JMB-0499` | Waru New ↔ Waru | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0756 ↔ GI-JMB-0463` | PLTU Paiton II ↔ Paiton | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0772 ↔ GI-JMB-0407` | Dolopo Baru ↔ Dolopo | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0858 ↔ GI-JMB-0414` | Trenggalek Baru ↔ Trenggalek | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0941 ↔ GI-JMB-0470` | Sukorejo ↔ Sukorejo | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0947 ↔ GI-JMB-0464` | Pier II ↔ Pier | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0997 ↔ GI-JMB-0519` | New Sanur ↔ Sanur | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0029 ↔ GI-KLM-0045` | Batulicin Baru ↔ GI BATULICIN | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0001 ↔ GI-SLW-0003` | Bitung Baru ↔ Bitung | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0002 ↔ GI-SLW-0003` | Bitung Baru ↔ Bitung | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| ntb | sub | `RUPTL-NTB-GI-0006 ↔ GI-NTB-0011` | Switching Mataram ↔ Mataram | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| ntt | sub | `RUPTL-NTT-GI-0001 ↔ GI-NTT-0005` | Naibonat ↔ Naibonat | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| ntt | sub | `RUPTL-NTT-GI-0015 ↔ GI-NTT-0007` | Kefamenanu ↔ Kefamenanu | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| ntt | sub | `RUPTL-NTT-GI-0016 ↔ GI-NTT-0008` | Atambua ↔ Atambua | 60.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0022 ↔ GI-KLM-0004` | Kota Baru 2 ↔ GI KOTA BARU | 30.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0031 ↔ GI-SLW-0038` | Moutong ↔ Moutong | 30.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0038 ↔ GI-SLW-0037` | Bangkir ↔ Bangkir | 30.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0143 ↔ GI-SMT-0096` | LP Ngenang ↔ Ngenang | 9.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0144 ↔ GI-SMT-0096` | Ngenang ↔ Ngenang | 9.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0808 ↔ GI-JMB-0495` | Sawahan II ↔ Sawahan | 8.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0107 ↔ GI-JMB-0098` | Curug Switching ↔ Curug | 6.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0250 ↔ GI-JMB-0171` | Cikalong ↔ Cikalong | 4.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0156 ↔ GI-SMT-0096` | LP Ngenang ** ↔ Ngenang | 4.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0157 ↔ GI-SMT-0096` | Ngenang ** ↔ Ngenang | 4.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0249 ↔ GI-SMT-0207` | LP Ketapang ↔ Ketapang | 4.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0035 ↔ GI-JMB-0008` | Cawang ↔ Cawang | 2.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0556 ↔ GI-JMB-0352` | Weleri II ↔ Weleri | 2.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0718 ↔ GI-JMB-0437` | PLTS Karangkates ↔ Karangkates | 2.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| sumatra | sub | `RUPTL-SUMATRA-GI-0214 ↔ GI-SMT-0142` | PLTP Sungai Penuh ↔ Sungai Penuh | 2.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0032 ↔ GI-JMB-0074` | PLTSA Sunter ↔ Sunter | 1.0 | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |
| jamali | sub | `RUPTL-JAMALI-GI-0827 ↔ GI-JMB-0405` | Blitar ↔ Blitar Baru | — | Naming variant — baseline exists, RUPTL flagged as NEW build | Override FORCE_MATCH to merge, or REJECT_MATCH if genuinely  |

## FALSE_NEGATIVE (440)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| jamali | gen | `RUPTL-JAMALI-P-0263` | Isolated Jatim | 7868.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0201` | Muara Juloi | 3401.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0054` | Muara Juloi | 3401.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0266` | Karawang | 2000.0 | High-MVA NEW_BUILD (500/150 kV, 2000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0800` | Tanjung Awar- Awar | 1500.0 | High-MVA NEW_BUILD (500/150 kV, 1500.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0087` | Peranap (Konverter)* | 1500.0 | High-MVA NEW_BUILD (500 * kV, 1500.0 MVA) — check for baseline naming  | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0091` | Peranap (Konverter)* | 1500.0 | High-MVA NEW_BUILD (500 * kV, 1500.0 MVA) — check for baseline naming  | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0139` | Peranap (Konverter) | 1500.0 | High-MVA NEW_BUILD (500 DC kV, 1500.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0140` | Rempang/Tanjung Gundap (Konverter) | 1500.0 | High-MVA NEW_BUILD (500 DC kV, 1500.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0147` | Rempang/Tanjung Gundap (Konverter)* | 1500.0 | High-MVA NEW_BUILD (500 kV, 1500.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0149` | Rempang/Tanjung Gundap (Konverter)** | 1500.0 | High-MVA NEW_BUILD (500 kV, 1500.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0003` | Jawa-9 | 1000.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0004` | Jawa-10 | 1000.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0025` | Jawa-5 | 1000.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0073` | Jawa-4 | 1000.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0106` | Jawa-6 | 1000.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0036` | Rasuna Said | 1000.0 | High-MVA NEW_BUILD (275/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0216` | Cibatu Baru II / Sukatani | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0260` | KIIC | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0304` | Karawang | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0317` | Citeurup | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0498` | Ampel / Tuntang | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0527` | Batang / Pemalang | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0545` | Rawalo / Kesugihan | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0590` | Tambak Lorok | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0731` | Watudodol / Kalipuro | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0744` | Madiun | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0779` | Kalanganyar | 1000.0 | High-MVA NEW_BUILD (500/275 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0833` | Kalanganyar | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0994` | Antosari / Gilimanuk | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-1015` | Antosari / Gilimanuk | 1000.0 | High-MVA NEW_BUILD (500/150 kV, 1000.0 MVA) — check for baseline namin | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0332` | GITET KFI | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0376` | GITET Embalut | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0377` | GITET IKN 1 | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0381` | GITET KFI | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0066` | GITET KFI | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0111` | GITET IKN 1 | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0115` | GITET KFI | 1000.0 | High-MVA NEW_BUILD (500 kV, 1000.0 MVA) — check for baseline naming va | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0188` | Jawa-3 | 800.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0293` | Mempawah/Senggiring (Arah PLTG/GU Kalbar | 722.0 | High-MVA NEW_BUILD (150 kV, 722.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0027` | Mempawah/Senggiring (Arah PLTG/GU Kalbar | 722.0 | High-MVA NEW_BUILD (150 kV, 722.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0329` | Pangkalan Bun (Arah PLTG/GU Kalteng) Jum | 602.0 | High-MVA NEW_BUILD (150 kV, 602.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0063` | Pangkalan Bun (Arah PLTG/GU Kalteng) Jum | 602.0 | High-MVA NEW_BUILD (150 kV, 602.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0093` | Jambi-1 | 600.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0094` | Jambi-2 | 600.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sulawesi | gen | `RUPTL-SULAWESI-P-0028` | Sulbagsel 3 | 600.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sulawesi | gen | `RUPTL-SULAWESI-P-0053` | Sulbagsel 3 | 600.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0044` | Inalum/Kuala Tanjung* | 503.0 | High-MVA NEW_BUILD (500/275 kV, 503.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0148` | Rempang/Tanjung Gundap | 503.0 | High-MVA NEW_BUILD (500/150 kV, 503.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0001` | GITET Sumatera 2 | 501.0 | High-MVA NEW_BUILD (500/275 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0041` | Rantau Prapat | 501.0 | High-MVA NEW_BUILD (500/275 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0043` | Rantau Prapat | 501.0 | High-MVA NEW_BUILD (500/275 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0051` | Medan Barat | 501.0 | High-MVA NEW_BUILD (275/150 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0053` | Medan Barat | 501.0 | High-MVA NEW_BUILD (275/150 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0084` | Peranap | 501.0 | High-MVA NEW_BUILD (500/150 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0217` | Palembang-1/Palembang Utara/Kenten | 501.0 | High-MVA NEW_BUILD (275/150 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0223` | Palembang-1/Palembang Utara/Kenten | 501.0 | High-MVA NEW_BUILD (275/150 kV, 501.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0026` | Jawa-Bali-7 | 500.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0089` | Suralaya Lama | 500.0 | High-MVA NEW_BUILD (500/150 kV, 500.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0168` | Cibatu Baru / Deltamas | 500.0 | High-MVA NEW_BUILD (500/150 kV, 500.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| jamali | sub | `RUPTL-JAMALI-GI-0169` | Cibatu Baru / Deltamas | 500.0 | High-MVA NEW_BUILD (500/150 kV, 500.0 MVA) — check for baseline naming | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0053` | Sumatera Pump Storage -1 | 500.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0375` | GITET Balikpapan | 500.0 | High-MVA NEW_BUILD (500 kV, 500.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| sumatra | sub | `RUPTL-SUMATRA-GI-0406` | GITET Tj. Selor | 500.0 | High-MVA NEW_BUILD (500 kV, 500.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| kalimantan | sub | `RUPTL-KALIMANTAN-GI-0140` | GITET Tj. Selor | 500.0 | High-MVA NEW_BUILD (500 kV, 500.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0269` | Jawa-Bali-2 | 450.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0270` | Jawa-Bali-3 | 450.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0271` | Jawa-Bali-6 | 450.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0206` | Kalimantan | 400.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| kalimantan | gen | `RUPTL-KALIMANTAN-P-0059` | Kalimantan | 400.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0092` | Merangin | 350.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| maluku | gen | `RUPTL-MALUKU-P-0037` | PLTGU/ G/MG | 350.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| maluku | gen | `RUPTL-MALUKU-P-0052` | Halmahera 2 | 350.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0016` | PLTS BESS Sumatera 2 | 302.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0083` | Kolaka Smelter | 302.0 | High-MVA NEW_BUILD (150 kV, 302.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| sulawesi | sub | `RUPTL-SULAWESI-GI-0084` | Andowia (Sisi 150 kV GITET Andowia) | 302.0 | High-MVA NEW_BUILD (150 kV, 302.0 MVA) — check for baseline naming var | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0076` | Jawa-Bali-5 | 300.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| jamali | gen | `RUPTL-JAMALI-P-0215` | Jawa-Bali-4 | 300.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0048` | Sumut-14) | 300.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |
| sumatra | gen | `RUPTL-SUMATRA-P-0131` | Sumbagsel 2 | 300.0 | High-MW planned without baseline match — check for naming variant | Manual review + potential FORCE_MATCH |

_(+360 more, see per-region reports)_

## AMBIGUOUS_DATA (19)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| sumatra | trm | `RUPTL-SUMATRA-T-0182` | Sribawono** → Ketapang** | 200.0 | Ratio 4.28× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| maluku | trm | `RUPTL-MALUKU-T-0012` | GI Jailolo → GI Malifut | 160.0 | Ratio 4.12× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| maluku | trm | `RUPTL-MALUKU-T-0011` | GI Jailolo → GI Sofifi | 160.0 | Ratio 3.76× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| sulawesi | trm | `RUPTL-SULAWESI-T-0063` | Punagaya → Bantaeng switching | 132.0 | Ratio 3.0× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| ntb | trm | `RUPTL-NTB-T-0001` | GI Jeranjang → GI Sekotong | 57.0 | Ratio 3.47× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0307` | Waru → Krian | 45.0 | Ratio 3.89× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0201` | Ungaran → Jelok | 40.0 | Ratio 3.16× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | gen | `RUPTL-JAMALI-P-0052` | Wayang Windu (FTP2) | 30.0 | 8 kandidat IPM PLTP dalam 15.0 km — butuh manual pick | Manual review needed — multiple candidates in threshold |
| jamali | trm | `RUPTL-JAMALI-T-0005` | Priok → Muara Tawar | 30.0 | Ratio 3.01× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0360` | Rungkut → Surabaya Selatan | 22.0 | Ratio 3.76× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0025` | Rasuna Said → Cawang | 20.0 | Ratio 4.94× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0004` | Kebon Jeruk → Duri Kosambi | 20.0 | Ratio 3.03× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0019` | Petukangan → PLTD Senayan | 19.0 | Ratio 4.47× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0394` | Wonokromo → Kupang | 16.0 | Ratio 4.18× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | gen | `RUPTL-JAMALI-P-0060` | Cibuni (FTP2) | 10.0 | 3 kandidat IPM PLTP dalam 15.0 km — butuh manual pick | Manual review needed — multiple candidates in threshold |
| jamali | trm | `RUPTL-JAMALI-T-0395` | Undaan → Simpang | 10.0 | Ratio 6.84× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0393` | Undaan → Kenjeran | 10.0 | Ratio 3.14× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0002` | Budi Kemuliaan → Kebon Sirih | 4.0 | Ratio 3.0× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |
| jamali | trm | `RUPTL-JAMALI-T-0020` | Manggarai → Gedung Pola | 3.5 | Ratio 3.44× — cable routing atau endpoint gazetteer imprecise | Manual verify, may be legitimate SKTT routing |

## GEOCODING_ISSUE (8)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| jamali | gen | `(bulk)` | 234 planned generators fallback ke provi | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| sumatra | gen | `(bulk)` | 213 planned generators fallback ke provi | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| kalimantan | gen | `(bulk)` | 70 planned generators fallback ke provin | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| sulawesi | gen | `(bulk)` | 49 planned generators fallback ke provin | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| maluku | gen | `(bulk)` | 36 planned generators fallback ke provin | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| papua | gen | `(bulk)` | 49 planned generators fallback ke provin | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| ntb | gen | `(bulk)` | 6 planned generators fallback ke provinc | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |
| ntt | gen | `(bulk)` | 34 planned generators fallback ke provin | — | Gazetteer match miss → coord = province centroid + jitter | Build additional gazetteer (BIG shapefile, PLN annual report |

## GENUINELY_UNMATCHED (285)

| Region | Kind | ID | Name | MW/km | Reason | Action |
| --- | --- | --- | --- | ---: | --- | --- |
| jamali | gen | `GEN-JMB-0022` | PLTU Tanjung Jati B | 4640.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0044` | Unit Pembangkit Listrik Paiton | 4608.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0058` | PLTU Suralaya | 4025.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| maluku | gen | `GEN-MLK-0013` | PLTU Weda Bay | 4000.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `GEN-SLW-0070` | PLTU Labota | 3360.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0069` | PLTGU Priok | 2720.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0036` | PLTGU Muara Tawar | 2593.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0016` | PLTU Cilacap | 2121.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `GEN-SLW-0058` | PLTU IMIP Morowali | 2080.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0098` | PLTGU Tambak Lorok | 2014.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0057` | PLTU Jawa 7 | 2000.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0083` | PLTU Batang | 2000.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0075` | PLTGU Gresik | 1924.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0015` | PLTGU Muara Karang | 1908.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `GEN-SLW-0061` | PLTU Delong Nickel Phase II | 1840.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0103` | PLTGU Jawa-1 | 1760.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0015` | Sumbagut (kuota ISJ) tersebar2) | 1450.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0045` | PLTGU Grati | 1424.7 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `GEN-SMT-0118` | PLTU Sumsel 8 | 1320.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0047` | PLTU Banten Lontar | 1260.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0110` | Sumatera Hybrid1) | 1200.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0064` | PLTU Palabuhan Ratu | 1050.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0081` | PLTA Cirata | 1008.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0035` | PLTU Indramayu | 990.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `RUPTL-JAMALI-P-0108` | Jawa Barat (Kuota) Tersebar X | 977.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0111` | Jawa Barat (Kuota) Tersebar XI | 977.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0114` | Jawa Barat (Kuota) Tersebar XII | 977.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0100` | PLTGU Jawa-2 Power Project | 800.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0052` | Panas Bumi Sumatera (kuota ISJ) Tersebar | 800.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sulawesi | gen | `RUPTL-SULAWESI-P-0020` | Sulbagsel (Kuota) Tersebar Tambahan II | 800.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sulawesi | gen | `RUPTL-SULAWESI-P-0058` | Sulbagsel (Kuota) Tersebar Tambahan II | 800.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0162` | Jawa Tengah (Kuota) Tersebar X | 786.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0167` | Jawa Tengah (Kuota) Tersebar XI | 786.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0169` | Jawa Tengah (Kuota) Tersebar XII | 786.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0170` | Jawa Tengah (Kuota) Tersebar XIII | 786.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0072` | PLTGU Jababeka | 755.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `GEN-SMT-0001` | PLTU Indah Kiat (multi-unit) Perawang | 755.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0071` | PLTGU Cilegon | 740.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `GEN-SMT-0008` | PLTGU Belawan | 720.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0076` | PLTU Tanjung Awar-Awar | 700.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0019` | PLTU Cirebon Unit 1 | 660.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0091` | PLTU Cirebon Unit 2 | 660.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0097` | PLTU Jawa Tengah 2 | 660.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0037` | PLTU Pacitan | 630.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0043` | PLTU Rembang | 630.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0070` | PLTU Banten Serang | 625.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `RUPTL-JAMALI-P-0038` | Jawa-Bali (Kuota) Tersebar IV | 600.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0034` | PLTU Labuan Banten | 600.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `RUPTL-SULAWESI-P-0021` | Sulbagsel (Kuota) Tersebar Tambahan II | 600.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sulawesi | gen | `RUPTL-SULAWESI-P-0059` | Sulbagsel (Kuota) Tersebar Tambahan II | 600.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `RUPTL-SUMATRA-P-0014` | Sumbagut (Kuota) Tersebar1) | 561.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0236` | Jawa Timur (Kuota) Tersebar XII | 525.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0251` | Jawa Timur (Kuota) Tersebar XIII | 525.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `GEN-SMT-0036` | PLTU Pangkalan Susu | 440.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | trm | `RUPTL-SUMATRA-T-0037` | Galang → Rantau Prapat | 440.0 | Length 440.0 km — verify inter-island / EHV route | Likely legitimate (Bali crossing, EHV inter-region), no acti |
| jamali | gen | `RUPTL-JAMALI-P-0242` | BESS Smoothing Tersebar | 400.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0023` | PLTU 400 MW PT Krakatau Chandra Energi | 400.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0012` | Sumatera (kuota) tersebar1) | 400.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `GEN-SMT-0105` | PLTU IPP Nagan Raya | 400.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `RUPTL-SULAWESI-P-0022` | Sulbagsel (Kuota) Tersebar Tambahan II | 400.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sulawesi | gen | `GEN-SLW-0003` | PLTA Poso-2 | 395.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| jamali | gen | `GEN-JMB-0050` | PLTU Celukan Bawang | 380.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0087` | Sumbagselteng (kuota ISJ) tersebar2) | 350.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `GEN-SMT-0124` | PLTA Kerinci | 350.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sulawesi | gen | `GEN-SLW-0098` | PLTU Ambunu | 350.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| kalimantan | trm | `RUPTL-KALIMANTAN-T-0001` | Sandai → Tayan | 332.0 | Length 332.0 km — verify inter-island / EHV route | Likely legitimate (Bali crossing, EHV inter-region), no acti |
| jamali | gen | `GEN-JMB-0027` | PLTDG Pesanggaran | 325.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0040` | Sumatera (Kuota) Tersebar1) | 325.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `GEN-SMT-0094` | PLTA Tangga | 317.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| kalimantan | trm | `RUPTL-KALIMANTAN-T-0112` | Muara Wahau → Tanjung Redeb | 304.0 | Length 304.0 km — verify inter-island / EHV route | Likely legitimate (Bali crossing, EHV inter-region), no acti |
| jamali | gen | `RUPTL-JAMALI-P-0030` | Jawa-Bali (Kuota) Tersebar III | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0034` | Jawa-Bali (Kuota) Tersebar II | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0035` | Jawa-Bali (Kuota) Tersebar IIIA | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `RUPTL-JAMALI-P-0252` | BESS Jawa- Bali (Kuota) Tersebar IIID | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| jamali | gen | `GEN-JMB-0118` | PLTU Asahimas Chemical | 300.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `RUPTL-SUMATRA-P-0111` | Sumatera Hybrid1) | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `RUPTL-SUMATRA-P-0242` | Kalseltengtimra (Kuota) Tersebar | 300.0 | Planned aggregate/kuota placeholder — expected unmatched | No action (this is expected) |
| sumatra | gen | `GEN-SMT-0019` | PLTU Paluh Kurau | 300.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `GEN-SMT-0043` | PLTU Simpang Belimbing | 300.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |
| sumatra | gen | `GEN-SMT-0073` | PLTGU Cogeneration North Duri | 300.0 | High-MW OSM plant without RUPTL entry — likely pre-2025 existing not i | No action (existing outside RUPTL scope) |

_(+205 more, see per-region reports)_
