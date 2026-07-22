# Collection guides

Document source-specific collection instructions here as sources are approved. Include access date, URL or contact, method, licensing or confidentiality constraints, expected format, update frequency, and verification checks.

## Central Bank of Iran Time Series Database

- Source: <https://tsdview.cis.cbi.ir/single-data>
- Organization: Central Bank of the Islamic Republic of Iran
- Current method: manual Excel export
- Current batch: 18 workbooks generated on 1405/04/31 and collected on 2026-07-22
- Raw rule: preserve each workbook and filename unchanged; calculate and register checksums
- Structural rule: report metadata occupies rows 1–8 and observations start on row 9 in the current exports
- Preliminary rule: the source note identifies gray-filled cells as preliminary; preserve this status in separate Boolean columns
- Geographic rule: pair only columns explicitly labeled `کليه مناطق شهري` and `تهران` for the same indicator and unit
- Time rule: retain actual observations from 1370 onward; do not create values through 1405 when the source ends earlier
- Licensing: not stated in the supplied workbooks; review before redistribution

The source page timed out during automated access on 2026-07-22. Provenance is supported by the user-provided URL and the internal CBI report labels in all workbooks; website details should be rechecked manually when accessible.

## Imported macro CSVs from Data_Analysis

The received files are already standardized outputs from another user project. In this repository, “raw” means the exact files received—not necessarily the original provider downloads. Preserve them byte-for-byte and do not portray them as untouched provider exports.

| Dataset | Provider/provenance | Important limitation |
|---|---|---|
| Iran CPI and inflation | Statistical Center of Iran; <https://amar.org.ir/statistical-information/statid/28579> | Official table identity and individual values remain pending independent verification. |
| Free-market USD/IRR | D-Learn archive, underlying rows labeled TGJU; <https://d-learn.ir/p/usd-price/> | The original `USD2Rials-1.csv` is absent; the received file had already been subset, deduplicated, and structurally standardized upstream. |
| Real and nominal GDP | Statistical Center of Iran Economic Accounts; <https://amar.org.ir/economic-accounts> | User-reported Table 3 constant-price and Table 1 current-price series require independent verification. |
| اخزا risk-free proxy | TSETMC; <https://www.tsetmc.com/> | Final monthly aggregate is retained, but original API responses and instrument-day inputs are absent. |
| Federal Funds Effective Rate | FRED `FEDFUNDS`; <https://fred.stlouisfed.org/series/FEDFUNDS> | Approximate Jalali-month values use overlap-weighted Gregorian monthly averages; original FRED download is absent. |

Run `src/macro/register_standardized_macro_csvs.py` to validate encoding, schemas, expected keys, coverage, row counts, missingness, numeric fields, and raw/cleaned byte identity. Do not interpolate missing market days or manufacture higher-frequency GDP.
