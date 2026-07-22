# Data workflow

## Atomic API collection

API collectors fetch and validate a complete requested batch in memory before publishing it. A timeout, malformed JSON, empty required group, missing index, or invalid schema aborts the refresh. Individually empty instrument histories discovered through a broader search are excluded and are not saved as datasets. Existing dated raw batches are immutable; cleaned outputs can be rebuilt from them without network access.

## Executable flow

```text
Official/manual sources
        |
        v
ignored intake (manual CBI/SCI) ----- checksum/identity inspection
        |
        v
dated immutable raw snapshots
        |
        +---- offline parser/standardizer ----> cleaned source-level panels
        |                                           |
        |                                           v
        |                                  derived calculated series
        |                                           |
        +-------------------> metadata/catalog/manifest/validation
                                                    |
                                                    v
                                      tasks, notebooks, and analysis
```

The executable entry point is `src/workflows/update_repository_data.py`. It coordinates source-specific processors and then runs `src/workflows/validate_repository.py`. Source collectors remain separate so a failure cannot silently affect unrelated categories.

The repository separates continuous data management from request-driven analysis:

```text
incoming -> raw -> optional cleaned -> optional derived -> optional task analysis
```

A dataset does not need to pass through every stage.

## Intake

Inspect each new file without modifying it. Record its filename, extension, size, SHA-256 checksum, supported identity and source facts, and basic structure. Check exact duplicates. For CSV files, inspect encoding, delimiter, row count, and columns. For Excel files, inspect sheet names and basic dimensions.

Use a confirmed category only when reliable evidence supports it. Otherwise place the file in `data/incoming/uncategorized/` and mark it for review.

## Raw

Raw files are unchanged originals. Retain the original filename in metadata, never silently overwrite a raw file, and keep older source versions. A safer storage name is acceptable only when metadata preserves the original name.

## Cleaned and derived

Create cleaned data only for a documented interpretation or research need. Preserve raw inputs and record material transformations in `metadata/cleaning_log.csv`. Never infer missing values, interpolate, remove duplicates, or transform variables without evidence and authorization.

Derived data must identify all inputs and its generating script. Cross-category combinations belong in `data/derived/cross_category/`; narrow professor-request datasets belong in `data/derived/task_specific/` or their task directory.

## Reproducibility

`metadata/file_manifest.csv` records paths, sizes, and SHA-256 checksums for files distributed by the repository: canonical CBI, SCI, and imported-macro raw files plus cleaned and derived data. Temporary intake, generated reports, and reproducible dated TSETMC API caches are excluded from Git and from the distributed-file manifest. TSETMC raw paths remain recorded in the data catalog. SCI rebuilds read the canonical raw workbooks directly; incoming copies are only needed for first-time ingestion.

The imported macro CSVs have a separate idempotent validator at `src/macro/register_standardized_macro_csvs.py`. Their raw layer is the exact artifact received from the other project; upstream provider downloads are unavailable for some series. Both processors preserve each other's catalog and registry entries.

The TSETMC collector has two modes. `--refresh` performs network discovery and creates a new date-stamped immutable raw batch; no flag rebuilds cleaned, derived, and metadata outputs from the latest retained complete batch. `--as-of YYYY-MM-DD` selects an explicit snapshot date. A same-date refresh is refused rather than overwriting raw data.

Cleaned macro data is organized by economic meaning—not by provider or processing method: prices and inflation, exchange rates, national accounts, money and credit, labor market, and interest rates. Interest rates are divided into domestic and international series where useful. New macro datasets should be placed in the closest established economic domain, with a new lowercase snake_case domain added only when none fits.

## Tasks

Substantial professor requests get a record under `tasks/active/`. Store the objective, research question, inputs, outputs, constraints, methods, status, and related files. Move completed records to `tasks/completed/`; promote stable reusable code to `src/` only when justified.
