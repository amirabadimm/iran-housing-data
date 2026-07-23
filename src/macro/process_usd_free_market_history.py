"""Preserve and standardize the received long-history USD/IRR source file."""

from __future__ import annotations

import csv
import hashlib
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INCOMING = ROOT / "data" / "incoming" / "manually_collected" / "USD2Rials-1.csv"
RAW = ROOT / "data" / "raw" / "macro" / "dlearn_tgju_20260723" / "USD2Rials-1.csv"
PRIOR_RAW = ROOT / "data" / "raw" / "macro" / "external_data_analysis_20260722" / "iran_daily_usd_free_market_rate_1399_1405.csv"
CLEAN = ROOT / "data" / "cleaned" / "macro" / "exchange_rates" / "iran_daily_usd_free_market_rate_1399_1405.csv"
DATASET_ID = "macro_iran_usd_free_market_daily_1399_1405"
TASK_ID = "extend_usd_free_market_history_20260723"
SOURCE_URL = "https://d-learn.ir/p/usd-price/"

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
SOURCE_FIELDS = "source_id,source_organization,source_name,source_url,access_method,date_accessed,license,access_status,contact,notes".split(",")
ISSUE_FIELDS = "issue_id,dataset_id,date_identified,issue_type,description,severity,status,resolution,related_file,notes".split(",")
OUTPUT_FIELDS = ["jalali_date", "gregorian_date", "jalali_year", "jalali_month", "jalali_day", "source", "usd_free_market_rate_irr"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def replace_dataset_rows(path: Path, fields: list[str], new_rows: list[dict[str, object]]) -> None:
    existing = read_rows(path)[1] if path.exists() else []
    ids = {str(row["dataset_id"]) for row in new_rows}
    write_rows(path, fields, [row for row in existing if row.get("dataset_id") not in ids] + new_rows)


def parse_gregorian(value: str) -> str:
    for pattern in ("%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized Gregorian date: {value!r}")


def preserve_raw() -> None:
    if INCOMING.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        if RAW.exists() and sha256(RAW) != sha256(INCOMING):
            raise FileExistsError(f"Incoming source differs from canonical raw: {RAW}")
        if not RAW.exists():
            shutil.copy2(INCOMING, RAW)
    if not RAW.exists():
        raise FileNotFoundError(f"Missing canonical source: {RAW}")


def standardize() -> list[dict[str, object]]:
    fields, source_rows = read_rows(RAW)
    if fields != ["date_pr", "date_gr", "source", "price_avg"]:
        raise ValueError(f"Unexpected source schema: {fields}")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        grouped[row["date_pr"]].append(row)
    duplicates = {key: rows for key, rows in grouped.items() if len(rows) > 1}
    if set(duplicates) != {"1404/10/09"} or len(duplicates["1404/10/09"]) != 2 or duplicates["1404/10/09"][0] != duplicates["1404/10/09"][1]:
        raise ValueError(f"Unexpected or conflicting duplicate source dates: {sorted(duplicates)}")

    result: list[dict[str, object]] = []
    for jalali_date in sorted(grouped):
        row = grouped[jalali_date][0]
        parts = jalali_date.split("/")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise ValueError(f"Invalid Jalali date: {jalali_date!r}")
        year, month, day = map(int, parts)
        price = float(row["price_avg"].replace(",", ""))
        if price <= 0:
            raise ValueError(f"Non-positive exchange rate: {jalali_date}")
        result.append({
            "jalali_date": f"{year:04d}/{month:02d}/{day:02d}",
            "gregorian_date": parse_gregorian(row["date_gr"]),
            "jalali_year": year,
            "jalali_month": month,
            "jalali_day": day,
            "source": row["source"],
            "usd_free_market_rate_irr": price,
        })
    if len(source_rows) != 13043 or len(result) != 13042:
        raise ValueError(f"Unexpected source/output row counts: {len(source_rows)}, {len(result)}")
    if result[0]["jalali_date"] != "1360/07/07" or result[-1]["jalali_date"] != "1405/04/21":
        raise ValueError("Unexpected standardized coverage")
    return result


def validate_prior_overlap(rows: list[dict[str, object]]) -> None:
    fields, prior = read_rows(PRIOR_RAW)
    if fields != OUTPUT_FIELDS or len(prior) != 1815:
        raise ValueError("Prior standardized raw FX file changed unexpectedly")
    current = {str(row["jalali_date"]): float(row["usd_free_market_rate_irr"]) for row in rows}
    for row in prior:
        key = row["jalali_date"]
        if key not in current or current[key] != float(row["usd_free_market_rate_irr"]):
            raise ValueError(f"Conflict with prior standardized FX observation: {key}")


def update_metadata(rows: list[dict[str, object]]) -> None:
    notes = (
        "Standardized from the retained USD2Rials-1.csv source. Coverage extends backward from the prior "
        "1399 subset to 1360/07/07; all 1,815 overlapping observations match exactly. One exact duplicate "
        "source row for 1404/10/09 was removed. The historical cleaned filename is retained for compatibility."
    )
    replace_dataset_rows(ROOT / "metadata" / "data_catalog.csv", CATALOG_FIELDS, [{
        "dataset_id": DATASET_ID,
        "dataset_name": "Iran free-market USD exchange rate",
        "topic": "Macroeconomic data",
        "category": "macro",
        "subcategory": "exchange_rate",
        "category_status": "confirmed",
        "description": "Daily available-market free-market USD/IRR observations",
        "source_organization": "D-Learn archive; underlying records labeled Bourseview and TGJU",
        "source_url": SOURCE_URL,
        "collection_method": "user-supplied source CSV standardized locally",
        "date_collected": "2026-07-23",
        "original_filename": "USD2Rials-1.csv",
        "stored_filename": "USD2Rials-1.csv",
        "raw_path": relative(RAW),
        "cleaned_path": relative(CLEAN),
        "derived_path": "",
        "file_format": "CSV",
        "sheet_names": "",
        "time_coverage_start": "1360/07/07",
        "time_coverage_end": "1405/04/21",
        "frequency": "daily available-market observations",
        "geographic_coverage": "Iran free market",
        "unit": "Iranian rial per US dollar",
        "language": "English field names",
        "access_status": "source file supplied by user",
        "cleaning_status": "completed",
        "validation_status": "schema, dates, numeric positivity, unique keys, coverage, duplicate identity, and prior overlap validated",
        "current_use": "available",
        "related_task": TASK_ID,
        "confidentiality": "not marked confidential",
        "checksum_sha256": sha256(CLEAN),
        "notes": notes,
    }])

    labels = {
        "jalali_date": ("Jalali date", "YYYY/MM/DD"),
        "gregorian_date": ("Gregorian date", "YYYY-MM-DD"),
        "jalali_year": ("Jalali year", "year"),
        "jalali_month": ("Jalali month", "month number"),
        "jalali_day": ("Jalali day", "day number"),
        "source": ("Source label", "text"),
        "usd_free_market_rate_irr": ("Daily average free-market USD rate", "Iranian rial per US dollar"),
    }
    replace_dataset_rows(ROOT / "metadata" / "variable_dictionary.csv", VARIABLE_FIELDS, [{
        "dataset_id": DATASET_ID,
        "variable_name": field,
        "variable_label": labels[field][0],
        "description": labels[field][0],
        "data_type": "numeric" if field in {"jalali_year", "jalali_month", "jalali_day", "usd_free_market_rate_irr"} else "string",
        "unit": labels[field][1],
        "language": "English",
        "allowed_values": "bourseview; tgju" if field == "source" else "",
        "missing_value_codes": "none",
        "source_definition": notes,
        "notes": "Standardized locally from the retained source CSV.",
    } for field in OUTPUT_FIELDS])
    replace_dataset_rows(ROOT / "metadata" / "cleaning_log.csv", CLEANING_FIELDS, [{
        "cleaning_id": f"extend_{DATASET_ID}",
        "dataset_id": DATASET_ID,
        "date": "2026-07-23",
        "input_path": f"{relative(RAW)}; {relative(PRIOR_RAW)}",
        "output_path": relative(CLEAN),
        "script": "src/macro/process_usd_free_market_history.py",
        "transformation": "Parsed source date fields; normalized Gregorian formatting; removed one exact duplicate date; removed thousands separators; retained values and source labels.",
        "reason": "User requested extending the existing standardized daily USD/IRR history.",
        "rows_before": 13043,
        "rows_after": len(rows),
        "columns_before": 4,
        "columns_after": len(OUTPUT_FIELDS),
        "performed_by": "Codex",
        "review_status": "completed",
        "notes": "All 1,815 observations overlapping the prior standardized raw file matched exactly.",
    }])

    source_path = ROOT / "metadata" / "source_registry.csv"
    sources = read_rows(source_path)[1]
    source = {
        "source_id": "dlearn_tgju_fx",
        "source_organization": "D-Learn archive; underlying records labeled Bourseview and TGJU",
        "source_name": "Iran free-market USD price archive",
        "source_url": SOURCE_URL,
        "access_method": "source CSV supplied by user",
        "date_accessed": "2026-07-23",
        "license": "not documented; requires review",
        "access_status": "source file retained",
        "contact": "",
        "notes": "USD2Rials-1.csv is preserved byte-for-byte; 8,817 rows are labeled bourseview and 4,226 rows tgju, including one exact duplicate TGJU row.",
    }
    write_rows(source_path, SOURCE_FIELDS, [row for row in sources if row.get("source_id") != "dlearn_tgju_fx"] + [source])

    issue_path = ROOT / "metadata" / "data_issues.csv"
    issues = read_rows(issue_path)[1]
    issue = {
        "issue_id": "issue_usd_source_exact_duplicate",
        "dataset_id": DATASET_ID,
        "date_identified": "2026-07-23",
        "issue_type": "exact_duplicate_source_row",
        "description": "USD2Rials-1.csv contains two identical records for 1404/10/09 (2025-12-30), source tgju, value 1,383,400 IRR/USD.",
        "severity": "low",
        "status": "resolved",
        "resolution": "Retained one record in the cleaned unique-date series; preserved both records in immutable raw.",
        "related_file": relative(RAW),
        "notes": "No conflicting duplicate dates were found.",
    }
    write_rows(issue_path, ISSUE_FIELDS, [row for row in issues if row.get("issue_id") != issue["issue_id"]] + [issue])


def update_manifest() -> None:
    manifest = []
    for layer in ("raw", "cleaned"):
        for path in sorted((ROOT / "data" / layer).glob("**/*")):
            if path.is_file() and path.name not in {".gitkeep", "README.md"}:
                manifest.append({
                    "layer": layer,
                    "category": path.relative_to(ROOT / "data" / layer).parts[0],
                    "path": relative(path),
                    "file_format": path.suffix.lower().lstrip("."),
                    "size_bytes": path.stat().st_size,
                    "checksum_sha256": sha256(path),
                })
    write_rows(ROOT / "metadata" / "file_manifest.csv", ["layer", "category", "path", "file_format", "size_bytes", "checksum_sha256"], manifest)


def main() -> None:
    preserve_raw()
    rows = standardize()
    validate_prior_overlap(rows)
    write_rows(CLEAN, OUTPUT_FIELDS, rows)
    update_metadata(rows)
    update_manifest()
    print(f"Preserved USD2Rials-1.csv and standardized {len(rows)} unique daily USD/IRR observations.")


if __name__ == "__main__":
    main()
