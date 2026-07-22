# Task record

- task_id: import_standardized_macro_20260722
- title: Integrate standardized macro datasets from the user's other project
- request_date: 2026-07-22
- requested_by: repository owner
- objective: Read five macro CSVs and six supporting documents, preserve the received files, validate them against this repository's standard, and register reusable cleaned datasets.
- research_question: Not applicable; this is data registration and standardization, not analysis.
- required_datasets: CPI/inflation, daily free-market USD/IRR, quarterly real/nominal GDP, monthly اخزا risk-free proxy, and Jalali-aligned monthly FEDFUNDS
- requested_outputs: canonical raw copies, validated cleaned copies, reproducible validator, metadata, provenance, issues, and workflow updates
- constraints: retain upstream values and native frequencies; do not import unrelated model decisions or conclusions; do not fabricate missing observations or upstream raw provenance
- methodological_notes: received files already conformed, so cleaned copies are byte-identical; see `docs/methodology_notes.md`
- status: completed
- completion_date: 2026-07-22
- related_files: `src/macro/register_standardized_macro_csvs.py`; `data/raw/macro/external_data_analysis_20260722/`; economic-domain folders under `data/cleaned/macro/`; metadata tables
