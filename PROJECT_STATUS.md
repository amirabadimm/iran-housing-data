# Project Status

Last reviewed: 2026-09-22

## Overall stage

**In progress: rebuilding and extending a previously collected research database.** An initial broad collection, processing, and calculation phase was completed in July. The project was subsequently redesigned so that datasets could be brought into an organized subject-oriented structure through documented collection and processing workflows. Several core datasets have now been rebuilt; the remaining relevant collections must be reviewed and established in the new structure.

The four currently registered packages must not be described as the whole history of the project. Equally, the former 51-dataset catalog must not be described as 51 currently deployed packages. The old and new catalogs use different organization and dataset boundaries.

## Evidence-backed project timeline

Dates below are Git commit dates unless explicitly stated otherwise.

| Phase | Work completed | Evidence |
|---|---|---|
| 22 July: initial CBI collection | Preserved CBI workbooks and prepared 20 housing and 2 macroeconomic datasets; paired Tehran and all-urban observations where appropriate. | `9cca1d6` |
| 22 July: macroeconomic expansion | Added five received macro series covering CPI, FX, GDP, domestic risk-free-rate proxy, and US interest rates. | `32696ad` |
| 22 July: housing-linked securities | Collected mortgage certificates, real-estate funds, developers, and related market indices; calculated a continuous daily mortgage-certificate series. An executable update/rebuild workflow already existed. | `4fb223f` |
| 23 July: SCI collection | Prepared building-permit, Tehran price/rent/transaction, construction-input/material-price, and urban-CPI datasets from SCI workbooks. | `3d93d9f` |
| 23 July: national accounts and FX | Added building investment and real-estate value added at current and constant prices; extended historical USD/IRR coverage. | `7357561` |
| 23 July: derived indicators | Calculated CBI housing/rent inflation and a combined CBI/SCI panel. The historical catalog reached 51 datasets. | `8591fdf` |
| 19–25 August: preparation for further work | Added research articles and standardized source filenames and provenance paths. | `ee7e675`, `aac7557` |
| 31 August: redesign | Replaced the old working-tree structure with subject-oriented packages, data lifecycle layers, and new registries. The status text records 26 August as the redesign date; the change was committed on 31 August. | `9e711d0` |
| 31 August: first rebuilt collection | Registered the monthly CBI monetary-report corpus and implemented the monthly liquidity series; subsequent documentation records the completed series. | `351f7fa`, `bfc2d21` |
| 1 September: SCI reconstruction | Added standardized SCI building-input and urban-CPI datasets in the new structure. | `9a1ec9a` |
| Current local work, documented 19 September | Added the CBI Tehran monthly transaction-price package and curated Power BI input; registered the SCI packages in the current dataset registry. These changes are present locally but were not committed at this review. | Working-tree changes to README, registries, dataset package, and housing builder |

## What the first phase had already achieved

The July collection covered housing supply and construction, investment and finance, rent and land indicators, SCI Tehran market statistics, construction costs, macroeconomic series, and housing-linked securities. It included processing scripts, source-level tables, update commands, and derived indicators—not only downloaded files.

The historical 51-dataset count comprised 27 housing, 17 macroeconomic, 6 securities, and 1 related-industries dataset. It includes derived outputs and is not a count of independent source publications. The old README, catalog, methodology notes, and decisions log can be inspected at `8591fdf`; renamed source paths are visible at `aac7557`.

The redesign removed the previous structure from the tracked working tree while retaining Git history. This does not establish that every old local, ignored source snapshot is still available. Recovery of an old collection should begin by inspecting its historical records and checking the actual source files available today.

## Current registered inventory

| Package | Present output and coverage | Current stage |
|---|---|---|
| CBI monthly monetary and credit data | 240 monthly observations, 1385/01–1404/12; liquidity, money, and quasi-money | Standardized |
| SCI Tehran residential building inputs | Construction-input indices, inflation, and selected material prices; registry latest period 1404-Q4 | Standardized |
| SCI urban CPI | National, group, provincial, and historical urban CPI series from 12 source tables; registry latest period 1405-04 | Standardized |
| CBI Tehran monthly housing transactions | 101 monthly prices, 1395/01–1403/05; source corpus of 87 PDFs and one staging workbook | Curated; Power BI-ready |

The registry's latest period is a package checkpoint, not a claim that every component series has identical coverage. Dataset-specific README files and schemas define the details.

## Current state

- The repository uses a subject-oriented architecture and explicit lifecycle layers.
- The CBI monthly monetary and credit dataset is registered and standardized.
- All 240 source reports are checksum-registered and preserved byte-for-byte.
- The monthly series covers Solar Hijri 1385-01 through 1404-12 without gaps.
- Every observation passes: liquidity = money + quasi-money.
- Both existing SCI standardized datasets are now present in the dataset registry alongside their source and file registrations.
- The CBI Tehran housing transaction-price dataset is checksum-registered (87 official PDFs and one staging workbook), independently validated, and published as a 101-row curated CSV for Power BI. The two adjacent-report revision disagreements remain documented. No separate Power BI mart is needed for this single dataset.

## Remaining work and priorities

The CBI housing corpus ends at 1403/05. Additional months require new official reports, preserved source registration, and a reviewed extraction. The SCI datasets remain standardized rather than curated, and their detailed variable-dictionary entries remain to be authored from source definitions.

1. Review the historical catalog against the current registry and identify which previous collections are still required. Do not assume an automatic one-to-one migration of all 51 historical entries.
2. Rebuild and register the remaining relevant housing supply, rent/land, investment, finance, securities, and macroeconomic collections. Their historical existence is established; their publication in the new structure is not yet established by the current registry.
3. Use `Notes.txt` as a historical list of requested coverage updates and definition questions, including housing/land/rent, permits, interest rates, GDP, unemployment, and housing-linked market series. Verify each item against current sources before declaring it complete. The notes are not a current completion checklist.
4. Maintain the four established packages and complete the SCI variable definitions and any requested curation.
5. Extend housing-price coverage when additional official evidence is available. A housing-price refresh currently rebuilds the documented period from existing sources; it does not automatically obtain new monthly reports.
6. Undertake further modeling or visualization only for an explicit research question.

## Reading and updating this status

README summarizes the project trajectory; this file owns the detailed historical/current distinction; `metadata/dataset_registry.csv` lists the packages established in the new structure. Dataset README files own source, coverage, and refresh instructions. When another collection is rebuilt, update those records together and state whether it is a historical collection being re-established or a genuinely new addition.

Useful read-only history commands:

```powershell
git show 8591fdf:PROJECT_STATUS.md
git show 8591fdf:metadata/data_catalog.csv
git show 8591fdf:docs/decisions_log.md
git show aac7557:README.md
git show 9e711d0:PROJECT_STATUS.md
git diff -- README.md PROJECT_STATUS.md metadata/dataset_registry.csv
```
