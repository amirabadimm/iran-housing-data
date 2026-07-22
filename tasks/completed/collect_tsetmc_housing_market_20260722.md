# collect_tsetmc_housing_market_20260722

Completed: 2026-07-22

Collected and retained validated official TSETMC JSON responses for housing-finance certificates, real-estate funds, real-estate developers, the real-estate sector index, and cement and tile/ceramic sector indices. Exact month-by-month discovery found 144 distinct `تسه` records and retained all 104 with valid traded histories. Created six standardized source-level CSV datasets plus one derived continuous daily `تسه` series, updated all metadata registries, and verified an offline rebuild from the canonical raw responses.

Validation included non-empty requested groups, valid JSON/schema, positive trading activity and prices, valid dates, unique instrument-date/index-date keys, aggregate arithmetic, immutable raw paths, and SHA-256 manifest registration. Forty discovered `تسه` records without valid positive trading histories were not retained as datasets.

Future refreshes and offline rebuilds are routed through `src/workflows/update_repository_data.py`; the standalone audit is `src/workflows/validate_repository.py`, and the operating procedure is `docs/UPDATE_RUNBOOK.md`.
