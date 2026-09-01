# SCI Urban Household Consumer Price Index

The Statistical Center of Iran (SCI) workbook reports the urban-household consumer price index with base Solar Hijri year 1400, month-over-month change, year-over-year change, and twelve-month inflation. It contains national major-group, province, and long historical headline series.

## Provider and acquisition

- Organization: Statistical Center of Iran
- Official page: https://amar.org.ir/statistical-information/statid/28595
- Acquisition: manually downloaded workbook
- Direct workbook URL: unavailable in the supplied page/workbook evidence
- Original filename: `ts_urban_140504-14050519161936.xlsx`

The raw workbook is byte-preserved under `data/raw/macroeconomic_environment/inflation/sci_urban_consumer_price_index/1405/` and registered in `metadata/file_registry.csv`.

## Processing

All 12 statistical tables are unpivoted into `urban_cpi_series.csv`. The deterministic pipeline `pipelines/standardization/build_sci_urban_consumer_price_index.py` detects headers by content, preserves table and column lineage, validates unique keys and complete table participation, and publishes atomically.

## Known source anomaly

Table 9 has two distinct 12-column blocks both labeled Solar Hijri year 1402, beginning at source columns 147 and 159; the next block is labeled 1404. The values in columns 159-170 exactly match the independently labeled national 1403 series in table 3 for all 12 months. The pipeline therefore assigns analytical year 1403 to that block while retaining `source_label_year=1402`, the original `source_column`, and an explicit correction status.

Unknown publishing unit, publication date, license, release lag, and direct download URL remain null.
