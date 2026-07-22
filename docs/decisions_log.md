# Decisions log

## 2026-07-22: Housing-linked TSETMC collection

- Preserve a dated, immutable raw JSON batch and make cleaned outputs reproducible offline.
- Validate algotik-tse sector mappings, then use official TSETMC JSON endpoints for reliable bulk retrieval.
- Use explicit economic folders: housing finance, real-estate funds, real-estate developers, reference, and construction-material market indices.
- Reject timeouts and empty required groups; exclude rather than publish individually empty legacy instruments.
- Label cement and tile/ceramic data as market-sector indices, not production quantities.

## 2026-07-22: Executable update workflow

- Use scripts, rather than a notebook, as the authoritative reproducible pipeline; notebooks may consume outputs but must not be the only way to rebuild them.
- Use one repository runner to coordinate independent source processors and a separate validator.
- Date every network snapshot automatically, refuse same-date overwrite, and select the latest retained complete snapshot for default offline rebuilds.
- Advance exact `تسه` discovery using the collection date's Jalali year.
- Write a JSON validation report after coordinated updates.

| Date | Decision | Reason | Affected files | Decided by |
|---|---|---|---|---|
| 2026-07-22 | Initialize a flexible category-based research repository. | Establish safe intake and preservation before datasets arrive. | Repository structure and metadata templates | User/Codex |
| 2026-07-22 | Pair matching all-urban and Tehran CBI series in one dataset. | Preserve the requested geographic comparison without splitting files or inventing counterparts. | 13 cleaned housing datasets | User/Codex |
| 2026-07-22 | Retain non-geographic and city-size CBI series separately. | Their source scope does not support an urban–Tehran pair. | 9 cleaned housing/macro datasets | Codex |
| 2026-07-22 | Restrict cleaned outputs to observations from 1370 onward. | User-requested period; later endpoints follow actual source availability. | All CBI cleaned datasets | User/Codex |
| 2026-07-22 | Import five already-standardized macro CSVs without changing values. | Files passed this repository's structural standard; further cleaning would be unnecessary and risk altering documented series. | Imported CPI, FX, GDP, اخزا, and FEDFUNDS datasets | User/Codex |
| 2026-07-23 | Standardize eleven complete SCI workbooks into nine economically coherent long-form datasets. | Preserve published Persian definitions and index bases while making all tables reproducible and catalogued. | SCI permits, Tehran housing/construction inputs, and urban CPI | User/Codex |
| 2026-07-23 | Keep SCI base-1390 and base-1402 construction-input indices separate. | Splicing or rebasing would introduce an unpublished transformation. | Tehran construction-input indices | Codex |
| 2026-07-22 | Treat received macro CSVs as raw received artifacts, not original provider downloads. | Several upstream downloads/API responses were not retained in the other project. | Imported macro raw layer and provenance metadata | Codex |
| 2026-07-22 | Do not import the other project's analytical conclusions or panel/model decisions. | This repository's analysis remains professor-request driven; only data provenance and construction rules are relevant now. | Documentation and workflow | Codex |
