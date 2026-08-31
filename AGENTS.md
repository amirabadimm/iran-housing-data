# Repository instructions

- Treat this as a flexible research data repository, not a universal pipeline.
- Preserve data first. Never modify or silently overwrite files in `data/raw/`.
- Inspect and register new files before doing anything else.
- Organize datasets by subject; record the provider and download URL in metadata.
- Keep datasets from different providers separate through the standardized layer.
- Cleaning is optional and must have a documented purpose.
- Analysis and visualization are driven by explicit research requests.
- Never guess unknown sources, definitions, units, coverage, or classifications.
- Use `data/incoming/uncategorized/` and flag review when classification is uncertain.
- Link derived datasets to their inputs and generating code/configuration.
- Publish to `data/curated/` and `data/marts/` only after validation passes.
- Power BI reads only from curated datasets or marts, never from raw files.
- Update existing documentation instead of creating duplicate documents.
- Use relative paths, Windows-compatible code, and UTF-8.
- Do not create empty scripts or speculative pipelines.
- Do not commit or push without explicit user permission.
