# Derive the all-source housing and rent inflation panel

- Output: `data/derived/housing/inflation/housing_rent_inflation_all_sources.csv`
- Status: preferred comprehensive housing/rent inflation deliverable
- Rows: 13,575
- Providers: CBI/TSD (1,785 rows) and SCI (11,790 rows)
- Frequencies: monthly, quarterly, and annual, retained explicitly
- Included: CBI rent/land-index changes; SCI Tehran dwelling/rent/land changes by municipal region; SCI urban housing/rent CPI inflation; SCI Tehran residential construction-input inflation
- Reviewed but excluded: provincial and historical total CPI without housing components; single-quarter selected material-price snapshot; superseded legacy construction index
- Reproduction: `python src/workflows/update_repository_data.py --all-local`, `--rebuild-cbi`, or `--rebuild-sci`
- Rules: never blend unlike definitions into one synthetic rate; preserve provider, source measure, geography, frequency, and published-versus-calculated status
