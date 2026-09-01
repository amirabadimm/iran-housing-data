# SCI Tehran Residential Building Input Prices

The Statistical Center of Iran (SCI) workbook contains price indices for inputs used in the prevalent type of residential construction in Tehran, related inflation measures, and minimum, maximum, and average transaction prices for selected construction materials. Its methodology states that index changes control for item-quality changes, while changes in average material prices are not quality-adjusted.

## Provider and acquisition

- Organization: Statistical Center of Iran
- Official page: https://amar.org.ir/statistical-information/statid/57092
- Acquisition: manually downloaded workbook
- Direct workbook URL: unavailable in the supplied page/workbook evidence
- Original filename: `ts_building_140404-14050319105758.xlsx`

The raw workbook is byte-preserved under `data/raw/construction_costs/input_price_indices/sci_tehran_residential_building_input_prices/1404/` and registered in `metadata/file_registry.csv`.

## Processing

Tables 1-7 are unpivoted into `building_input_price_series.csv`. Tables 8-20 are combined into `building_material_prices.csv`. Table identity, period, metric, base year, Persian source labels, units, source coordinates, raw path, and checksum are retained.

The deterministic pipeline is `pipelines/standardization/build_sci_tehran_building_input_prices.py`. It detects period headers by content, validates unique lineage keys, requires both output families, and publishes atomically.

Unknown publishing unit, publication date, license, release lag, and direct download URL remain null.
