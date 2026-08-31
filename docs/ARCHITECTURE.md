# Repository Architecture

## Subject hierarchy

```text
datasets/
|-- housing_market/
|   |-- residential_sales/
|   |-- rent/
|   `-- land/
|-- housing_supply/
|   |-- building_permits/
|   |-- construction_starts/
|   `-- construction_completions/
|-- construction_costs/
|-- housing_investment/
|-- housing_finance/
|-- capital_markets/
`-- macroeconomic_environment/
    |-- liquidity/
    |-- inflation/
    |-- exchange_rate/
    |-- interest_rates/
    |-- unemployment/
    `-- gdp/
```

The provider is metadata, not the top-level organizing principle. Comparable statistics from different providers use separate dataset IDs and remain separate through standardization. Curated data may combine them only through a documented reconciliation method.

## Data lifecycle

1. `incoming`: temporary, unverified arrivals.
2. `raw`: registered, immutable source snapshots.
3. `staging`: temporary run output used for validation.
4. `standardized`: consistent technical format without cross-provider merging.
5. `curated`: validated, research-ready datasets.
6. `marts`: stable consumption models, including Power BI schemas.

## Dataset package

Each dataset package lives at `datasets/<domain>/<topic>/<dataset_id>/` and contains at least `dataset.yml`, `README.md`, and `schema.yml`.

Lifecycle: `discovered -> downloaded -> inspected -> registered -> validated -> standardized -> published -> monitored`.
