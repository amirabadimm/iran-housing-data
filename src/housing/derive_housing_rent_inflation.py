"""Derive quarterly housing-market and rent inflation from published CBI indices."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENT_PAIR = ROOT / "data" / "cleaned" / "housing" / "cbi_urban_tehran_pairs" / "cbi_hsg_rent_index_q.csv"
LAND_PAIR = ROOT / "data" / "cleaned" / "housing" / "cbi_urban_tehran_pairs" / "cbi_hsg_land_price_index_q.csv"
RENT_CITY_SIZE = ROOT / "data" / "cleaned" / "housing" / "cbi_non_geographic" / "cbi_hsg_rent_index_by_city_size_q.csv"
OUTPUT = ROOT / "data" / "derived" / "housing" / "inflation" / "cbi_housing_rent_inflation_quarterly.csv"
DATASET_ID = "housing_rent_inflation_cbi_quarterly"
TASK_ID = "derive_housing_rent_inflation_20260723"

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
OUTPUT_FIELDS = [
    "period", "solar_hijri_year", "quarter", "indicator", "geography_code",
    "geography_label_en", "geography_label_fa", "source_index_value",
    "qoq_inflation_pct", "yoy_inflation_pct", "source_preliminary",
    "qoq_inflation_preliminary", "yoy_inflation_preliminary", "source_dataset_id",
]


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


def bool_value(value: str) -> bool:
    if value not in {"True", "False"}:
        raise ValueError(f"Invalid Boolean value: {value!r}")
    return value == "True"


def source_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    specs = [
        (RENT_PAIR, "rent", "cbi_hsg_rent_index_q", [
            ("urban_value", "urban_preliminary", "all_urban", "All urban areas", "کليه مناطق شهري"),
            ("tehran_value", "tehran_preliminary", "tehran", "Tehran", "تهران"),
        ]),
        (LAND_PAIR, "land_price_housing_proxy", "cbi_hsg_land_price_index_q", [
            ("urban_value", "urban_preliminary", "all_urban", "All urban areas", "کليه مناطق شهري"),
            ("tehran_value", "tehran_preliminary", "tehran", "Tehran", "تهران"),
        ]),
        (RENT_CITY_SIZE, "rent", "cbi_hsg_rent_index_by_city_size_q", [
            ("large_cities_value", "large_cities_value_preliminary", "large_cities", "Large cities", "شهرهاي بزرگ"),
            ("medium_cities_value", "medium_cities_value_preliminary", "medium_cities", "Medium cities", "شهرهاي متوسط"),
            ("small_cities_value", "small_cities_value_preliminary", "small_cities", "Small cities", "شهرهاي کوچک"),
        ]),
    ]
    for path, indicator, source_dataset_id, columns in specs:
        for row in read_rows(path):
            for value_field, preliminary_field, code, label_en, label_fa in columns:
                value = float(row[value_field])
                if value <= 0:
                    raise ValueError(f"Non-positive index in {path}: {row['period']}")
                records.append({
                    "period": row["period"],
                    "solar_hijri_year": int(row["solar_hijri_year"]),
                    "quarter": int(row["quarter"]),
                    "indicator": indicator,
                    "geography_code": code,
                    "geography_label_en": label_en,
                    "geography_label_fa": label_fa,
                    "source_index_value": value,
                    "source_preliminary": bool_value(row[preliminary_field]),
                    "source_dataset_id": source_dataset_id,
                })
    return records


def derive(records: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in records:
        groups[(str(row["indicator"]), str(row["geography_code"]))].append(row)

    output: list[dict[str, object]] = []
    for group_rows in groups.values():
        group_rows.sort(key=lambda row: (int(row["solar_hijri_year"]), int(row["quarter"])))
        for index, row in enumerate(group_rows):
            current = float(row["source_index_value"])
            previous = group_rows[index - 1] if index >= 1 else None
            year_ago = group_rows[index - 4] if index >= 4 else None
            result = dict(row)
            result["qoq_inflation_pct"] = "" if previous is None else (current / float(previous["source_index_value"]) - 1) * 100
            result["yoy_inflation_pct"] = "" if year_ago is None else (current / float(year_ago["source_index_value"]) - 1) * 100
            result["qoq_inflation_preliminary"] = "" if previous is None else bool(row["source_preliminary"]) or bool(previous["source_preliminary"])
            result["yoy_inflation_preliminary"] = "" if year_ago is None else bool(row["source_preliminary"]) or bool(year_ago["source_preliminary"])
            output.append(result)
    output.sort(key=lambda row: (str(row["period"]), str(row["indicator"]), str(row["geography_code"])))
    return output


def update_metadata(rows: list[dict[str, object]]) -> None:
    source_paths = [RENT_PAIR, LAND_PAIR, RENT_CITY_SIZE]
    notes = (
        "Quarter-over-quarter inflation = 100*(index_t/index_t-1 - 1); year-over-year inflation = "
        "100*(index_t/index_t-4 - 1). Land-price inflation is a housing-market proxy, not a general "
        "dwelling-sale CPI. City-size groups retain exact CBI scopes and are not interpreted as excluding Tehran."
    )
    replace_dataset_rows(ROOT / "metadata" / "data_catalog.csv", CATALOG_FIELDS, [{
        "dataset_id": DATASET_ID,
        "dataset_name": "CBI quarterly housing-market and rent inflation by geographic scope",
        "topic": "Housing and rent inflation",
        "category": "housing",
        "subcategory": "inflation",
        "category_status": "confirmed",
        "description": "Calculated quarterly and annual changes in CBI rent and land-price indices",
        "source_organization": "Central Bank of the Islamic Republic of Iran",
        "source_url": "https://tsdview.cis.cbi.ir/single-data",
        "collection_method": "derived from registered cleaned CBI index datasets",
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
        "frequency": "quarterly",
        "geographic_coverage": "Tehran; all urban areas; large, medium, and small city groups as labeled by CBI",
        "unit": "source index points; calculated inflation in percent",
        "language": "English fields; English and Persian geography labels",
        "access_status": "derived from public-source data",
        "cleaning_status": "derived",
        "validation_status": "formula, row count, unique key, sequence, positivity, and missing-lag checks completed",
        "current_use": "available",
        "related_task": TASK_ID,
        "confidentiality": "public",
        "checksum_sha256": sha256(OUTPUT),
        "notes": notes,
    }])

    descriptions = {
        "period": ("Solar Hijri quarter", "YYYY-Qn", "string"),
        "solar_hijri_year": ("Solar Hijri year", "year", "numeric"),
        "quarter": ("Quarter number", "quarter", "numeric"),
        "indicator": ("Inflation indicator", "rent or land-price housing proxy", "string"),
        "geography_code": ("Stable geographic-scope code", "category", "string"),
        "geography_label_en": ("Geographic-scope label in English", "text", "string"),
        "geography_label_fa": ("Source geographic-scope label in Persian", "text", "string"),
        "source_index_value": ("Published CBI source index", "index points", "numeric"),
        "qoq_inflation_pct": ("Quarter-over-quarter index change", "percent", "numeric"),
        "yoy_inflation_pct": ("Year-over-year index change", "percent", "numeric"),
        "source_preliminary": ("Current source observation is preliminary", "Boolean", "string"),
        "qoq_inflation_preliminary": ("Current or previous-quarter input is preliminary", "Boolean", "string"),
        "yoy_inflation_preliminary": ("Current or year-ago input is preliminary", "Boolean", "string"),
        "source_dataset_id": ("Registered source dataset identifier", "identifier", "string"),
    }
    variable_rows = []
    for field in OUTPUT_FIELDS:
        description, unit, data_type = descriptions[field]
        variable_rows.append({
            "dataset_id": DATASET_ID,
            "variable_name": field,
            "variable_label": description,
            "description": description,
            "data_type": data_type,
            "unit": unit,
            "language": "English; Persian for geography_label_fa",
            "allowed_values": "",
            "missing_value_codes": "blank only when the required lag is unavailable",
            "source_definition": notes,
            "notes": "Derived reproducibly from the registered CBI source indices.",
        })
    replace_dataset_rows(ROOT / "metadata" / "variable_dictionary.csv", VARIABLE_FIELDS, variable_rows)

    replace_dataset_rows(ROOT / "metadata" / "cleaning_log.csv", CLEANING_FIELDS, [{
        "cleaning_id": f"derive_{DATASET_ID}",
        "dataset_id": DATASET_ID,
        "date": "2026-07-23",
        "input_path": "; ".join(relative(path) for path in source_paths),
        "output_path": relative(OUTPUT),
        "script": "src/housing/derive_housing_rent_inflation.py",
        "transformation": "Reshaped seven published index series to long form and calculated quarter-over-quarter and four-quarter percentage changes.",
        "reason": "User requested a focused Tehran and city-group housing/rent inflation dataset.",
        "rows_before": sum(len(read_rows(path)) for path in source_paths),
        "rows_after": len(rows),
        "columns_before": 25,
        "columns_after": len(OUTPUT_FIELDS),
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


def validate(rows: list[dict[str, object]]) -> None:
    keys = [(row["period"], row["indicator"], row["geography_code"]) for row in rows]
    if len(rows) != 910 or len(keys) != len(set(keys)):
        raise ValueError("Expected 910 rows with unique period/indicator/geography keys")
    if sum(row["qoq_inflation_pct"] == "" for row in rows) != 7:
        raise ValueError("Expected one unavailable quarter-over-quarter lag per series")
    if sum(row["yoy_inflation_pct"] == "" for row in rows) != 28:
        raise ValueError("Expected four unavailable year-over-year lags per series")


def main() -> None:
    rows = derive(source_records())
    validate(rows)
    write_rows(OUTPUT, OUTPUT_FIELDS, rows)
    update_metadata(rows)
    update_manifest()
    print(f"Derived {len(rows)} quarterly housing-market and rent inflation observations.")


if __name__ == "__main__":
    main()
