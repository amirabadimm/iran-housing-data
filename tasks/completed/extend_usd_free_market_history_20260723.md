# Extend the daily USD/IRR free-market history

- Source intake: `data/incoming/manually_collected/USD2Rials-1.csv`
- Preservation: byte-identical canonical raw copy under `data/raw/macro/dlearn_tgju_20260723/`
- Source rows: 13,043
- Cleaned output: 13,042 unique daily available-market observations
- Coverage: 1360/07/07 through 1405/04/21
- Prior-overlap check: all 1,815 retained 1399–1405 observations match exactly
- Duplicate handling: two identical 1404/10/09 records remain in raw; one remains in cleaned
- Reproduction: `python src/workflows/update_repository_data.py --rebuild-imported-macro`
- Rules: preserve raw; normalize date and numeric formatting only; do not interpolate, fill calendars, average, or convert units
