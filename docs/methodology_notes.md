# Methodology notes

Record methodology only when a collection, cleaning, transformation, or analysis decision is made. Distinguish source definitions from researcher assumptions.

## CBI TSD bulk standardization (2026-07-22)

The supplied files mix single-series exports, multi-series exports, geographic labels, indicator labels, and units across header rows. The reusable processor reads those header fields, normalizes Solar Hijri quarterly labels to `YYYY-Qn`, and retains source numeric values unchanged.

An urban–Tehran pair is created only when two source columns have the same substantive indicator and unit and are explicitly labeled all urban areas and Tehran. Both values appear in the same row. Some source files provide the pair in separate workbooks; others provide both columns in one workbook. Period unions preserve available values and leave an unavailable counterpart blank.

Non-geographic indicators—including national monetary, credit, construction, or Bank Maskan measures—remain single-scope datasets. The processor does not manufacture a geographic pair. The supplied urban unemployment rate is categorized as macro but remains as labeled because no Tehran counterpart was supplied.

No interpolation, missing-value replacement, frequency conversion, rebasing, deflation, unit conversion, outlier treatment, or statistical analysis was performed. Gray-filled source observations are marked preliminary.

The substantive dataset names, labels, and units are kept exactly as written in the Excel headers. English identifiers are used only for stable machine-readable filenames and column keys; they do not replace the CBI definitions.
