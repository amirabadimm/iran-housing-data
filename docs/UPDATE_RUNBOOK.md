# Data update runbook

This is the operational footprint for maintaining the repository. Run commands from the repository root with the project environment activated.

## Normal commands

Rebuild TSETMC cleaned and derived outputs from the latest retained raw snapshot, without network access:

```powershell
python src\workflows\update_repository_data.py --rebuild-tsetmc
```

Collect a new TSETMC snapshot dated today, rebuild outputs, and validate the repository:

```powershell
python src\workflows\update_repository_data.py --refresh-tsetmc
```

Rebuild every collection from local canonical raw data:

```powershell
python src\workflows\update_repository_data.py --all-local
```

Run only the final audit:

```powershell
python src\workflows\validate_repository.py --report outputs\validation\latest_repository_validation.json
```

## Selective and dated runs

```powershell
python src\workflows\update_repository_data.py --rebuild-cbi
python src\workflows\update_repository_data.py --rebuild-imported-macro
python src\workflows\update_repository_data.py --rebuild-tsetmc --as-of 2026-07-22
python src\workflows\update_repository_data.py --refresh-tsetmc --as-of 2026-08-15
```

`--as-of` is a Gregorian date. It controls the immutable raw folder name, catalog collection date, task identifier, and Jalali-year discovery horizon. Never use a false date merely to avoid a folder collision.

## What each stage does

1. Discovery identifies exact source entities. TSETMC `تسه` discovery enumerates exact month symbols rather than relying on capped broad search.
2. Collection holds every response in memory and validates the complete requested batch before publishing.
3. Raw publication creates new date-stamped folders and refuses overwrite.
4. Cleaning standardizes source-level records while preserving instrument identity and unadjusted values.
5. Derivation calculates the continuous daily `تسه` market summary from the cleaned panel.
6. Metadata generation updates the catalog, variables, cleaning log, sources, issues, and SHA-256 manifest.
7. Validation checks manifest files and hashes, catalog output paths, unique keys, positive trading values, and derived arithmetic.

## Failure and recovery

- Network timeout, malformed JSON, or missing required market group: the refresh exits nonzero and publishes no new raw batch.
- Exact candidate with no history: it is excluded; neither an empty history nor an empty exact-search response is retained.
- Existing dated raw destination: choose the truthful collection date or rebuild that retained snapshot; never overwrite it.
- Validation failure: do not commit the generated outputs. Read the reported errors, correct the source-specific processor, rerun the same offline rebuild, and validate again.
- Conflicting CBI intake file: the runner stops. Compare it with the canonical raw workbook; it will not overwrite a differing file.

## Outputs and audit trail

- Immutable inputs: `data/raw/` (dated TSETMC API caches remain local and Git-ignored; provider/raw paths are recorded in the catalog)
- Standardized source observations: `data/cleaned/`
- Calculated research series: `data/derived/`
- Dataset and variable dictionary: `metadata/data_catalog.csv`, `metadata/variable_dictionary.csv`
- Transformations and issues: `metadata/cleaning_log.csv`, `metadata/data_issues.csv`
- File hashes: `metadata/file_manifest.csv`
- Latest machine-readable audit: `outputs/validation/latest_repository_validation.json`
- Executable workflow: `src/workflows/update_repository_data.py`
- Standalone audit: `src/workflows/validate_repository.py`

## Git distribution boundary

Commit the reusable code, documentation, metadata, dictionaries, and suitable standardized/derived CSVs. The dated TSETMC raw JSON cache is large, frequently refreshed, and reproducible from the official API, so it is intentionally ignored. The cleaned instrument panels and continuous derived series are distributed so a new user can analyze the current snapshot immediately. To create a new local raw cache, run `--refresh-tsetmc`; exact historical rebuilds require retaining the corresponding local dated cache outside Git.
