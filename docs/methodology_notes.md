# Methodology notes

## TSETMC housing-linked securities

The instrument universe is defined as: exhaustive exact month-symbol searches for Bank Maskan `تسهYYMM` certificates from 1389 onward, annual post-1400 symbols, explicit real-estate investment-fund search matches, and official constituents of TSETMC real-estate sector `4654922806626448`. Exact searches found 144 distinct `تسه` records; 104 had valid positive traded observations and were retained. Cement (`70077233737515808`) and tile/ceramic (`57616105980228781`) use official sector-index histories.

Daily instrument fields map directly from TSETMC: `priceFirst`, `priceMax`, `priceMin`, `pDrCotVal`, `pClosing`, `priceYesterday`, `zTotTran`, `qTotTran5J`, and `qTotCap`. Prices and traded value are retained in Iranian rials. Prices are unadjusted. No interpolation, imputation, resampling, return calculation, inflation adjustment, or corporate-action adjustment is applied. Gregorian dates are retained and deterministic Jalali date fields are added.

The real-estate, cement, and tile/ceramic outputs are securities-market price indices in index points. They must not be interpreted as physical production indexes or output volumes.

The cleaned `تسه` panel preserves instrument-level observations. The derived continuous daily series groups all certificates traded on a date. `volume_weighted_price_irr = total_trade_value_irr / total_trade_volume`; unweighted mean, median, minimum, maximum, traded-instrument count, total trades, volume, and value are also reported. No missing calendar or trading dates are filled. This aggregate is a reproducible market summary, not an official TSETMC index.

Record methodology only when a collection, cleaning, transformation, or analysis decision is made. Distinguish source definitions from researcher assumptions.

## CBI TSD bulk standardization (2026-07-22)

The supplied files mix single-series exports, multi-series exports, geographic labels, indicator labels, and units across header rows. The reusable processor reads those header fields, normalizes Solar Hijri quarterly labels to `YYYY-Qn`, and retains source numeric values unchanged.

An urban–Tehran pair is created only when two source columns have the same substantive indicator and unit and are explicitly labeled all urban areas and Tehran. Both values appear in the same row. Some source files provide the pair in separate workbooks; others provide both columns in one workbook. Period unions preserve available values and leave an unavailable counterpart blank.

Non-geographic indicators—including national monetary, credit, construction, or Bank Maskan measures—remain single-scope datasets. The processor does not manufacture a geographic pair. The supplied urban unemployment rate is categorized as macro but remains as labeled because no Tehran counterpart was supplied.

No interpolation, missing-value replacement, frequency conversion, rebasing, deflation, unit conversion, outlier treatment, or statistical analysis was performed. Gray-filled source observations are marked preliminary.

The substantive dataset names, labels, and units are kept exactly as written in the Excel headers. English identifiers are used only for stable machine-readable filenames and column keys; they do not replace the CBI definitions.

## CBI annual national accounts (2026-07-23)

The annual CBI export generated 1405/05/01 contains twelve labeled data columns for 1393–1403. Six columns contain eight observations each, covering 1395–1402: private- and public-sector gross fixed capital formation in buildings and real-estate-activities value added, each in current prices and constant 1400 prices. All source units are billion rials. The 1402 observations are gray-filled and retained with `value_preliminary=True`.

Six other labeled columns contain no observations and are recorded as empty in `metadata/excel_series_inventory.csv`; no empty cleaned dataset was created. No missing years were filled, and no aggregation, deflation, rebasing, growth calculation, or reconciliation between current- and constant-price series was performed.

## Imported standardized macro datasets (2026-07-22)

The five received CSVs were already UTF-8-with-BOM, comma-delimited, lowercase `snake_case`, and keyed using canonical Jalali daily, monthly, or quarterly fields. Validation found complete expected monthly/quarterly sequences, unique ordered keys, no missing required values, and numeric fields that parse correctly. Because they already meet the standard, the cleaned copies are byte-identical to the received raw files.

