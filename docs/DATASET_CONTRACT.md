# Dataset Contract

Each `dataset.yml` records evidence-backed metadata:

- stable dataset ID and English title;
- provider and publishing unit;
- official landing page and download URL;
- access method;
- frequency, coverage, geography, unit, and classification;
- stock/flow nature and reference time;
- source filename, timestamps, and checksum;
- license or restrictions;
- publication lag and revision policy;
- update strategy, record key, overlap rules, and publication method.

Unknown values remain `null` and are registered in `metadata/quality_issues.csv`. Never infer unsupported metadata.

`schema.yml` defines technical names, types, units, definitions, domains, and nullability. Stop publication and review unexpected schema changes.

Every derived output records its inputs, generating code, execution time, and validation status in `metadata/update_log.csv`.
