# Iran Housing Research Data Repository

This repository supports flexible collection and management of housing, economic, stock-market, and related-industry data for research on Iran. Data preservation comes before analysis. Cleaning, merging, visualization, and statistical analysis begin only when a specific research need or professor request justifies them.

## Data flow

```text
source -> incoming -> inspection and registration -> raw
       -> optional cleaned -> optional derived -> optional task deliverable
```

A dataset may stop at any valid stage. It does not need cleaned, derived, or analytical versions.

## Main directories

- `data/incoming/`: temporary intake and review area.
- `data/raw/`: unchanged original source files; never overwrite them.
- `data/cleaned/`: documented standardized copies created only when needed.
- `data/derived/`: merges, indicators, aggregates, and task-specific datasets.
- `metadata/`: dataset catalog, sources, variables, cleaning history, and issues.
- `docs/`: workflow and research documentation.
- `src/`: reusable code added only when real work requires it.
- `tasks/`: active, completed, and template-based professor requests.
- `notebooks/`: exploration and task-specific notebooks.
- `outputs/`: generated tables, figures, datasets, and reports.
- `tests/`: tests for reusable code.

The initial categories are `macro`, `housing`, `stocks`, and `related_industries`. Add a lowercase snake_case category and update metadata when the research expands; no architecture redesign is required.

## Current CBI collection

