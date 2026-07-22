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
- Liquidity and urban unemployment are under `data/cleaned/macro/cbi_non_geographic/`.
- Cleaned coverage begins no earlier than 1370 and ends at each source series' latest actual observation. Most quarterly housing series currently end at 1404-Q2; this is not extended with estimated values.
- Gray source cells are retained as Boolean preliminary flags. No values were interpolated, aggregated, inflation-adjusted, or converted to different units.

Rebuild the registered outputs from the incoming files with:

```powershell
python src\common\process_cbi_tsd_exports.py
```

See `metadata/data_catalog.csv` for dataset-level coverage and provenance, `metadata/variable_dictionary.csv` for variables, and `metadata/cleaning_log.csv` for transformations.

The Excel workbooks—not filenames, earlier documentation, or translated labels—are the authority for dataset identity. Exact Persian report titles, dataset paths, labels, units, reported ranges, frequencies, and observation counts are recorded in `metadata/excel_series_inventory.csv`. Cleaned values retain those source definitions without English renaming.

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
```

The copy step reconstructs the ignored temporary intake area from the canonical raw layer. The processor refuses to overwrite a differing raw file. After processing, compare `metadata/file_manifest.csv` and the catalog checksums to verify byte-level reproducibility.

## Git and data

Commit documentation, metadata, configuration, task definitions, reusable code, and suitable small non-confidential datasets. Do not commit credentials, temporary files, confidential data, large raw data, frequently changing binaries, or reproducible generated outputs without reviewing licensing, size, confidentiality, and professor requirements.

For the current private repository, the small canonical CBI raw workbooks and their cleaned CSVs are retained so a future researcher can use and reproduce the registered collection. Duplicate files in `data/incoming/` remain ignored. If repository visibility or data permissions change, review the raw and cleaned data before publishing.
