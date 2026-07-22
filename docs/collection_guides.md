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