The first registered collection contains 18 manually exported Excel workbooks from the Central Bank of Iran [Time Series Database](https://tsdview.cis.cbi.ir/single-data), generated on Solar Hijri date 1405/04/31.

- Unchanged copies are stored under `data/raw/housing/cbi_tsd_14050431/` and `data/raw/macro/cbi_tsd_14050431/`.
- Thirteen housing indicators are standardized under `data/cleaned/housing/cbi_urban_tehran_pairs/`. Each CSV keeps all-urban and Tehran observations side by side by quarter.
- Seven housing datasets without an all-urban/Tehran pair are under `data/cleaned/housing/cbi_non_geographic/`, including one combined dataset for large-, medium-, and small-city rent indices.
- Macro datasets are organized by economic domain under `data/cleaned/macro/`, independent of their source or processing history.
- Cleaned coverage begins no earlier than 1370 and ends at each source series' latest actual observation. Most quarterly housing series currently end at 1404-Q2; this is not extended with estimated values.
- Gray source cells are retained as Boolean preliminary flags. No values were interpolated, aggregated, inflation-adjusted, or converted to different units.

Rebuild the registered outputs from the incoming files with:

```powershell
python src\common\process_cbi_tsd_exports.py
```

See `metadata/data_catalog.csv` for dataset-level coverage and provenance, `metadata/variable_dictionary.csv` for variables, and `metadata/cleaning_log.csv` for transformations.

The Excel workbooks—not filenames, earlier documentation, or translated labels—are the authority for dataset identity. Exact Persian report titles, dataset paths, labels, units, reported ranges, frequencies, and observation counts are recorded in `metadata/excel_series_inventory.csv`. Cleaned values retain those source definitions without English renaming.

## Current Statistical Center of Iran collection

Eleven Persian SCI workbooks from the official [statistical-information portal](https://amar.org.ir/statistical-information) are preserved byte-for-byte under dated provider folders in `data/raw/`. They produce nine standardized long-form datasets covering building permits, Tehran housing prices/rents/transactions, Tehran construction-input indices and selected material prices, and national/provincial/historical urban CPI. Workbook and sheet coverage is auditable in `metadata/sci_excel_inventory.csv`; source missing markers are retained and no values are interpolated, rebased, or spliced.

## Imported standardized macro collection

Five standardized macro CSVs were received from another user project on 2026-07-22:

- Iran total CPI and inflation, monthly, 1399-01 through 1404-12;
- free-market USD/IRR rate, daily available-market observations, 1399/01/05 through 1405/04/21;
- Iran real and nominal GDP at basic prices, quarterly, 1399-Q1 through 1404-Q4;
- annualized اخزا risk-free-rate proxy, monthly, 1399-01 through 1404-12;
- US Federal Funds Effective Rate aligned approximately to Jalali months, 1399-01 through 1404-12.

The received files already conformed to the documented CSV standard. They are preserved exactly under `data/raw/macro/external_data_analysis_20260722/` and copied byte-for-byte into the appropriate economic-domain folders under `data/cleaned/macro/` after validation. No value, date, key, field, unit, or missing value was changed. See the catalog and `docs/methodology_notes.md` for upstream provenance limitations.

Revalidate and recreate missing cleaned copies with:

```powershell
.\.venv\Scripts\python.exe src\macro\register_standardized_macro_csvs.py
```

## Tehran securities-market collection

Housing-linked market data retrieved on 2026-07-22 are standardized in economically meaningful folders under `data/cleaned/stocks/`:

- `housing_finance/mortgage_facility_certificates/`: 104 traded Bank Maskan `تسه` certificate series, exhaustively enumerated month by month;
- `real_estate_funds/`: 7 traded real-estate investment funds;
- `real_estate_developers/`: 13 current real-estate-sector constituents plus the official sector index;
- `reference/`: the 124-instrument registry.

The standardized long panel contains every valid instrument-day. A continuous daily market series aggregated across all `تسه` instruments traded that day is stored under `data/derived/stocks/housing_finance/`. Its primary measure is volume-weighted price, calculated as total traded value divided by total traded volume; it also includes mean, median, minimum, maximum, and daily coverage counts.

The cement and tile/ceramic sector indices are under `data/cleaned/related_industries/construction_materials/market_indices/`. These are TSETMC securities-market indices, not physical production-volume indices.

Canonical API responses are retained under dated folders in `data/raw/stocks/` and `data/raw/related_industries/`. Rebuild cleaned files and metadata from those raw responses with:

```powershell
python src\stocks\collect_tsetmc_housing_market.py
```

To collect a new automatically dated batch, use the repository update runner. Collection is atomic: timeouts, malformed or empty required responses abort the refresh. Search candidates with no valid traded observations are excluded, and their empty histories are not retained.

```powershell
python src\workflows\update_repository_data.py --refresh-tsetmc
```

For a fully offline rebuild of every retained collection, use `--all-local`. The runner rebuilds both CBI and SCI manual collections from canonical raw workbooks, runs every processor, and finishes with repository validation:

```powershell
python src\workflows\update_repository_data.py --all-local
```

See `docs/UPDATE_RUNBOOK.md` for update modes, snapshot rules, validation, and recovery behavior.

## Adding data

1. Put a newly obtained file in the appropriate `data/incoming/` category. Use `uncategorized` if its category is uncertain.
2. Inspect it without changing it; record its name, type, size, structure, and SHA-256 checksum.
3. Check for exact duplicates and document supported source and coverage facts.
4. Preserve the verified original under `data/raw/<category>/` without overwriting an existing file.
5. Register it in `metadata/data_catalog.csv` and its source in `metadata/source_registry.csv`.
6. Stop unless cleaning or analysis has been requested.

## Environment

Use relative paths and UTF-8 to preserve Persian text. On Windows PowerShell, reproduce the registered cleaned collection from the canonical raw Excel files with:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item data\raw\housing\cbi_tsd_14050431\*.xlsx data\incoming\manually_collected\
Copy-Item data\raw\macro\cbi_tsd_14050431\*.xlsx data\incoming\manually_collected\
.\.venv\Scripts\python.exe src\common\process_cbi_tsd_exports.py
.\.venv\Scripts\python.exe src\macro\register_standardized_macro_csvs.py
.\.venv\Scripts\python.exe src\stocks\collect_tsetmc_housing_market.py
```

The copy step reconstructs the ignored temporary intake area from the canonical raw layer. The processor refuses to overwrite a differing raw file. After processing, compare `metadata/file_manifest.csv` and the catalog checksums to verify byte-level reproducibility.

## Git and data

Commit documentation, metadata, configuration, task definitions, reusable code, and suitable small non-confidential datasets. Do not commit credentials, temporary files, confidential data, large raw data, frequently changing binaries, or reproducible generated outputs without reviewing licensing, size, confidentiality, and professor requirements.

For the current private repository, the small canonical CBI raw workbooks and their cleaned CSVs are retained so a future researcher can use and reproduce the registered collection. Duplicate files in `data/incoming/` remain ignored. If repository visibility or data permissions change, review the raw and cleaned data before publishing.

TSETMC uses a different distribution boundary: standardized and derived CSVs, code, and metadata are committed, while the 90 MB dated raw JSON cache remains local and ignored because it is reproducible from the official API and changes with each snapshot. Preserve a local dated cache when exact historical byte-for-byte reconstruction is required.
