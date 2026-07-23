# Derive quarterly housing and rent inflation

- Inputs: registered CBI quarterly rent and land-price index datasets
- Output: `data/derived/housing/inflation/cbi_housing_rent_inflation_quarterly.csv`
- Rows: 910
- Series: 7
- Coverage: rent 1370-Q1–1404-Q2; land-price housing proxy 1377-Q1–1404-Q2
- Geography: Tehran, all urban areas, and exact CBI large/medium/small-city rent groups
- Measures: published source index, quarter-over-quarter percentage change, and year-over-year percentage change
- Reproduction: `python src/workflows/update_repository_data.py --rebuild-cbi`
- Rules: leave unavailable lags blank; preserve source scopes and preliminary flags; do not interpolate, smooth, rebase, weight, or imply that city-size groups exclude Tehran
