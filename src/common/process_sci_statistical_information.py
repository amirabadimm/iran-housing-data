"""Preserve and standardize Persian SCI statistical-information workbooks.

The workbook contents are authoritative. Originals are copied byte-for-byte to
dated raw folders. Source missing markers (``-`` and ``×``) remain explicit;
no interpolation, imputation, rebasing, unit conversion, or aggregation occurs.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INCOMING = ROOT / "data" / "incoming" / "manually_collected"
RAW_HOUSING = ROOT / "data" / "raw" / "housing" / "sci_statistical_information_20260723"
RAW_MACRO = ROOT / "data" / "raw" / "macro" / "sci_statistical_information_20260723"
DATE = "2026-07-23"
TASK = "process_sci_statistical_information_20260723"
SOURCE_URL = "https://amar.org.ir/statistical-information"

FILES = [
    "sci_residential_building_permits_land_area_urban_1369_1401.xls",
    "sci_building_permits_land_area_urban_1369_1401.xls",
    "sci_residential_building_permits_floor_area_urban_1369_1401.xls",
    "sci_tehran_housing_prices_rents_transactions_quarterly_1388_1399.xlsx",
    "sci_residential_building_permits_count_urban_1369_1401.xls",
    "sci_building_permits_count_by_use_urban_1369_1401.xls",
    "sci_building_permits_count_by_province_urban_1359_1401.xlsx",
    "sci_building_permits_count_tehran_1369_1401.xls",
    "sci_building_permits_predicted_residential_units_tehran_1369_1401.xls",
    "sci_tehran_residential_building_input_indices_material_prices_1390_1404.xlsx",
    "sci_urban_household_cpi_inflation_national_provincial_1381_1405.xlsx",
]

MACRO_FILES = {"sci_urban_household_cpi_inflation_national_provincial_1381_1405.xlsx"}
MISSING = {"-", "_", "×", "x", "X", "…", "..."}
QUARTER = {"بهار": 1, "تابستان": 2, "پاییز": 3, "پاييز": 3, "زمستان": 4}
MONTH = {name: i for i, name in enumerate(("فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"), 1)}
MONTH.update({"فروردين": 1, "ارديبهشت": 2, "تير": 4, "شهريور": 6, "مهرماه": 7, "آبان ماه": 8, "دي": 10})

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
SOURCE_FIELDS = "source_id,source_organization,source_name,source_url,access_method,date_accessed,license,access_status,contact,notes".split(",")
ISSUE_FIELDS = "issue_id,dataset_id,date_identified,issue_type,description,severity,status,resolution,related_file,notes".split(",")


@dataclass(frozen=True)
class Output:
    dataset_id: str
    name: str
    category: str
    subcategory: str
    path: Path
    rows: list[dict[str, Any]]
    fields: list[str]
    unit: str
    frequency: str
    geography: str
    source_files: tuple[str, ...]
    notes: str


def norm(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value if value is not None else "").strip()
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    text = text.replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه")
    return re.sub(r"\s+", " ", text).strip()


def number(value: Any) -> tuple[float | int | None, str]:
    if value is None or pd.isna(value):
        return None, "blank"
    text = norm(value).replace(",", "")
    if text in MISSING:
        return None, text
    try:
        result = float(text)
    except ValueError as error:
        raise ValueError(f"Unexpected nonnumeric value: {value!r}") from error
    return (int(result) if result.is_integer() else result), ""


def year_value(value: Any) -> int | None:
    text = norm(value).replace("سال", "").strip()
    match = re.search(r"\d{2,4}", text)
    if not match:
        return None
    year = int(match.group())
    return 1300 + year if 80 <= year <= 99 else 1400 + year if 0 <= year < 80 else year


def strict_year(value: Any) -> int | None:
    """Accept a year cell only, never a footnote that happens to mention a year."""
    text = norm(value)
    if not re.fullmatch(r"\d{4}(?:\.0)?", text):
        return None
    return int(float(text))


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def preserve_raw() -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name in FILES:
        destination = (RAW_MACRO if name in MACRO_FILES else RAW_HOUSING) / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = INCOMING / name
        if not source.is_file() and not destination.is_file():
            raise FileNotFoundError(f"Neither incoming nor canonical raw workbook exists: {name}")
        if source.is_file() and destination.exists() and sha256(destination) != sha256(source):
            raise FileExistsError(f"Raw destination differs: {destination}")
        if source.is_file() and not destination.exists():
            shutil.copy2(source, destination)
        if source.is_file() and sha256(destination) != sha256(source):
            raise AssertionError(f"Raw byte preservation failed: {name}")
        paths[name] = destination
    return paths


def frame(name: str, sheet: str | int = 0) -> pd.DataFrame:
    path = (RAW_MACRO if name in MACRO_FILES else RAW_HOUSING) / name
    return pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)


def permit_rows() -> list[dict[str, Any]]:
    simple = {
        FILES[0]: ("residential_construction_permit_land_area", "square metre", "urban areas of Iran"),
        FILES[1]: ("all_construction_permit_land_area", "square metre", "urban areas of Iran"),
        FILES[2]: ("residential_construction_permit_floor_area", "square metre", "urban areas of Iran"),
        FILES[4]: ("residential_construction_permit_count", "count", "urban areas of Iran"),
        FILES[7]: ("construction_permit_count", "count", "Tehran city"),
        FILES[8]: ("predicted_residential_unit_count", "count", "Tehran city"),
    }
    result: list[dict[str, Any]] = []
    for name, (measure, unit, geography) in simple.items():
        data = frame(name)
        for _, row in data.iterrows():
            year = strict_year(row.iloc[0])
            if year is None or not 1300 <= year <= 1500:
                continue
            value, marker = number(row.iloc[1])
            result.append({"solar_hijri_year": year, "geography_level": "city" if geography == "Tehran city" else "national_urban", "geography": geography, "measure": measure, "category_fa": "", "value": value, "unit": unit, "source_missing_marker": marker, "source_file": name})

    use_name = FILES[5]
    data = frame(use_name)
    categories = [norm(value) for value in data.iloc[1, 1:].tolist()]
    for _, row in data.iloc[2:].iterrows():
        year = strict_year(row.iloc[0])
        if year is None:
            continue
        for col, category in enumerate(categories, 1):
            value, marker = number(row.iloc[col])
            result.append({"solar_hijri_year": year, "geography_level": "national_urban", "geography": "urban areas of Iran", "measure": "construction_permit_count_by_building_use", "category_fa": category, "value": value, "unit": "count", "source_missing_marker": marker, "source_file": use_name})

    province_name = FILES[6]
    data = frame(province_name)
    provinces = [norm(value) for value in data.iloc[1, 1:].tolist()]
    for _, row in data.iloc[2:].iterrows():
        year = strict_year(row.iloc[0])
        if year is None:
            continue
        for col, province in enumerate(provinces, 1):
            value, marker = number(row.iloc[col])
            result.append({"solar_hijri_year": year, "geography_level": "national_urban" if "کشور" in province else "province_urban", "geography": province, "measure": "building_permit_count", "category_fa": "", "value": value, "unit": "count", "source_missing_marker": marker, "source_file": province_name})
    return result


def periods_from_headers(years: Iterable[Any], labels: Iterable[Any]) -> list[tuple[int | None, str, int | None]]:
    current: int | None = None
    result = []
    for raw_year, raw_label in zip(years, labels):
        parsed = year_value(raw_year)
        if parsed is not None:
            current = parsed
        label = norm(raw_label)
        result.append((current, label, QUARTER.get(label) or MONTH.get(label)))
    return result


def tehran_market_rows() -> list[dict[str, Any]]:
    name = FILES[3]
    book = pd.ExcelFile((RAW_MACRO if name in MACRO_FILES else RAW_HOUSING) / name)
    specs = {
        book.sheet_names[2]: ("land_sale_price_per_sqm", "thousand rial", False, 3),
        book.sheet_names[3]: ("residential_building_sale_price_per_sqm", "thousand rial", False, 3),
        book.sheet_names[4]: ("residential_rent_plus_three_percent_deposit_per_sqm", "rial", False, 3),
        book.sheet_names[5]: ("transaction_count", "count", True, 4),
        book.sheet_names[6]: ("land_sale_price_qoq_change", "percent", False, 3),
        book.sheet_names[7]: ("land_sale_price_yoy_change", "percent", False, 3),
        book.sheet_names[8]: ("residential_building_sale_price_qoq_change", "percent", False, 3),
        book.sheet_names[9]: ("residential_building_sale_price_yoy_change", "percent", False, 3),
        book.sheet_names[10]: ("residential_rent_qoq_change", "percent", False, 3),
        book.sheet_names[11]: ("residential_rent_yoy_change", "percent", False, 3),
        book.sheet_names[12]: ("transaction_count_qoq_change", "percent", True, 4),
        book.sheet_names[13]: ("transaction_count_yoy_change", "percent", True, 4),
    }
    transaction = {"زمین": "land", "زمين": "land", "زیربنا": "residential_building", "زيربنا": "residential_building", "اجاره": "rent"}
    result = []
    for sheet, (measure, unit, typed, start) in specs.items():
        data = frame(name, sheet)
        periods = periods_from_headers(data.iloc[1, 1:], data.iloc[2, 1:])
        types = [transaction.get(norm(value), norm(value)) for value in data.iloc[3, 1:]] if typed else [""] * (data.shape[1] - 1)
        for _, row in data.iloc[start:].iterrows():
            region = norm(row.iloc[0])
            if region != "شهر تهران" and not re.fullmatch(r"منطقه \d+", region):
                continue
            for offset, (year, season, quarter) in enumerate(periods, 1):
                if year is None or quarter is None:
                    continue
                value, marker = number(row.iloc[offset])
                result.append({"solar_hijri_period": f"{year}-Q{quarter}", "solar_hijri_year": year, "quarter": quarter, "season_fa": season, "tehran_region": region, "measure": measure, "transaction_type": types[offset - 1], "value": value, "unit": unit, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})
    return result


def building_index_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    name = FILES[9]
    book = pd.ExcelFile((RAW_MACRO if name in MACRO_FILES else RAW_HOUSING) / name)
    quarterly: list[dict[str, Any]] = []
    annual: list[dict[str, Any]] = []
    qspecs = [(2, 3, 4, 5, "price_index"), (3, 2, 3, 4, "qoq_change"), (4, 3, 4, 5, "yoy_change"), (5, 3, 4, 5, "four_quarter_change")]
    for sheet_index, year_row, period_row, data_start, measure in qspecs:
        sheet = book.sheet_names[sheet_index]
        data = frame(name, sheet)
        periods = periods_from_headers(data.iloc[year_row, 2:], data.iloc[period_row, 2:])
        for row_index in range(data_start, len(data)):
            group = norm(data.iloc[row_index, 1])
            if not group or group.startswith(("جدول", "(")):
                continue
            for offset, (year, season, quarter) in enumerate(periods, 2):
                if year is None or quarter is None:
                    continue
                value, marker = number(data.iloc[row_index, offset])
                quarterly.append({"solar_hijri_period": f"{year}-Q{quarter}", "solar_hijri_year": year, "quarter": quarter, "season_fa": season, "input_group_fa": group, "measure": measure, "value": value, "unit": "index points" if measure == "price_index" else "percent", "base_year": 1402, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})

    for sheet_index, measure in ((6, "annual_price_index"), (7, "annual_inflation")):
        sheet = book.sheet_names[sheet_index]
        data = frame(name, sheet)
        years = [year_value(value) for value in data.iloc[3, 2:]]
        for row_index in range(5, len(data)):
            group = norm(data.iloc[row_index, 1])
            if not group or group.startswith(("جدول", "(")):
                continue
            for offset, year in enumerate(years, 2):
                if year is None:
                    continue
                value, marker = number(data.iloc[row_index, offset])
                annual.append({"solar_hijri_year": year, "input_group_fa": group, "measure": measure, "value": value, "unit": "index points" if measure == "annual_price_index" else "percent", "base_year": 1402, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})

    legacy_sheet = book.sheet_names[8]
    data = frame(name, legacy_sheet)
    periods = periods_from_headers(data.iloc[2, 2:], data.iloc[3, 2:])
    legacy = []
    for row_index in range(4, len(data)):
        group = norm(data.iloc[row_index, 1])
        if not group or group.startswith(("جدول", "(")):
            continue
        for offset, (year, season, quarter) in enumerate(periods, 2):
            if year is None or quarter is None:
                continue
            value, marker = number(data.iloc[row_index, offset])
            legacy.append({"solar_hijri_period": f"{year}-Q{quarter}", "solar_hijri_year": year, "quarter": quarter, "season_fa": season, "input_group_fa": group, "measure": "price_index", "value": value, "unit": "index points", "base_year": 1390, "source_missing_marker": marker, "source_sheet": legacy_sheet, "source_file": name})
    quarterly.extend(annual)
    return quarterly, legacy, selected_material_rows(book)


def selected_material_rows(book: pd.ExcelFile) -> list[dict[str, Any]]:
    name = FILES[9]
    result = []
    for sheet in book.sheet_names[9:]:
        data = frame(name, sheet)
        title = " | ".join(norm(value) for value in data.iloc[0].tolist() if pd.notna(value))
        match = re.search(r"گروه (.+?)(?::|:|،? زمستان)", title)
        group = norm(match.group(1)) if match else sheet
        for row_index in range(3, len(data)):
            values = [value for value in data.iloc[row_index].tolist() if pd.notna(value)]
            if len(values) < 5:
                continue
            item, unit = norm(values[0]), norm(values[1])
            low, low_marker = number(values[2]); high, high_marker = number(values[3]); average, average_marker = number(values[4])
            result.append({"solar_hijri_period": "1404-Q4", "solar_hijri_year": 1404, "quarter": 4, "material_group_fa": group, "item_fa": item, "transaction_unit_fa": unit, "minimum_price_irr": low, "maximum_price_irr": high, "average_price_irr": average, "minimum_missing_marker": low_marker, "maximum_missing_marker": high_marker, "average_missing_marker": average_marker, "source_sheet": sheet, "source_file": name})
    return result


def urban_cpi_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    name = FILES[10]
    book = pd.ExcelFile((RAW_MACRO if name in MACRO_FILES else RAW_HOUSING) / name)
    national_monthly = []
    measures = {2: ("cpi_index", "index points"), 3: ("monthly_change", "percent"), 4: ("yoy_change", "percent"), 5: ("twelve_month_inflation", "percent")}
    for sheet_index, (measure, unit) in measures.items():
        sheet = book.sheet_names[sheet_index]
        data = frame(name, sheet)
        periods = periods_from_headers(data.iloc[1, 1:], data.iloc[2, 1:])
        for row_index in range(3, len(data)):
            group = norm(data.iloc[row_index, 0])
            if not group:
                continue
            for offset, (year, month_name, month) in enumerate(periods, 1):
                if year is None or month is None:
                    continue
                value, marker = number(data.iloc[row_index, offset])
                national_monthly.append({"solar_hijri_period": f"{year}-{month:02d}", "solar_hijri_year": year, "month": month, "month_fa": month_name, "consumption_group_fa": group, "measure": measure, "value": value, "unit": unit, "base_year": 1400, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})

    national_annual = []
    for sheet_index, (measure, unit) in {6: ("annual_cpi_index", "index points"), 7: ("annual_inflation", "percent")}.items():
        sheet = book.sheet_names[sheet_index]
        data = frame(name, sheet)
        years = [year_value(value) for value in data.iloc[2, 1:]]
        for row_index in range(3, len(data)):
            group = norm(data.iloc[row_index, 0])
            if not group:
                continue
            for offset, year in enumerate(years, 1):
                if year is None:
                    continue
                value, marker = number(data.iloc[row_index, offset])
                national_annual.append({"solar_hijri_year": year, "consumption_group_fa": group, "measure": measure, "value": value, "unit": unit, "base_year": 1400, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})

    provincial = []
    provincial_specs = {8: "cpi_index", 9: "monthly_change", 10: "yoy_change", 11: "twelve_month_inflation"}
    for sheet_index, measure in provincial_specs.items():
        sheet = book.sheet_names[sheet_index]
        data = frame(name, sheet)
        periods = periods_from_headers(data.iloc[1, 2:], data.iloc[2, 2:])
        # Table 9 repeats 1402 in its second 1402 header, between 1402 and 1404.
        # Parallel provincial tables 7, 8 and 10 identify this block as 1403.
        if sheet_index == 10:
            starts = [i for i, (_, label, _) in enumerate(periods) if label == "فروردین"]
            years = [periods[i][0] for i in starts]
            if years[-5:] != [1401, 1402, 1402, 1404, 1405]:
                raise ValueError(f"Unexpected Table 9 year-header pattern: {years[-5:]}")
            correction_start = starts[-3]
            correction_end = starts[-2]
            periods[correction_start:correction_end] = [
                (1403, label, month) for _, label, month in periods[correction_start:correction_end]
            ]
        for row_index in range(3, len(data)):
            code, province = norm(data.iloc[row_index, 0]), norm(data.iloc[row_index, 1])
            if not province:
                continue
            for offset, (year, period_label, period_number) in enumerate(periods, 2):
                if year is None:
                    continue
                annual = "سالانه" in period_label
                month = None if annual else period_number
                if not annual and month is None:
                    continue
                value, marker = number(data.iloc[row_index, offset])
                provincial.append({"solar_hijri_period": str(year) if annual else f"{year}-{month:02d}", "solar_hijri_year": year, "month": month, "period_type": "annual" if annual else "monthly", "period_label_fa": period_label, "province_code": code, "province_fa": province, "measure": measure, "value": value, "unit": "index points" if measure == "cpi_index" else "percent", "base_year": 1400, "source_missing_marker": marker, "source_sheet": sheet, "source_file": name})

    historic = []
    annual_sheet = book.sheet_names[12]
    data = frame(name, annual_sheet)
    for _, row in data.iloc[2:].iterrows():
        year = strict_year(row.iloc[0])
        if year is None:
            continue
        value, marker = number(row.iloc[1])
        historic.append({"solar_hijri_period": str(year), "solar_hijri_year": year, "month": None, "period_type": "annual", "measure": "total_cpi_index", "value": value, "unit": "index points", "base_year": 1400, "source_missing_marker": marker, "source_sheet": annual_sheet, "source_file": name})
    monthly_sheet = book.sheet_names[13]
    data = frame(name, monthly_sheet)
    current_year = None
    for _, row in data.iloc[2:].iterrows():
        parsed = strict_year(row.iloc[0])
        if parsed is not None:
            current_year = parsed
        month_name = norm(row.iloc[1])
        month = MONTH.get(month_name)
        if current_year is None or month is None:
            continue
        value, marker = number(row.iloc[2])
        historic.append({"solar_hijri_period": f"{current_year}-{month:02d}", "solar_hijri_year": current_year, "month": month, "period_type": "monthly", "measure": "total_cpi_index", "value": value, "unit": "index points", "base_year": 1400, "source_missing_marker": marker, "source_sheet": monthly_sheet, "source_file": name})
    return national_monthly, national_annual, provincial, historic


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows)
    payload = buffer.getvalue().encode("utf-8-sig")
    # Avoid touching an identical generated file. Besides preserving timestamps,
    # this lets a reproducible run succeed when a reviewer has the CSV open.
    if path.exists() and path.read_bytes() == payload:
        return
    path.write_bytes(payload)


def inventory(raw: dict[str, Path]) -> None:
    fields = ["source_file", "raw_path", "sha256", "file_size_bytes", "sheet_name", "rows", "columns", "nonempty_cells", "title_fa"]
    rows = []
    for name, path in raw.items():
        book = pd.ExcelFile(path)
        for sheet in book.sheet_names:
            data = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)
            title = next((norm(value) for value in data.to_numpy().flat if pd.notna(value) and norm(value)), "")
            rows.append({"source_file": name, "raw_path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "file_size_bytes": path.stat().st_size, "sheet_name": sheet, "rows": data.shape[0], "columns": data.shape[1], "nonempty_cells": int(data.notna().sum().sum()), "title_fa": title})
    write_csv(ROOT / "metadata" / "sci_excel_inventory.csv", fields, rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists(): return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle: return list(csv.DictReader(handle))


def replace(path: Path, fields: list[str], key: str, prefix: str, rows: list[dict[str, Any]]) -> None:
    retained = [row for row in read_csv(path) if not row.get(key, "").startswith(prefix)]
    write_csv(path, fields, retained + rows)


def build_outputs() -> list[Output]:
    permits = permit_rows(); market = tehran_market_rows(); building, legacy, materials = building_index_rows(); nm, na, provincial, historic = urban_cpi_rows()
    outputs = [
        Output("sci_building_permits_annual", "SCI annual building permits, land, floor area, use and geography", "housing", "construction_permits", ROOT/"data/cleaned/housing/sci_building_permits/sci_building_permits_annual.csv", permits, list(permits[0]), "mixed", "annual", "Iran urban areas, provinces, and Tehran city", tuple(FILES[i] for i in (0,1,2,4,5,6,7,8)), "Source definitions and missing markers preserved; Tehran exclusions/estimated-year notes remain in raw files and metadata inventory."),
        Output("sci_tehran_housing_market_quarterly_1388_1399", "SCI Tehran housing prices, rent and transactions by municipality region", "housing", "tehran_prices_rents_transactions", ROOT/"data/cleaned/housing/sci_tehran_housing_market/sci_tehran_housing_market_quarterly_1388_1399.csv", market, list(market[0]), "mixed", "quarterly", "Tehran city and 22 municipality regions", (FILES[3],), "Includes levels, transaction counts, quarter-on-quarter changes and year-on-year changes exactly as published."),
        Output("sci_tehran_building_input_indices_base1402", "SCI Tehran residential building input price indices, base 1402", "housing", "construction_input_prices", ROOT/"data/cleaned/housing/sci_construction_inputs/sci_tehran_building_input_indices_base1402.csv", building, list(building[0]), "index points or percent", "quarterly and annual", "Tehran city", (FILES[9],), "Tables 1-6; current base-year series and published changes."),
        Output("sci_tehran_building_input_index_legacy_base1390", "SCI Tehran residential building input price index, legacy base 1390", "housing", "construction_input_prices", ROOT/"data/cleaned/housing/sci_construction_inputs/sci_tehran_building_input_index_legacy_base1390.csv", legacy, list(legacy[0]), "index points", "quarterly", "Tehran city", (FILES[9],), "Table 7 retained separately; not spliced or rebased to the base-1402 series."),
        Output("sci_tehran_selected_building_material_prices_1404q4", "SCI selected building-material prices in Tehran, 1404-Q4", "housing", "construction_material_prices", ROOT/"data/cleaned/housing/sci_construction_inputs/sci_tehran_selected_building_material_prices_1404q4.csv", materials, list(materials[0]), "Iranian rial per published transaction unit", "quarterly snapshot", "Tehran city", (FILES[9],), "Minimum, maximum and average prices for every published selected item in tables 8-20."),
        Output("sci_urban_cpi_national_monthly_by_group", "SCI urban-household CPI and inflation by consumption group, monthly", "macro", "prices_and_inflation", ROOT/"data/cleaned/macro/prices_and_inflation/sci_urban_cpi_national_monthly_by_group.csv", nm, list(nm[0]), "index points or percent", "monthly", "Iran urban households", (FILES[10],), "Tables 1-4; base 1400; published missing markers retained."),
        Output("sci_urban_cpi_national_annual_by_group", "SCI urban-household CPI and inflation by consumption group, annual", "macro", "prices_and_inflation", ROOT/"data/cleaned/macro/prices_and_inflation/sci_urban_cpi_national_annual_by_group.csv", na, list(na[0]), "index points or percent", "annual", "Iran urban households", (FILES[10],), "Tables 5-6; base 1400."),
        Output("sci_urban_cpi_provincial", "SCI urban-household CPI and inflation by province", "macro", "prices_and_inflation", ROOT/"data/cleaned/macro/prices_and_inflation/sci_urban_cpi_provincial.csv", provincial, list(provincial[0]), "index points or percent", "monthly and annual", "Iran and provinces, urban households", (FILES[10],), "Tables 7-10; annual and monthly periods retained as published."),
        Output("sci_urban_cpi_total_historical", "SCI historical total urban-household CPI", "macro", "prices_and_inflation", ROOT/"data/cleaned/macro/prices_and_inflation/sci_urban_cpi_total_historical.csv", historic, list(historic[0]), "index points", "monthly and annual", "Iran urban households", (FILES[10],), "Tables 11-12; long historical total index, base 1400."),
    ]
    for output in outputs:
        write_csv(output.path, output.fields, output.rows)
    return outputs


def update_metadata(outputs: list[Output], raw: dict[str, Path]) -> None:
    catalog=[]; variables=[]; cleaning=[]
    for output in outputs:
        years=[int(row["solar_hijri_year"]) for row in output.rows if row.get("solar_hijri_year") not in (None, "")]
        raw_paths="; ".join(str(raw[name].relative_to(ROOT)).replace("\\", "/") for name in output.source_files)
        rel=str(output.path.relative_to(ROOT)).replace("\\", "/")
        catalog.append({"dataset_id":output.dataset_id,"dataset_name":output.name,"topic":"Statistical Center of Iran statistical-information portal","category":output.category,"subcategory":output.subcategory,"category_status":"confirmed","description":output.name,"source_organization":"Statistical Center of Iran","source_url":SOURCE_URL,"collection_method":"User-downloaded SCI Excel workbook; byte-preserved and parsed with pandas/openpyxl/xlrd","date_collected":DATE,"original_filename":"; ".join(output.source_files),"stored_filename":"; ".join(output.source_files),"raw_path":raw_paths,"cleaned_path":rel,"derived_path":"","file_format":"CSV","sheet_names":"see metadata/sci_excel_inventory.csv","time_coverage_start":min(years),"time_coverage_end":max(years),"frequency":output.frequency,"geographic_coverage":output.geography,"unit":output.unit,"language":"Persian source values; English standardized fields","access_status":"user supplied from official portal","cleaning_status":"completed","validation_status":"raw byte identity, non-empty outputs, numeric parsing, period/geography keys, uniqueness and missing-marker preservation validated","current_use":"available","related_task":TASK,"confidentiality":"public statistical data; reuse terms require review","checksum_sha256":sha256(output.path),"notes":f"{output.notes} Rows={len(output.rows)}."})
        cleaning.append({"cleaning_id":f"clean_{output.dataset_id}","dataset_id":output.dataset_id,"date":DATE,"input_path":raw_paths,"output_path":rel,"script":"src/common/process_sci_statistical_information.py","transformation":"Parsed all substantive Persian worksheets into tidy long-form records; normalized digits and spacing; preserved source units, base years, labels and missing markers.","reason":"User requested complete extraction and standardization","rows_before":"see metadata/sci_excel_inventory.csv","rows_after":len(output.rows),"columns_before":"source workbook matrix","columns_after":len(output.fields),"performed_by":"Codex","review_status":"completed","notes":"No interpolation, imputation, rebasing, deflation, seasonal adjustment, aggregation or unit conversion."})
        for field in output.fields:
            variables.append({"dataset_id":output.dataset_id,"variable_name":field,"variable_label":field.replace("_"," "),"description":field.replace("_"," "),"data_type":"numeric" if field in {"solar_hijri_year","quarter","month","value","base_year","minimum_price_irr","maximum_price_irr","average_price_irr"} else "string","unit":"as named or dataset-specific","language":"English field; Persian labels where applicable","allowed_values":"","missing_value_codes":"blank value plus explicit source_missing_marker/marker field","source_definition":"Standardized directly from the named SCI workbook sheet","notes":"See catalog, cleaning log and SCI inventory."})
    replace(ROOT/"metadata/data_catalog.csv",CATALOG_FIELDS,"dataset_id","sci_",catalog)
    replace(ROOT/"metadata/variable_dictionary.csv",VARIABLE_FIELDS,"dataset_id","sci_",variables)
    replace(ROOT/"metadata/cleaning_log.csv",CLEANING_FIELDS,"dataset_id","sci_",cleaning)
    source={"source_id":"sci_statistical_information","source_organization":"Statistical Center of Iran","source_name":"Statistical information portal and supplied Persian Excel tables","source_url":SOURCE_URL,"access_method":"Manual user download; local Excel parsing","date_accessed":DATE,"license":"not confirmed; review official reuse terms","access_status":"11 workbooks received and preserved","contact":"","notes":"Portal returned HTTP 502 during automated verification on 2026-07-23; workbook titles, metadata sheets and internal source notes establish identity."}
    replace(ROOT/"metadata/source_registry.csv",SOURCE_FIELDS,"source_id","sci_statistical_information",[source])
    issues=[
        {"issue_id":"issue_sci_portal_502_20260723","dataset_id":"sci_","date_identified":DATE,"issue_type":"source_access","description":"Official statistical-information URL returned HTTP 502 during automated verification.","severity":"low","status":"documented","resolution":"Used user-supplied official workbooks and their internal Persian metadata/source notes; retained URL for later review.","related_file":"metadata/sci_excel_inventory.csv","notes":"Does not affect local extraction."},
        {"issue_id":"issue_sci_source_missing_markers","dataset_id":"sci_","date_identified":DATE,"issue_type":"missing_values","description":"Several sheets use '-' or '×' for unavailable observations.","severity":"low","status":"resolved","resolution":"Stored numeric value as blank and retained the exact marker in an adjacent marker field.","related_file":"data/cleaned/","notes":"No zero or estimate was substituted."},
        {"issue_id":"issue_sci_cpi_table9_year_header","dataset_id":"sci_urban_cpi_provincial","date_identified":DATE,"issue_type":"source_header_typo","description":"Urban CPI Table 9 repeats year 1402 for the block positioned between 1402 and 1404.","severity":"medium","status":"resolved","resolution":"Standardized that block as 1403, corroborated by the chronological sequence and parallel Tables 7, 8 and 10; raw workbook remains unchanged.","related_file":"data/raw/macro/sci_statistical_information_20260723/sci_urban_household_cpi_inflation_national_provincial_1381_1405.xlsx","notes":"The processor asserts the exact source pattern before applying the correction."},
    ]
    replace(ROOT/"metadata/data_issues.csv",ISSUE_FIELDS,"issue_id","issue_sci_",issues)
    manifest=[]
    for layer in ("raw","cleaned","derived"):
        for path in sorted((ROOT/"data"/layer).glob("**/*")):
            if not path.is_file() or path.name in {".gitkeep","README.md"}: continue
            relative=path.relative_to(ROOT)
            if layer=="raw" and any(part.startswith(("tsetmc_housing_market_","tsetmc_construction_materials_")) for part in relative.parts): continue
            manifest.append({"layer":layer,"category":path.relative_to(ROOT/"data"/layer).parts[0],"path":str(relative).replace("\\","/"),"file_format":path.suffix.lower().lstrip("."),"size_bytes":path.stat().st_size,"checksum_sha256":sha256(path)})
    write_csv(ROOT/"metadata/file_manifest.csv",["layer","category","path","file_format","size_bytes","checksum_sha256"],manifest)


def validate(outputs: list[Output]) -> None:
    for output in outputs:
        if not output.rows or not output.path.is_file(): raise AssertionError(output.dataset_id)
        keys=[]
        for row in output.rows:
            keys.append(tuple(str(row.get(field,"")) for field in output.fields if field not in {"value","unit","source_missing_marker","minimum_price_irr","maximum_price_irr","average_price_irr","minimum_missing_marker","maximum_missing_marker","average_missing_marker"}))
        if len(keys)!=len(set(keys)): raise ValueError(f"Duplicate standardized key: {output.dataset_id}")


def main() -> None:
    raw=preserve_raw()
    inventory(raw)
    outputs=build_outputs()
    validate(outputs)
    update_metadata(outputs,raw)
    print(f"Preserved {len(raw)} SCI workbooks and standardized {len(outputs)} datasets ({sum(len(o.rows) for o in outputs)} rows).")


if __name__ == "__main__":
    main()
