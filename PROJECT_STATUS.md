# Project status

Latest update: 2026-07-22

## Available datasets

Thirty-four datasets are registered: 20 housing, 7 macro, 6 stocks, and 1 related-industries dataset. Thirteen housing datasets contain all-urban and Tehran values paired by period. The securities collection covers 124 validated instruments, including 104 traded `تسه` series, and three market-sector indices. The sixth stocks dataset is a derived continuous daily `تسه` series.

## Awaiting review

The CBI page's licensing/reuse terms and the substantive definitions of the exported indicators require human review. SCI CPI/GDP table identities and values require independent verification. Upstream raw inputs are unavailable for the imported FX, اخزا, and Federal Funds processed files.

## Cleaned datasets

Available under `data/cleaned/housing/`, `data/cleaned/macro/`, `data/cleaned/stocks/`, and `data/cleaned/related_industries/`. Coverage and units are recorded per dataset in `metadata/data_catalog.csv`.

## Known data issues

Two labeled source columns contain no observations: the construction-services price index in `TSD-Rep-14050431 (15).xlsx` and a quarterly Bank Maskan loan-count placeholder in `TSD-Rep-14050431 (16).xlsx`. They were not registered as available datasets. See `metadata/data_issues.csv`.

Imported macro limitations are also recorded there: pending SCI provenance verification and missing upstream raw inputs for three previously processed series.

The algotik/TSETMC real-estate-fund listing endpoint returned an empty array, so the validated official instrument-search endpoint was used. One empty legacy `تسه` search candidate was excluded without retaining its empty history. See `metadata/data_issues.csv`.

## Active professor requests

None recorded.

## Completed tasks

`cbi_tsd_bulk_standardization_20260722`: preserved 18 raw workbooks and created 22 standardized datasets.

`import_standardized_macro_20260722`: preserved and validated 5 received macro CSVs and added byte-identical cleaned copies.

`collect_tsetmc_housing_market_20260722`: exhaustively enumerated monthly `تسه` symbols, preserved official non-empty TSETMC responses, created 6 standardized source-level datasets, and created 1 derived continuous `تسه` series.

## Upcoming collection needs

Not yet defined.

## Blocked work

None.

## Maintenance workflow

Use `python src/workflows/update_repository_data.py --refresh-tsetmc` for a new atomic market snapshot, `--rebuild-tsetmc` for an offline market rebuild, or `--all-local` for all locally reproducible collections. Every run ends with `src/workflows/validate_repository.py`; operational details are in `docs/UPDATE_RUNBOOK.md`.