- CPI retains the total index (`1400=100`) and published month-over-month, year-over-year, and twelve-month-average inflation measures. No measure is selected for analysis here.
- FX retains available daily free-market observations in Iranian rials per US dollar. Missing non-market days are not created; 1405 remains supplementary source coverage.
- GDP retains quarterly real GDP at constant 1400 prices and nominal GDP at current prices, both at basic prices and in billion rials. No growth, seasonal adjustment, interpolation, or deflation is added.
- The اخزا proxy remains an annualized percentage rate reported monthly. Upstream construction used a 1,000,000-rial face value, annual effective zero-coupon YTM per valid instrument-day, transaction-value-weighted daily aggregation, and monthly median. It is not divided by 12.
- FEDFUNDS remains a percentage-point level. Upstream conversion approximated Jalali-month values by day-overlap weighting Gregorian monthly averages; it is not an exact daily-series Jalali average.

These rules document the received datasets; they do not authorize merging, frequency conversion, feature engineering, correlation, regression, or reuse of conclusions from the other project.

## Extended USD/IRR history (2026-07-23)

The later-supplied `USD2Rials-1.csv` is preserved byte-for-byte and contains 13,043 source rows from 1360/07/07 through 1405/04/21. Source labels transition from `bourseview` (8,817 rows through 1390/09/03) to `tgju` (4,226 rows from 1390/09/05). The file contains one exact duplicate for 1404/10/09; the raw file retains both rows and the cleaned unique-date series retains one.

Cleaning normalizes Gregorian dates to `YYYY-MM-DD`, splits the Jalali key into year/month/day fields, removes numeric thousands separators, and parses the rate as Iranian rials per US dollar. All 1,815 observations overlapping the previously retained 1399–1405 standardized raw file agree exactly. No interpolation, calendar filling, averaging, unit conversion, or conflict resolution was required. The historical cleaned filename ending in `1399_1405` is retained for downstream compatibility even though catalogued coverage now starts in 1360.

## Derived housing and rent inflation (2026-07-23)

Quarter-over-quarter inflation is calculated as `100 × (index_t / index_t-1 − 1)`, and year-over-year inflation as `100 × (index_t / index_t-4 − 1)`. The inputs are the registered CBI quarterly rent indices for Tehran, all urban areas, and large/medium/small-city groups, plus the Tehran and all-urban land-price indices.

The land-price change is labeled `land_price_housing_proxy`; it is not a general dwelling-sale CPI. City-size groups retain the exact CBI labels and must not be interpreted as mutually exclusive “other cities outside Tehran,” because no exclusion weights or Tehran-free aggregate were published. Initial unavailable lags remain blank. No interpolation, smoothing, seasonal adjustment, rebasing, weighting, or annualization is performed.

## All-source housing and rent inflation panel (2026-07-23)

The preferred long-form panel combines the calculated CBI rates above with published SCI measures from four relevant datasets: Tehran dwelling-sale, land, and rent changes by municipal region; national urban housing/rent/housing-utilities/maintenance CPI inflation; annual inflation for those CPI components; and Tehran residential construction-input inflation by input group. Provider, source dataset, original measure, frequency, geography, component, and published-versus-calculated status remain explicit.

All registered files were reviewed for relevance. SCI provincial CPI is excluded because it contains total CPI by province but no housing component. The historical total CPI file is likewise not housing-specific. The selected building-material file is a single 1404-Q4 price snapshot and cannot support an inflation rate without a comparison period. The SCI legacy construction-input file contains indices but is superseded for this purpose by the base-1402 dataset, which already publishes the corresponding change measures. No unlike frequencies or definitions are merged into a synthetic rate.

## SCI statistical-information workbooks (2026-07-23)

All 58 sheets in eleven supplied Persian workbooks are inventoried. Published tables are normalized to long form while preserving Solar Hijri periods, Persian categories, geographic level, source sheet/file, units, index base years, and explicit missing markers. No interpolation, aggregation, inflation adjustment, unit conversion, or frequency conversion is performed.

Tehran housing prices, rent, transactions, quarterly and annual changes remain distinct measures in one region-period panel. Construction-input indices using base years 1390 and 1402 remain separate datasets. CPI tables are separated economically into national monthly by group, national annual by group, provincial tables, and long historical total series. Permit footnotes are not parsed as observations; their definitions remain recoverable from immutable raw workbooks and the sheet inventory.

Provincial urban CPI Table 9 contains an evident header typo: its year blocks end `1401, 1402, 1402, 1404, 1405`, while parallel Tables 7, 8, and 10 use `1401, 1402, 1403, 1404, 1405`. The processor records the intervening Table 9 block as 1403 only after asserting this exact pattern; the raw workbook remains unchanged and the correction is registered in `metadata/data_issues.csv`.
