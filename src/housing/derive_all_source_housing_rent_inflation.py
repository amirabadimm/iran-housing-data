"""Combine all relevant registered CBI and SCI housing/rent inflation measures."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CBI = ROOT / "data" / "derived" / "housing" / "inflation" / "cbi_housing_rent_inflation_quarterly.csv"
SCI_TEHRAN = ROOT / "data" / "cleaned" / "housing" / "sci_tehran_housing_market" / "sci_tehran_housing_market_quarterly_1388_1399.csv"
SCI_INPUTS = ROOT / "data" / "cleaned" / "housing" / "sci_construction_inputs" / "sci_tehran_building_input_indices_base1402.csv"
SCI_CPI_MONTHLY = ROOT / "data" / "cleaned" / "macro" / "prices_and_inflation" / "sci_urban_cpi_national_monthly_by_group.csv"
SCI_CPI_ANNUAL = ROOT / "data" / "cleaned" / "macro" / "prices_and_inflation" / "sci_urban_cpi_national_annual_by_group.csv"
OUTPUT = ROOT / "data" / "derived" / "housing" / "inflation" / "housing_rent_inflation_all_sources.csv"
DATASET_ID = "housing_rent_inflation_all_sources"
TASK_ID = "derive_housing_rent_inflation_all_sources_20260723"

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
FIELDS = [
    "period", "solar_hijri_year", "month", "quarter", "frequency", "indicator",
    "component_fa", "geography_level", "geography_code", "geography_label_fa",
    "inflation_measure", "inflation_pct", "rate_status", "provider",
    "source_dataset_id", "source_measure", "source_file", "notes",
]

HOUSING = "\u0645\u0633\u06a9\u0646"
RENT = "\u0627\u062c\u0627\u0631\u0647"
HOUSING_UTILITIES = "04 - \u0645\u0633\u06a9\u0646 \u060c \u0622\u0628 \u060c \u0628\u0631\u0642 \u060c \u06af\u0627\u0632 \u0648 \u0633\u0627\u06cc\u0631 \u0633\u0648\u062e\u062a\u200c\u0647\u0627"
HOUSING_MAINTENANCE = "043 - \u062e\u062f\u0645\u0627\u062a \u0646\u06af\u0647\u062f\u0627\u0631\u06cc \u0648 \u062a\u0639\u0645\u06cc\u0631 \u0648\u0627\u062d\u062f \u0645\u0633\u06a9\u0648\u0646\u06cc (\u062e\u062f\u0645\u062a )"
CPI_GROUPS = {HOUSING, RENT, HOUSING_UTILITIES, HOUSING_MAINTENANCE}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def replace_dataset_rows(path: Path, fields: list[str], new_rows: list[dict[str, object]]) -> None:
    existing = read_rows(path) if path.exists() else []
    write_rows(path, fields, [row for row in existing if row.get("dataset_id") != DATASET_ID] + new_rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def base_row(**values: object) -> dict[str, object]:
    row = {field: "" for field in FIELDS}
    row.update(values)
    return row


def cbi_rows() -> list[dict[str, object]]:
    result = []
    measure_fields = [
        ("qoq_inflation_pct", "qoq_change"),
        ("yoy_inflation_pct", "yoy_change"),
    ]
    for source in read_rows(CBI):
        for field, measure in measure_fields:
            if source[field] == "":
                continue
            indicator = "rent" if source["indicator"] == "rent" else "land_price_housing_proxy"
            result.append(base_row(
                period=source["period"],
                solar_hijri_year=source["solar_hijri_year"],
                quarter=source["quarter"],
                frequency="quarterly",
                indicator=indicator,
                component_fa="شاخص کرايه مسکن اجاره اي" if indicator == "rent" else "شاخص قيمت زمين",
                geography_level="CBI geographic scope",
                geography_code=source["geography_code"],
                geography_label_fa=source["geography_label_fa"],
                inflation_measure=measure,
                inflation_pct=source[field],
                rate_status="calculated_from_published_index",
                provider="Central Bank of the Islamic Republic of Iran",
                source_dataset_id=source["source_dataset_id"],
                source_measure=source["indicator"],
                notes="CBI city-size groups retain source scopes and are not interpreted as excluding Tehran.",
            ))
    return result


def sci_tehran_rows() -> list[dict[str, object]]:
    mapping = {
        "land_sale_price_qoq_change": ("land_price_housing_proxy", "qoq_change"),
        "land_sale_price_yoy_change": ("land_price_housing_proxy", "yoy_change"),
        "residential_building_sale_price_qoq_change": ("residential_sale_price", "qoq_change"),
        "residential_building_sale_price_yoy_change": ("residential_sale_price", "yoy_change"),
        "residential_rent_qoq_change": ("rent", "qoq_change"),
        "residential_rent_yoy_change": ("rent", "yoy_change"),
    }
    result = []
    for source in read_rows(SCI_TEHRAN):
        if source["measure"] not in mapping or source["value"] == "":
            continue
        indicator, measure = mapping[source["measure"]]
        region = source["tehran_region"]
        result.append(base_row(
            period=source["solar_hijri_period"],
            solar_hijri_year=source["solar_hijri_year"],
            quarter=source["quarter"],
            frequency="quarterly",
            indicator=indicator,
            component_fa=source["measure"],
            geography_level="Tehran municipality region",
            geography_code="tehran_total" if region == "شهر تهران" else f"tehran_region_{region.split()[-1]}",
            geography_label_fa=region,
            inflation_measure=measure,
            inflation_pct=source["value"],
            rate_status="published",
            provider="Statistical Center of Iran",
            source_dataset_id="sci_tehran_housing_market_quarterly_1388_1399",
            source_measure=source["measure"],
            source_file=source["source_file"],
            notes="Published SCI change; source missing observations remain excluded.",
        ))
    return result


def cpi_indicator(group: str) -> str:
    return {
        HOUSING: "housing_cpi",
        RENT: "rent_cpi",
        HOUSING_UTILITIES: "housing_utilities_cpi",
        HOUSING_MAINTENANCE: "housing_maintenance_cpi",
    }[group]


def sci_cpi_rows() -> list[dict[str, object]]:
    measure_map = {
        "monthly_change": "mom_change",
        "yoy_change": "yoy_change",
        "twelve_month_inflation": "twelve_month_inflation",
    }
    result = []
    for source in read_rows(SCI_CPI_MONTHLY):
        group = source["consumption_group_fa"]
        if group not in CPI_GROUPS or source["measure"] not in measure_map or source["value"] == "":
            continue
        result.append(base_row(
            period=source["solar_hijri_period"],
            solar_hijri_year=source["solar_hijri_year"],
            month=source["month"],
            frequency="monthly",
            indicator=cpi_indicator(group),
            component_fa=group,
            geography_level="national urban households",
            geography_code="iran_urban",
            geography_label_fa="خانوارهای شهری کشور",
            inflation_measure=measure_map[source["measure"]],
            inflation_pct=source["value"],
            rate_status="published",
            provider="Statistical Center of Iran",
            source_dataset_id="sci_urban_cpi_national_monthly_by_group",
            source_measure=source["measure"],
            source_file=source["source_file"],
            notes=f"Published urban CPI component; base year {source['base_year']}.",
        ))
    for source in read_rows(SCI_CPI_ANNUAL):
        group = source["consumption_group_fa"]
        if group not in CPI_GROUPS or source["measure"] != "annual_inflation" or source["value"] == "":
            continue
        result.append(base_row(
            period=source["solar_hijri_year"],
            solar_hijri_year=source["solar_hijri_year"],
            frequency="annual",
            indicator=cpi_indicator(group),
            component_fa=group,
            geography_level="national urban households",
            geography_code="iran_urban",
            geography_label_fa="خانوارهای شهری کشور",
            inflation_measure="annual_inflation",
            inflation_pct=source["value"],
            rate_status="published",
            provider="Statistical Center of Iran",
            source_dataset_id="sci_urban_cpi_national_annual_by_group",
            source_measure=source["measure"],
            source_file=source["source_file"],
            notes=f"Published annual urban CPI component inflation; base year {source['base_year']}.",
        ))
    return result


def sci_construction_rows() -> list[dict[str, object]]:
    measure_map = {
        "qoq_change": ("quarterly", "qoq_change"),
        "yoy_change": ("quarterly", "yoy_change"),
        "four_quarter_change": ("quarterly", "four_quarter_inflation"),
        "annual_inflation": ("annual", "annual_inflation"),
    }
    result = []
    for source in read_rows(SCI_INPUTS):
        if source["measure"] not in measure_map or source["value"] == "":
            continue
        frequency, measure = measure_map[source["measure"]]
        period = source["solar_hijri_period"] or source["solar_hijri_year"]
        result.append(base_row(
            period=period,
            solar_hijri_year=source["solar_hijri_year"],
            quarter=source["quarter"],
            frequency=frequency,
            indicator="residential_construction_input_cost",
            component_fa=source["input_group_fa"],
            geography_level="Tehran",
            geography_code="tehran",
            geography_label_fa="تهران",
            inflation_measure=measure,
            inflation_pct=source["value"],
            rate_status="published",
            provider="Statistical Center of Iran",
            source_dataset_id="sci_tehran_building_input_indices_base1402",
            source_measure=source["measure"],
            source_file=source["source_file"],
            notes=f"Published Tehran residential construction-input measure; base year {source['base_year']}.",
        ))
    return result


def build_rows() -> list[dict[str, object]]:
    rows = cbi_rows() + sci_tehran_rows() + sci_cpi_rows() + sci_construction_rows()
    rows.sort(key=lambda row: (
        int(row["solar_hijri_year"]), str(row["period"]), str(row["provider"]),
        str(row["indicator"]), str(row["geography_code"]), str(row["inflation_measure"]),
        str(row["component_fa"]),
    ))
    return rows


def validate(rows: list[dict[str, object]]) -> None:
    if not rows or any(float(row["inflation_pct"]) != float(row["inflation_pct"]) for row in rows):
        raise ValueError("Missing or non-numeric inflation value")
    providers = {row["provider"] for row in rows}
    if providers != {"Central Bank of the Islamic Republic of Iran", "Statistical Center of Iran"}:
        raise ValueError(f"Unexpected provider set: {providers}")
    required_sources = {
        "cbi_hsg_rent_index_q",
        "cbi_hsg_land_price_index_q",
        "cbi_hsg_rent_index_by_city_size_q",
        "sci_tehran_housing_market_quarterly_1388_1399",
        "sci_urban_cpi_national_monthly_by_group",
        "sci_urban_cpi_national_annual_by_group",
        "sci_tehran_building_input_indices_base1402",
    }
    actual_sources = {str(row["source_dataset_id"]) for row in rows}
    if not required_sources.issubset(actual_sources):
        raise ValueError(f"Missing relevant source datasets: {sorted(required_sources - actual_sources)}")


def update_metadata(rows: list[dict[str, object]]) -> None:
    source_paths = [CBI, SCI_TEHRAN, SCI_INPUTS, SCI_CPI_MONTHLY, SCI_CPI_ANNUAL]
    notes = (
        "Combines calculated CBI rent/land-index changes with published SCI Tehran housing-market, "
        "urban housing/rent CPI, and residential construction-input inflation. Provincial SCI total CPI "
        "is excluded because it is not housing-specific; the single-quarter material-price snapshot cannot "
        "support an inflation calculation. Definitions, frequencies, and source scopes remain separate."
    )
    replace_dataset_rows(ROOT / "metadata" / "data_catalog.csv", CATALOG_FIELDS, [{
        "dataset_id": DATASET_ID,
        "dataset_name": "All-source Iran housing and rent inflation panel",
        "topic": "Housing and rent inflation",
        "category": "housing",
        "subcategory": "inflation",
        "category_status": "confirmed",
        "description": "Analysis-ready long panel of relevant CBI and SCI housing, rent, land, and construction-input inflation measures",
        "source_organization": "Central Bank of Iran; Statistical Center of Iran",
        "source_url": "https://tsdview.cis.cbi.ir/single-data; https://amar.org.ir/statistical-information",
        "collection_method": "combined from registered cleaned and derived datasets",
        "date_collected": "2026-07-23",
        "original_filename": "",
        "stored_filename": OUTPUT.name,
        "raw_path": "",
        "cleaned_path": "",
        "derived_path": relative(OUTPUT),
        "file_format": "CSV",
        "sheet_names": "",
        "time_coverage_start": min(str(row["period"]) for row in rows),
        "time_coverage_end": max(str(row["period"]) for row in rows),
        "frequency": "monthly; quarterly; annual",
        "geographic_coverage": "Iran urban households; Tehran and its municipal regions; CBI urban and city-size scopes",
        "unit": "percent",
        "language": "English fields; Persian source labels",
        "access_status": "derived from public-source data",
        "cleaning_status": "derived",
        "validation_status": "source inclusion, numeric values, provider coverage, and schema validated",
        "current_use": "preferred all-source housing/rent inflation panel",
        "related_task": TASK_ID,
        "confidentiality": "public",
        "checksum_sha256": sha256(OUTPUT),
        "notes": notes,
    }])

    variable_rows = []
    numeric = {"solar_hijri_year", "month", "quarter", "inflation_pct"}
    for field in FIELDS:
        variable_rows.append({
            "dataset_id": DATASET_ID,
            "variable_name": field,
            "variable_label": field.replace("_", " "),
            "description": field.replace("_", " "),
            "data_type": "numeric" if field in numeric else "string",
            "unit": "percent" if field == "inflation_pct" else "identifier or source metadata",
            "language": "English; Persian in *_fa fields",
            "allowed_values": "",
            "missing_value_codes": "blank where not applicable to the source frequency",
            "source_definition": notes,
            "notes": "Provider, source dataset, frequency, rate status, and original source measure identify comparability.",
        })
    replace_dataset_rows(ROOT / "metadata" / "variable_dictionary.csv", VARIABLE_FIELDS, variable_rows)
    replace_dataset_rows(ROOT / "metadata" / "cleaning_log.csv", CLEANING_FIELDS, [{
        "cleaning_id": f"derive_{DATASET_ID}",
        "dataset_id": DATASET_ID,
        "date": "2026-07-23",
        "input_path": "; ".join(relative(path) for path in source_paths),
        "output_path": relative(OUTPUT),
        "script": "src/housing/derive_all_source_housing_rent_inflation.py",
        "transformation": "Selected relevant published/calculated inflation measures and standardized them to one long schema without changing rates.",
        "reason": "User requested one housing/rent inflation file using all relevant CBI/TSD and SCI sources.",
        "rows_before": sum(len(read_rows(path)) for path in source_paths),
        "rows_after": len(rows),
        "columns_before": "",
        "columns_after": len(FIELDS),
        "performed_by": "Codex",
        "review_status": "completed",
        "notes": notes,
    }])


def update_manifest() -> None:
    manifest = []
    for layer in ("raw", "cleaned", "derived"):
        for path in sorted((ROOT / "data" / layer).glob("**/*")):
            if path.is_file() and path.name not in {".gitkeep", "README.md"}:
                rel = path.relative_to(ROOT)
                if layer == "raw" and any(part.startswith(("tsetmc_housing_market_", "tsetmc_construction_materials_")) for part in rel.parts):
                    continue
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
    rows = build_rows()
    validate(rows)
    write_rows(OUTPUT, FIELDS, rows)
    update_metadata(rows)
    update_manifest()
    print(f"Derived {len(rows)} all-source housing and rent inflation observations.")


if __name__ == "__main__":
    main()
