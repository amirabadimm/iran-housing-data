# Data workflow

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

`metadata/file_manifest.csv` records paths, sizes, and SHA-256 checksums for the canonical raw workbooks and cleaned CSVs. The temporary incoming copies are intentionally excluded from Git. Reconstruct them from `data/raw/` before running `src/common/process_cbi_tsd_exports.py`; the exact commands are in `README.md`.

## Tasks

Substantial professor requests get a record under `tasks/active/`. Store the objective, research question, inputs, outputs, constraints, methods, status, and related files. Move completed records to `tasks/completed/`; promote stable reusable code to `src/` only when justified.
