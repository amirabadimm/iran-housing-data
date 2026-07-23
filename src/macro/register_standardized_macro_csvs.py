"""Validate and register standardized macro CSVs received from another project.

The files in ``data/raw/macro/external_data_analysis_20260722`` are the exact
files received. They had already been standardized upstream, so this script
validates their documented schemas and copies them byte-for-byte to the cleaned
layer. It does not recalculate, interpolate, rescale, or rename any value.
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "macro" / "external_data_analysis_20260722"
CLEAN_DIR = ROOT / "data" / "cleaned" / "macro"
COLLECTED_DATE = "2026-07-22"
TASK_ID = "import_standardized_macro_20260722"

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
SOURCE_FIELDS = "source_id,source_organization,source_name,source_url,access_method,date_accessed,license,access_status,contact,notes".split(",")
ISSUE_FIELDS = "issue_id,dataset_id,date_identified,issue_type,description,severity,status,resolution,related_file,notes".split(",")


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    filename: str
    name: str
    subcategory: str
    clean_directory: str
    frequency: str
    key: str
    coverage_start: str
    coverage_end: str
    expected_rows: int
    fields: tuple[str, ...]
    numeric_fields: tuple[str, ...]
    unit: str
    source_organization: str
    source_url: str
    geographic_coverage: str
    notes: str


SPECS = (
    DatasetSpec(
        "macro_iran_cpi_inflation_monthly_1399_1404",
        "iran_cpi_inflation_monthly_1399_1404.csv",
        "Iran total CPI and published inflation measures",
        "inflation",
        "prices_and_inflation",
        "monthly",
        "period",
        "1399-01",
        "1404-12",
        72,
        ("period", "jalali_year", "jalali_month", "cpi_index_1400_100", "inflation_mom_pct", "inflation_yoy_pct", "inflation_12m_avg_pct"),
        ("jalali_year", "jalali_month", "cpi_index_1400_100", "inflation_mom_pct", "inflation_yoy_pct", "inflation_12m_avg_pct"),
        "CPI index (1400=100); inflation in percent",
        "Statistical Center of Iran",
        "https://amar.org.ir/statistical-information/statid/28579",
        "Iran; all households",
        "Already standardized upstream. Official table identity and individual values remain pending independent verification; no observation was changed here.",
    ),
    DatasetSpec(
        "macro_iran_gdp_quarterly_nominal_real_1399_1404",
        "iran_gdp_quarterly_nominal_real_1399_1404.csv",
        "Iran quarterly real and nominal GDP at basic prices",
        "gdp",
        "national_accounts",
        "quarterly",
        "period",
        "1399-Q1",
        "1404-Q4",
        24,
        ("period", "jalali_year", "quarter", "real_gdp_constant_1400_billion_rial", "nominal_gdp_current_price_billion_rial"),
        ("jalali_year", "quarter", "real_gdp_constant_1400_billion_rial", "nominal_gdp_current_price_billion_rial"),
        "billion Iranian rial; real base year 1400",
        "Statistical Center of Iran",
        "https://amar.org.ir/economic-accounts",
        "Iran",
        "Already standardized upstream from user-reported SCI Table 3 (real) and Table 1 (nominal). Table identities and values remain pending independent verification; levels are not seasonally adjusted.",
    ),
    DatasetSpec(
        "macro_iran_ikhza_risk_free_monthly_1399_1404",
        "iran_risk_free_rate_ikhza_monthly_jalali_1399_1404.csv",
        "Iran اخزا annualized risk-free-rate proxy",
        "interest_rate",
        "interest_rates/domestic",
        "monthly",
        "period",
        "1399-01",
        "1404-12",
        72,
        ("period", "jalali_year", "jalali_month", "risk_free_rate_ikhza_pct", "daily_observation_count", "instrument_day_observation_count", "aggregation_method", "rate_frequency", "source", "notes"),
        ("jalali_year", "jalali_month", "risk_free_rate_ikhza_pct", "daily_observation_count", "instrument_day_observation_count"),
        "annualized percent reported monthly",
        "Tehran Securities Exchange Technology Management Co. (TSETMC)",
        "https://www.tsetmc.com/",
        "Iran government debt market",
        "Monthly median of daily transaction-value-weighted annualized zero-coupon YTM. Upstream raw API responses and instrument-level files were not retained; future reconstruction requires new retrieval from documented endpoints.",
    ),
    DatasetSpec(
        "macro_us_federal_funds_effective_monthly_jalali_1399_1404",
        "us_federal_funds_effective_rate_monthly_jalali_1399_1404.csv",
        "US Federal Funds Effective Rate aligned to Jalali months",
        "interest_rate",
        "interest_rates/international",
        "monthly",
        "period",
        "1399-01",
        "1404-12",
        72,
        ("period", "jalali_year", "jalali_month", "gregorian_start", "gregorian_end", "fed_funds_effective_rate_pct"),
        ("jalali_year", "jalali_month", "fed_funds_effective_rate_pct"),
        "percent; not seasonally adjusted",
        "Board of Governors of the Federal Reserve System via FRED",
        "https://fred.stlouisfed.org/series/FEDFUNDS",
        "United States",
        "Approximate Jalali-month rate calculated upstream by day-overlap weighting Gregorian monthly FEDFUNDS averages. Exact Jalali averages would require daily EFFR; the original FRED download is not present here.",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    raw = path.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"Expected UTF-8 BOM: {path}")
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
    existing = []
    if path.exists():
        _, existing = read_rows(path)
    ids = {str(row["dataset_id"]) for row in new_rows}
    retained = [row for row in existing if row.get("dataset_id") not in ids]
    write_rows(path, fields, retained + new_rows)


def expected_periods(spec: DatasetSpec) -> list[str] | None:
    if spec.frequency == "monthly":
        sy, sm = map(int, spec.coverage_start.split("-"))
        ey, em = map(int, spec.coverage_end.split("-"))
        result = []
        year, month = sy, sm
        while (year, month) <= (ey, em):
            result.append(f"{year:04d}-{month:02d}")
            month += 1
            if month == 13:
                year, month = year + 1, 1
        return result
    if spec.frequency == "quarterly":
        sy, sq = int(spec.coverage_start[:4]), int(spec.coverage_start[-1])
        ey, eq = int(spec.coverage_end[:4]), int(spec.coverage_end[-1])
        result = []
        year, quarter = sy, sq
        while (year, quarter) <= (ey, eq):
            result.append(f"{year:04d}-Q{quarter}")
            quarter += 1
            if quarter == 5:
                year, quarter = year + 1, 1
        return result
    return None


def validate(spec: DatasetSpec, path: Path) -> tuple[list[str], list[dict[str, str]]]:
    fields, rows = read_rows(path)
    if tuple(fields) != spec.fields:
        raise ValueError(f"Schema mismatch for {path.name}: {fields}")
    if len(rows) != spec.expected_rows:
        raise ValueError(f"Row-count mismatch for {path.name}: {len(rows)}")
    keys = [row[spec.key] for row in rows]
    if len(keys) != len(set(keys)) or keys != sorted(keys):
        raise ValueError(f"Keys are duplicated or unordered in {path.name}")
    if keys[0] != spec.coverage_start or keys[-1] != spec.coverage_end:
        raise ValueError(f"Coverage mismatch for {path.name}: {keys[0]} to {keys[-1]}")
    expected = expected_periods(spec)
    if expected is not None and keys != expected:
        raise ValueError(f"Period sequence is incomplete in {path.name}")
    for row_number, row in enumerate(rows, start=2):
        if None in row or any((row[field] == "" and field != "notes") for field in fields):
            raise ValueError(f"Unexpected missing value in {path.name}, row {row_number}")
        for field in spec.numeric_fields:
            try:
                float(row[field])
            except ValueError as error:
                raise ValueError(f"Non-numeric {field} in {path.name}, row {row_number}") from error
    if spec.frequency == "daily":
        if not all(re.fullmatch(r"\d{4}/\d{2}/\d{2}", key) for key in keys):
            raise ValueError(f"Invalid Jalali daily key in {path.name}")
    return fields, rows


def variable_metadata(spec: DatasetSpec, field: str) -> tuple[str, str]:
    units = {
        "cpi_index_1400_100": ("Total CPI, base 1400=100", "index"),
        "inflation_mom_pct": ("Month-over-month inflation", "percent"),
        "inflation_yoy_pct": ("Point-to-point/year-over-year inflation", "percent"),
        "inflation_12m_avg_pct": ("Twelve-month-average inflation", "percent"),
        "usd_free_market_rate_irr": ("Daily average free-market USD rate", "Iranian rial per US dollar"),
        "real_gdp_constant_1400_billion_rial": ("Real GDP at basic prices, constant 1400 prices", "billion Iranian rial"),
        "nominal_gdp_current_price_billion_rial": ("Nominal GDP at basic prices, current prices", "billion Iranian rial"),
        "risk_free_rate_ikhza_pct": ("Annualized اخزا risk-free-rate proxy", "annualized percent"),
        "daily_observation_count": ("Valid daily market-rate observations in month", "count"),
        "instrument_day_observation_count": ("Valid instrument-day observations in month", "count"),
        "fed_funds_effective_rate_pct": ("Federal Funds Effective Rate aligned to Jalali month", "percent"),
    }
    return units.get(field, (field.replace("_", " "), "identifier or metadata"))


def main() -> None:
    catalog_rows: list[dict[str, object]] = []
    variable_rows: list[dict[str, object]] = []
    cleaning_rows: list[dict[str, object]] = []

    for spec in SPECS:
        raw_path = RAW_DIR / spec.filename
        fields, rows = validate(spec, raw_path)
        clean_path = CLEAN_DIR / spec.clean_directory / spec.filename
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        if clean_path.exists() and sha256(clean_path) != sha256(raw_path):
            raise FileExistsError(f"Cleaned destination differs and will not be overwritten: {clean_path}")
        if not clean_path.exists():
            shutil.copy2(raw_path, clean_path)
        validate(spec, clean_path)
        if sha256(clean_path) != sha256(raw_path):
            raise AssertionError(f"Byte identity failed for {spec.filename}")

        catalog_rows.append({
            "dataset_id": spec.dataset_id,
            "dataset_name": spec.name,
            "topic": "Macroeconomic data",
            "category": "macro",
            "subcategory": spec.subcategory,
            "category_status": "confirmed",
            "description": spec.name,
            "source_organization": spec.source_organization,
            "source_url": spec.source_url,
            "collection_method": "imported standardized CSV from another user project",
            "date_collected": COLLECTED_DATE,
            "original_filename": spec.filename,
            "stored_filename": spec.filename,
            "raw_path": relative(raw_path),
            "cleaned_path": relative(clean_path),
            "derived_path": "",
            "file_format": "CSV",
            "sheet_names": "",
            "time_coverage_start": spec.coverage_start,
            "time_coverage_end": spec.coverage_end,
            "frequency": spec.frequency,
            "geographic_coverage": spec.geographic_coverage,
            "unit": spec.unit,
            "language": "English field names; Persian content where applicable",
            "access_status": "received from user's other project",
            "cleaning_status": "completed",
            "validation_status": "schema, encoding, coverage, keys, missingness, numeric fields, and byte identity validated",
            "current_use": "available",
            "related_task": TASK_ID,
            "confidentiality": "not marked confidential",
            "checksum_sha256": sha256(clean_path),
            "notes": spec.notes,
        })

        for field in fields:
            label, unit = variable_metadata(spec, field)
            variable_rows.append({
                "dataset_id": spec.dataset_id,
                "variable_name": field,
                "variable_label": label,
                "description": label,
                "data_type": "numeric" if field in spec.numeric_fields else "string",
                "unit": unit,
                "language": "English",
                "allowed_values": "",
                "missing_value_codes": "blank; only notes is intentionally blank",
                "source_definition": spec.notes,
                "notes": "Field retained exactly from the received standardized CSV.",
            })

        cleaning_rows.append({
            "cleaning_id": f"register_{spec.dataset_id}",
            "dataset_id": spec.dataset_id,
            "date": COLLECTED_DATE,
            "input_path": relative(raw_path),
            "output_path": relative(clean_path),
            "script": "src/macro/register_standardized_macro_csvs.py",
            "transformation": "Validated and copied byte-for-byte; no value, field, date, unit, or missing-value transformation.",
            "reason": "User requested integration and standardization; received files already conformed to the project CSV standard.",
            "rows_before": len(rows),
            "rows_after": len(rows),
            "columns_before": len(fields),
            "columns_after": len(fields),
            "performed_by": "Codex",
            "review_status": "completed",
            "notes": "Upstream processing and limitations are documented in the catalog and methodology notes.",
        })

    replace_dataset_rows(ROOT / "metadata" / "data_catalog.csv", CATALOG_FIELDS, catalog_rows)
    replace_dataset_rows(ROOT / "metadata" / "variable_dictionary.csv", VARIABLE_FIELDS, variable_rows)
    replace_dataset_rows(ROOT / "metadata" / "cleaning_log.csv", CLEANING_FIELDS, cleaning_rows)

    source_rows = [
        {"source_id": "sci_cpi", "source_organization": "Statistical Center of Iran", "source_name": "Total CPI and inflation tables", "source_url": "https://amar.org.ir/statistical-information/statid/28579", "access_method": "standardized CSV received from user's other project", "date_accessed": COLLECTED_DATE, "license": "not documented; requires review", "access_status": "provenance pending independent verification", "contact": "", "notes": "User-reported official table identities; page/value verification was not completed upstream."},
        {"source_id": "sci_gdp", "source_organization": "Statistical Center of Iran", "source_name": "Economic Accounts GDP tables", "source_url": "https://amar.org.ir/economic-accounts", "access_method": "standardized CSV received from user's other project", "date_accessed": COLLECTED_DATE, "license": "not documented; requires review", "access_status": "provenance pending independent verification", "contact": "", "notes": "User-reported Table 3 constant-price and Table 1 current-price GDP at basic prices."},
        {"source_id": "tsetmc_ikhza", "source_organization": "TSETMC", "source_name": "اخزا instrument metadata and daily histories", "source_url": "https://www.tsetmc.com/", "access_method": "upstream API-derived standardized CSV", "date_accessed": "2026-07-18", "license": "not documented; requires review", "access_status": "final aggregate received; upstream raw responses absent", "contact": "", "notes": "Endpoint templates and aggregation method are documented in docs/methodology_notes.md."},
        {"source_id": "fred_fedfunds", "source_organization": "Federal Reserve Bank of St. Louis / Board of Governors", "source_name": "Federal Funds Effective Rate (FEDFUNDS)", "source_url": "https://fred.stlouisfed.org/series/FEDFUNDS", "access_method": "upstream processed monthly series aligned to Jalali months", "date_accessed": "2026-07-18", "license": "review FRED series notes and terms", "access_status": "processed file received; original download absent", "contact": "", "notes": "Day-overlap-weighted conversion from Gregorian monthly averages; approximate Jalali-month values."},
    ]
    existing_sources = []
    source_path = ROOT / "metadata" / "source_registry.csv"
    if source_path.exists():
        _, existing_sources = read_rows(source_path)
    source_ids = {row["source_id"] for row in source_rows}
    write_rows(source_path, SOURCE_FIELDS, [row for row in existing_sources if row.get("source_id") not in source_ids] + source_rows)

    issue_rows = [
        {"issue_id": "issue_imported_macro_sci_provenance", "dataset_id": "macro_iran_cpi_inflation_monthly_1399_1404; macro_iran_gdp_quarterly_nominal_real_1399_1404", "date_identified": COLLECTED_DATE, "issue_type": "provenance_requires_review", "description": "SCI table identities and individual values are documented from the prior project but were not independently verified against the live official pages.", "severity": "medium", "status": "open", "resolution": "Verify the retained CPI and GDP values against the cited SCI publications when the pages are accessible.", "related_file": "data/raw/macro/external_data_analysis_20260722/", "notes": "Do not alter received values during verification; record any revised official release separately."},
        {"issue_id": "issue_imported_macro_upstream_raw_absent", "dataset_id": "macro_iran_ikhza_risk_free_monthly_1399_1404; macro_us_federal_funds_effective_monthly_jalali_1399_1404", "date_identified": COLLECTED_DATE, "issue_type": "upstream_raw_not_available", "description": "The received standardized CSVs are preserved, but their original API-response or instrument-level inputs were not retained in the other project.", "severity": "medium", "status": "open", "resolution": "For a future refresh, reacquire and preserve upstream raw responses with retrieval timestamps and checksums.", "related_file": "data/raw/macro/external_data_analysis_20260722/", "notes": "Current received files remain usable; limitation concerns full upstream reconstruction. The USD source file was subsequently supplied and is managed by process_usd_free_market_history.py."},
    ]
    issue_path = ROOT / "metadata" / "data_issues.csv"
    existing_issues = []
    if issue_path.exists():
        _, existing_issues = read_rows(issue_path)
    issue_ids = {row["issue_id"] for row in issue_rows}
    write_rows(issue_path, ISSUE_FIELDS, [row for row in existing_issues if row.get("issue_id") not in issue_ids] + issue_rows)

    manifest_rows = []
    for layer in ("raw", "cleaned"):
        for path in sorted((ROOT / "data" / layer).glob("**/*")):
            if path.is_file() and path.name not in {".gitkeep", "README.md"}:
                manifest_rows.append({"layer": layer, "category": path.relative_to(ROOT / "data" / layer).parts[0], "path": relative(path), "file_format": path.suffix.lower().lstrip("."), "size_bytes": path.stat().st_size, "checksum_sha256": sha256(path)})
    write_rows(ROOT / "metadata" / "file_manifest.csv", ["layer", "category", "path", "file_format", "size_bytes", "checksum_sha256"], manifest_rows)
    print(f"Validated and registered {len(SPECS)} standardized macro datasets.")


if __name__ == "__main__":
    main()
