# Cleaned macroeconomic data

This layer is organized by economic domain rather than source, collection method, or processing history.

```text
macro/
├── prices_and_inflation/       # CPI, price indices, and inflation measures
├── exchange_rates/             # Domestic-currency exchange-rate series
├── national_accounts/          # GDP and other national-accounts aggregates
├── money_and_credit/           # Monetary aggregates, liquidity, and credit conditions
├── labor_market/               # Employment, unemployment, wages, and participation
└── interest_rates/
    ├── domestic/               # Iranian policy, money-market, government, and credit rates
    └── international/          # Foreign rates relevant to the research context
```

Frequency and provider do not determine the directory. Daily, monthly, quarterly, or annual observations for the same economic concept remain in its domain. Dataset-specific frequency, unit, coverage, source, and exact path are recorded in `metadata/data_catalog.csv`.

Do not place merged cross-domain datasets here. Those belong in `data/derived/cross_category/` or a task-specific location.
