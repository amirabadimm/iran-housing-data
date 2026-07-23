# Process CBI annual national-accounts export

- Source: https://tsdview.cis.cbi.ir/single-data
- Intake: `data/incoming/manually_collected/TSD-Rep-14050501.xlsx`
- Report generation date: 1405/05/01
- Preservation: byte-identical canonical raw copy under `data/raw/macro/cbi_tsd_14050501/`
- Inventory: all 12 labeled data columns, comprising 6 populated and 6 empty series
- Output: 6 annual standardized CSV datasets under `data/cleaned/macro/national_accounts/`
- Coverage: 1395–1402, with 1402 retained as preliminary
- Reproduction: `python src/workflows/update_repository_data.py --rebuild-cbi`
- Rules: preserve source values, Persian definitions, units, missingness, and preliminary flags; do not impute, aggregate, deflate, rebase, or calculate growth
