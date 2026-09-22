# Iran Housing Data Research Platform

A reproducible, subject-oriented repository for collecting, preserving, standardizing, and analyzing data related to Iran's housing market. Providers and download locations are recorded in metadata; the repository itself is organized by research subject.

## Project history and present stage

This project has completed an initial broad collection and processing phase and is now rebuilding its datasets within a redesigned subject-oriented structure. It is not starting data collection for the first time.

- **22–23 July 2026:** CBI, SCI, TSETMC, and received macroeconomic files were collected and processed. The historical catalog reached 51 datasets: 27 housing, 17 macroeconomic, 6 securities, and 1 related-industries dataset. Outputs included a continuous mortgage-certificate (`تسه`) price series and housing/rent inflation panels. Collection scripts and rebuild workflows already existed in this phase.
- **August 2026:** Research literature was added, source filenames were organized, and further coverage and definition questions were recorded in `Notes.txt`.
- **Redesign recorded in Git on 31 August 2026:** The former structure was replaced with subject-oriented dataset packages, explicit data layers, and new registries. The redesign-era status file dates the redesign to 26 August; the commit date is 31 August. Historical outputs and documentation remain evidence in Git, but are not automatically current published datasets.
- **Since the redesign:** Monthly CBI liquidity, SCI building-input prices, SCI urban CPI, and CBI Tehran transaction prices have been established in the new structure. The current registry lists four dataset packages. This is the rebuilt inventory, not the total historical achievement of the project.

**Current stage:** rebuild and register the remaining relevant collections, update their coverage where source evidence permits, and prepare outputs for specific research requests. The housing project remains in progress. See [Project Status](PROJECT_STATUS.md) for the evidence-backed timeline, current inventory, and remaining work.

## Core principles

- Register every input with its source, acquisition time, and SHA-256 checksum.
- Preserve raw files byte-for-byte and retain every source revision.
- Keep comparable datasets from different providers separate through standardization.
- Validate outputs before atomic publication.
- Require idempotent pipelines.
- Connect Power BI only to validated curated data or marts.

## Repository map

- `datasets/`: subject catalog and dataset packages
- `data/`: lifecycle data layers
- `metadata/`: dataset, source, file, variable, quality, and update registries
- `pipelines/`: ingestion and standardization code
- `research/`: research questions, methods, literature, and notebooks
- `dashboards/power_bi/`: Power BI documentation
- `outputs/`: deliverable tables, figures, and reports
- `templates/dataset/`: new-dataset template

## Datasets established in the new structure

The CBI monthly monetary and credit dataset provides 240 validated observations from Solar Hijri 1385-01 through 1404-12. See its [dataset documentation](datasets/macroeconomic_environment/liquidity/cbi_selected_economic_indicators_monetary_credit_monthly/README.md).

The SCI Tehran building-input dataset provides normalized price-index, inflation, and selected-material-price observations. See its [dataset documentation](datasets/construction_costs/input_price_indices/sci_tehran_residential_building_input_prices/README.md).

The SCI urban CPI dataset provides normalized national, major-group, provincial, and historical urban-household series from all 12 source tables. See its [dataset documentation](datasets/macroeconomic_environment/inflation/sci_urban_consumer_price_index/README.md).

The CBI Tehran monthly housing transaction-price dataset has 101 validated months from 1395/01 through 1403/05 and a dataset-local one-click refresh. Power BI reads its curated CSV; see [dataset documentation](datasets/housing_market/transaction_prices/cbi_tehran_housing_monthly/README.md).

## Adding source data

1. Place the unchanged file in `data/incoming/`.
2. Verify and register its provider, definition, and checksum.
3. Preserve it under the appropriate subject and dataset path in `data/raw/`.
4. Create transformations only for a documented analytical purpose.
5. Publish only after validation succeeds.

See [Architecture](docs/ARCHITECTURE.md), [Dataset Contract](docs/DATASET_CONTRACT.md), and [Update Protocol](docs/UPDATE_PROTOCOL.md).

## Development environment

Python 3.11 or newer is required. This repository shares `..\Finenv` with `..\Work`.

```powershell
py -m venv ..\Finenv
..\Finenv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

VS Code uses the shared environment automatically. Never commit environments, caches, or credentials.
