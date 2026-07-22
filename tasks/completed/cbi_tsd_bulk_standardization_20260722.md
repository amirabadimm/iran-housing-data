# Task record

- task_id: cbi_tsd_bulk_standardization_20260722
- title: Preserve and standardize manually collected CBI TSD exports
- request_date: 2026-07-22
- requested_by: repository owner
- objective: Read all supplied CBI exports, preserve originals, standardize supported data from Solar Hijri year 1370 onward, and keep matching all-urban and Tehran series together.
- research_question: Not applicable; this is data preparation, not analysis.
- required_datasets: 18 Excel exports in `data/incoming/manually_collected/`
- requested_outputs: unchanged raw copies, paired urban–Tehran housing datasets, standardized non-geographic and city-size datasets, and updated metadata/documentation
- constraints: preserve source values and units; use each series' latest actual observation; do not keep urban and Tehran counterparts in separate cleaned files
- methodological_notes: see `docs/methodology_notes.md`
- status: completed
- completion_date: 2026-07-22
- related_files: `src/common/process_cbi_tsd_exports.py`; `metadata/data_catalog.csv`; `metadata/cleaning_log.csv`; 22 datasets under `data/cleaned/`
