# Update and Monitoring Protocol

## Reproducibility

Raw inputs, configuration, code, and dependencies must rebuild every output. Identical inputs must produce identical output without duplicate records.

## Update strategies

- `append_only`: unrevised event or daily data.
- `upsert_revision`: statistics that revise earlier periods.
- `snapshot_rebuild`: complete-history releases.
- `dependency_rebuild`: derived outputs rebuilt after input changes.

Record the strategy in `dataset.yml`. Retain prior observations for revision-prone data.

## Atomic publication

1. Build a unique run under `data/staging/<run_id>/`.
2. Validate schema, keys, coverage, missingness, outliers, identities, and compatibility.
3. Leave the current publication untouched on failure.
4. Publish the validated output and manifest atomically.

## Monitoring

Track coverage, timestamps, frequency, publication lag, freshness, row count, checksum, schema changes, revisions, run status, and quality failures. Refresh Power BI only after successful publication.
