# Decisions log

| Date | Decision | Reason | Affected files | Decided by |
|---|---|---|---|---|
| 2026-07-22 | Initialize a flexible category-based research repository. | Establish safe intake and preservation before datasets arrive. | Repository structure and metadata templates | User/Codex |
| 2026-07-22 | Pair matching all-urban and Tehran CBI series in one dataset. | Preserve the requested geographic comparison without splitting files or inventing counterparts. | 13 cleaned housing datasets | User/Codex |
| 2026-07-22 | Retain non-geographic and city-size CBI series separately. | Their source scope does not support an urban–Tehran pair. | 9 cleaned housing/macro datasets | Codex |
| 2026-07-22 | Restrict cleaned outputs to observations from 1370 onward. | User-requested period; later endpoints follow actual source availability. | All CBI cleaned datasets | User/Codex |
| 2026-07-22 | Import five already-standardized macro CSVs without changing values. | Files passed this repository's structural standard; further cleaning would be unnecessary and risk altering documented series. | Imported CPI, FX, GDP, اخزا, and FEDFUNDS datasets | User/Codex |
| 2026-07-22 | Treat received macro CSVs as raw received artifacts, not original provider downloads. | Several upstream downloads/API responses were not retained in the other project. | Imported macro raw layer and provenance metadata | Codex |
| 2026-07-22 | Do not import the other project's analytical conclusions or panel/model decisions. | This repository's analysis remains professor-request driven; only data provenance and construction rules are relevant now. | Documentation and workflow | Codex |
