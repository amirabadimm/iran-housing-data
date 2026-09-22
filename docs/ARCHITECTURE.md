# Repository Architecture

## Subject hierarchy

This architecture was introduced in the redesign committed as `9e711d0` on 31 August 2026. Earlier collections and calculation workflows existed under the former `src/`, `data/cleaned/`, and `data/derived/` structure. Their historical availability does not imply publication in the new structure. See [Project Status](../PROJECT_STATUS.md) for the transition and current inventory.

The tree below includes both established topics and planned or placeholder topics; directory existence alone does not indicate a completed dataset. Consult the dataset registry for established packages.

```text
datasets/
|-- housing_market/
|   |-- residential_sales/
|   |-- transaction_prices/
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

The current CBI Tehran monthly housing package lives under `housing_market/transaction_prices/cbi_tehran_housing_monthly/`. `residential_sales/` is an existing scaffold topic, not the path of that published package. No folder rename or data migration is implied by this documentation.

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
