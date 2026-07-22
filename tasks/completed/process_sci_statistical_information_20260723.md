# Process SCI statistical-information workbooks

- Source: https://amar.org.ir/statistical-information
- Intake: 11 complete Persian Excel workbooks supplied by the user
- Preservation: byte-identical dated canonical raw copies
- Output: 9 standardized long-form CSV datasets and a 58-sheet workbook inventory
- Reproduction: `python src/workflows/update_repository_data.py --rebuild-sci`
- Rules: retain source units, Persian labels, index bases, missing markers, and published coverage; do not impute, splice, rebase, or infer observations from footnotes
