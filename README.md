# Iran Housing Data Research Platform

A reproducible, subject-oriented repository for collecting, preserving, standardizing, and analyzing data related to Iran's housing market. Providers and download locations are recorded in metadata; the repository itself is organized by research subject.

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

## Current production dataset

The CBI monthly monetary and credit dataset provides 240 validated observations from Solar Hijri 1385-01 through 1404-12. See its [dataset documentation](datasets/macroeconomic_environment/liquidity/cbi_selected_economic_indicators_monetary_credit_monthly/README.md).

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
