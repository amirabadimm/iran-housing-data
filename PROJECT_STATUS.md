# Project status

Latest update: 2026-07-23

## Available datasets

Fifty-one datasets are registered: 27 housing, 17 macro, 6 stocks, and 1 related-industries dataset. Thirteen CBI housing datasets contain all-urban and Tehran values paired by period. The SCI collection adds nine datasets from eleven complete Persian workbooks: building permits, Tehran housing prices/rents/transactions, Tehran construction-input indices/material prices, and urban CPI. Six CBI annual national-accounts datasets cover building investment and real-estate value added at current and constant-1400 prices. The preferred all-source housing/rent inflation panel contains 13,575 CBI and SCI observations while a smaller CBI-only calculation remains available for auditability. The securities collection covers 124 validated instruments, including 104 traded `تسه` series, and three market-sector indices. The sixth stocks dataset is a derived continuous daily `تسه` series.

## Awaiting review

The CBI and SCI portals' licensing/reuse terms require human review. The SCI portal returned HTTP 502 during automated verification on 2026-07-23, so its supplied workbook contents and internal metadata were treated as authoritative. Upstream raw inputs are unavailable for the imported FX, اخزا, and Federal Funds processed files.

## Cleaned datasets

Available under `data/cleaned/housing/`, `data/cleaned/macro/`, `data/cleaned/stocks/`, and `data/cleaned/related_industries/`. Coverage and units are recorded per dataset in `metadata/data_catalog.csv`.

## Known data issues

Two labeled source columns contain no observations: the construction-services price index in `cbi_rent_land_price_unemployment_indices_quarterly.xlsx` and a quarterly Bank Maskan loan-count placeholder in `cbi_building_permits_floor_area_quarterly.xlsx`. They were not registered as available datasets. See `metadata/data_issues.csv`.

Six labeled columns in `cbi_building_investment_real_estate_value_added_national_accounts_annual_1395_1402.xlsx` also contain no observations. All are retained in the Excel inventory, while only the six populated series were standardized.

Imported macro limitations are also recorded there: pending SCI provenance verification and missing upstream raw inputs for the اخزا and Federal Funds series. The previously missing `dlearn_usd_irr_free_market_daily_1360_1405.csv` source is now retained and extends the cleaned FX history to 1360/07/07.

The algotik/TSETMC real-estate-fund listing endpoint returned an empty array, so the validated official instrument-search endpoint was used. One empty legacy `تسه` search candidate was excluded without retaining its empty history. See `metadata/data_issues.csv`.

## Active professor requests

None recorded.

## Completed tasks

`cbi_tsd_bulk_standardization_20260722`: preserved 18 raw workbooks and created 22 standardized datasets.

`import_standardized_macro_20260722`: preserved and validated 5 received macro CSVs and added byte-identical cleaned copies.

`collect_tsetmc_housing_market_20260722`: exhaustively enumerated monthly `تسه` symbols, preserved official non-empty TSETMC responses, created 6 standardized source-level datasets, and created 1 derived continuous `تسه` series.

`process_sci_statistical_information_20260723`: preserved 11 complete SCI workbooks, inventoried 58 sheets, and created 9 standardized datasets containing 99,114 rows.

`cbi_tsd_national_accounts_20260723`: preserved one annual CBI workbook, inventoried all 12 labeled data columns, and created 6 standardized national-accounts datasets.

`extend_usd_free_market_history_20260723`: preserved the complete 13,043-row USD/IRR source, removed one exact duplicate in the cleaned layer, verified all 1,815 prior overlapping values, and extended cleaned coverage to 13,042 unique observations from 1360/07/07 through 1405/04/21.

`derive_housing_rent_inflation_20260723`: created a 910-row quarterly panel of CBI rent and land-price-index changes for Tehran, all urban areas, and exact city-size groups.

`derive_housing_rent_inflation_all_sources_20260723`: created a 13,575-row preferred panel combining 1,785 CBI/TSD observations and 11,790 SCI published observations across monthly, quarterly, and annual frequencies.

## Upcoming collection needs

Not yet defined.

## Blocked work

None.

## Maintenance workflow

Use `python src/workflows/update_repository_data.py --rebuild-sci` for an offline SCI rebuild, `--refresh-tsetmc` for a new atomic market snapshot, `--rebuild-tsetmc` for an offline market rebuild, or `--all-local` for all locally reproducible collections. Every run ends with `src/workflows/validate_repository.py`; operational details are in `docs/UPDATE_RUNBOOK.md`.
