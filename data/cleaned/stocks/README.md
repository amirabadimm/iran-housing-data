# Stocks data

This category is organized by economic role rather than processing step:

- `housing_finance/mortgage_facility_certificates/`: Bank Maskan housing-finance certificates.
- `real_estate_funds/`: exchange-traded property funds.
- `real_estate_developers/`: listed property/development companies and their sector index.
- `reference/`: instrument-universe registry.

All prices are unadjusted Iranian-rial observations from TSETMC. Rebuild with `python src/stocks/collect_tsetmc_housing_market.py`.

Cleaned data preserve standardized source observations. Calculated aggregates belong under `data/derived/`; the continuous daily `تسه` market series is therefore stored in `data/derived/stocks/housing_finance/`.
