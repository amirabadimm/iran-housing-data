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

## Imported standardized macro datasets (2026-07-22)

The five received CSVs were already UTF-8-with-BOM, comma-delimited, lowercase `snake_case`, and keyed using canonical Jalali daily, monthly, or quarterly fields. Validation found complete expected monthly/quarterly sequences, unique ordered keys, no missing required values, and numeric fields that parse correctly. Because they already meet the standard, the cleaned copies are byte-identical to the received raw files.

- CPI retains the total index (`1400=100`) and published month-over-month, year-over-year, and twelve-month-average inflation measures. No measure is selected for analysis here.
- FX retains available daily free-market observations in Iranian rials per US dollar. Missing non-market days are not created; 1405 remains supplementary source coverage.
- GDP retains quarterly real GDP at constant 1400 prices and nominal GDP at current prices, both at basic prices and in billion rials. No growth, seasonal adjustment, interpolation, or deflation is added.
- The اخزا proxy remains an annualized percentage rate reported monthly. Upstream construction used a 1,000,000-rial face value, annual effective zero-coupon YTM per valid instrument-day, transaction-value-weighted daily aggregation, and monthly median. It is not divided by 12.
- FEDFUNDS remains a percentage-point level. Upstream conversion approximated Jalali-month values by day-overlap weighting Gregorian monthly averages; it is not an exact daily-series Jalali average.

These rules document the received datasets; they do not authorize merging, frequency conversion, feature engineering, correlation, regression, or reuse of conclusions from the other project.
