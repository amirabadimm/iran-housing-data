# Project status

Latest update: 2026-07-22

## Available datasets

Twenty-seven cleaned datasets are registered: 20 housing datasets and 7 macro datasets. Thirteen housing datasets contain all-urban and Tehran values paired by period. The macro collection contains two CBI series plus five validated standardized CSVs imported from another user project.

## Awaiting review

The CBI page's licensing/reuse terms and the substantive definitions of the exported indicators require human review. SCI CPI/GDP table identities and values require independent verification. Upstream raw inputs are unavailable for the imported FX, اخزا, and Federal Funds processed files.

## Cleaned datasets

Available under `data/cleaned/housing/` and `data/cleaned/macro/`. CBI coverage is restricted to Solar Hijri year 1370 onward and each series' latest actual observation. Imported macro coverage is recorded per dataset in `metadata/data_catalog.csv`.

## Known data issues

Two labeled source columns contain no observations: the construction-services price index in `TSD-Rep-14050431 (15).xlsx` and a quarterly Bank Maskan loan-count placeholder in `TSD-Rep-14050431 (16).xlsx`. They were not registered as available datasets. See `metadata/data_issues.csv`.

Imported macro limitations are also recorded there: pending SCI provenance verification and missing upstream raw inputs for three previously processed series.

## Active professor requests

None recorded.

## Completed tasks

`cbi_tsd_bulk_standardization_20260722`: preserved 18 raw workbooks and created 22 standardized datasets.

`import_standardized_macro_20260722`: preserved and validated 5 received macro CSVs and added byte-identical cleaned copies.

## Upcoming collection needs

Not yet defined.

## Blocked work

None.
