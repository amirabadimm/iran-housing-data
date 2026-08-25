"""Validate repository manifests, catalog paths, and key standardized datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate() -> dict[str, object]:
    errors: list[str] = []
    manifest = rows(ROOT / "metadata" / "file_manifest.csv")
    for item in manifest:
        path = ROOT / item["path"]
        if not path.is_file():
            errors.append(f"manifest missing: {item['path']}")
        elif digest(path) != item["checksum_sha256"]:
            errors.append(f"manifest checksum mismatch: {item['path']}")

    catalog = rows(ROOT / "metadata" / "data_catalog.csv")
    ids = [item["dataset_id"] for item in catalog]
    if len(ids) != len(set(ids)):
        errors.append("duplicate dataset_id in data catalog")
    for item in catalog:
        for field in ("cleaned_path", "derived_path"):
            if item.get(field) and not (ROOT / item[field]).is_file():
                errors.append(f"catalog missing {field}: {item[field]}")

    expected_sci = {
        "sci_building_permits_annual",
        "sci_tehran_housing_market_quarterly_1388_1399",
        "sci_tehran_building_input_indices_base1402",
        "sci_tehran_building_input_index_legacy_base1390",
        "sci_tehran_selected_building_material_prices_1404q4",
        "sci_urban_cpi_national_monthly_by_group",
        "sci_urban_cpi_national_annual_by_group",
        "sci_urban_cpi_provincial",
        "sci_urban_cpi_total_historical",
    }
    actual_sci = {item["dataset_id"] for item in catalog if item["dataset_id"].startswith("sci_")}
    if actual_sci != expected_sci:
        errors.append(f"SCI catalog set mismatch: {sorted(actual_sci ^ expected_sci)}")
    sci_inventory = rows(ROOT / "metadata" / "sci_excel_inventory.csv")
    if len(sci_inventory) != 58 or len({item["source_file"] for item in sci_inventory}) != 11:
        errors.append("SCI inventory must contain 58 sheets from 11 workbooks")

    expected_cbi_national_accounts = {
        "cbi_macro_building_gfcf_private_current_a",
        "cbi_macro_building_gfcf_public_current_a",
        "cbi_macro_real_estate_value_added_current_a",
        "cbi_macro_building_gfcf_private_constant_1400_a",
        "cbi_macro_building_gfcf_public_constant_1400_a",
        "cbi_macro_real_estate_value_added_constant_1400_a",
    }
    actual_cbi = {item["dataset_id"] for item in catalog if item["dataset_id"].startswith("cbi_")}
    if len(actual_cbi) != 28 or not expected_cbi_national_accounts.issubset(actual_cbi):
        errors.append("CBI catalog must contain 28 datasets including the six annual national-accounts series")
    cbi_inventory = rows(ROOT / "metadata" / "excel_series_inventory.csv")
    national_accounts_inventory = [
        item for item in cbi_inventory if item["source_file"] == "cbi_building_investment_real_estate_value_added_national_accounts_annual_1395_1402.xlsx"
    ]
    if len({item["source_file"] for item in cbi_inventory}) != 19:
        errors.append("CBI inventory must cover 19 workbooks")
    if len(national_accounts_inventory) != 12:
        errors.append("New CBI annual workbook must inventory all 12 labeled data columns")
    elif sum(item["status"] == "available" for item in national_accounts_inventory) != 6:
        errors.append("New CBI annual workbook must contain six available and six empty series")

    fx_path = ROOT / "data" / "cleaned" / "macro" / "exchange_rates" / "iran_daily_usd_free_market_rate_1399_1405.csv"
    fx_rows = rows(fx_path)
    fx_keys = [item["jalali_date"] for item in fx_rows]
    if len(fx_rows) != 13042 or len(fx_keys) != len(set(fx_keys)):
        errors.append("Extended USD/IRR series must contain 13,042 unique daily observations")
    elif fx_keys[0] != "1360/07/07" or fx_keys[-1] != "1405/04/21":
        errors.append("Extended USD/IRR coverage must be 1360/07/07 through 1405/04/21")
    if any(float(item["usd_free_market_rate_irr"]) <= 0 for item in fx_rows):
        errors.append("Extended USD/IRR series contains a non-positive value")

    housing_inflation_path = ROOT / "data" / "derived" / "housing" / "inflation" / "cbi_housing_rent_inflation_quarterly.csv"
    housing_inflation_rows = rows(housing_inflation_path)
    housing_inflation_keys = [
        (item["period"], item["indicator"], item["geography_code"])
        for item in housing_inflation_rows
    ]
    if len(housing_inflation_rows) != 910 or len(housing_inflation_keys) != len(set(housing_inflation_keys)):
        errors.append("Housing/rent inflation dataset must contain 910 unique period/indicator/geography rows")
    if sum(item["qoq_inflation_pct"] == "" for item in housing_inflation_rows) != 7:
        errors.append("Housing/rent inflation dataset must have one unavailable quarterly lag per series")
    if sum(item["yoy_inflation_pct"] == "" for item in housing_inflation_rows) != 28:
        errors.append("Housing/rent inflation dataset must have four unavailable annual lags per series")
    by_series: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in housing_inflation_rows:
        by_series.setdefault((item["indicator"], item["geography_code"]), []).append(item)
    for series_rows in by_series.values():
        series_rows.sort(key=lambda item: (int(item["solar_hijri_year"]), int(item["quarter"])))
        for index, item in enumerate(series_rows):
            value = float(item["source_index_value"])
            if index >= 1:
                expected = (value / float(series_rows[index - 1]["source_index_value"]) - 1) * 100
                if abs(float(item["qoq_inflation_pct"]) - expected) > 1e-10:
                    errors.append(f"Housing/rent quarterly inflation mismatch: {item['period']}")
                    break
            if index >= 4:
                expected = (value / float(series_rows[index - 4]["source_index_value"]) - 1) * 100
                if abs(float(item["yoy_inflation_pct"]) - expected) > 1e-10:
                    errors.append(f"Housing/rent annual inflation mismatch: {item['period']}")
                    break

    all_source_path = ROOT / "data" / "derived" / "housing" / "inflation" / "housing_rent_inflation_all_sources.csv"
    all_source_rows = rows(all_source_path)
    provider_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for item in all_source_rows:
        provider_counts[item["provider"]] = provider_counts.get(item["provider"], 0) + 1
        source_counts[item["source_dataset_id"]] = source_counts.get(item["source_dataset_id"], 0) + 1
        try:
            float(item["inflation_pct"])
        except ValueError:
            errors.append("All-source housing/rent inflation contains a non-numeric rate")
            break
    expected_source_counts = {
        "cbi_hsg_land_price_index_q": 430,
        "cbi_hsg_rent_index_by_city_size_q": 813,
        "cbi_hsg_rent_index_q": 542,
        "sci_tehran_building_input_indices_base1402": 2756,
        "sci_tehran_housing_market_quarterly_1388_1399": 5598,
        "sci_urban_cpi_national_annual_by_group": 92,
        "sci_urban_cpi_national_monthly_by_group": 3344,
    }
    if len(all_source_rows) != 13575 or source_counts != expected_source_counts:
        errors.append("All-source housing/rent inflation source coverage or row counts changed")
    if provider_counts != {
        "Central Bank of the Islamic Republic of Iran": 1785,
        "Statistical Center of Iran": 11790,
    }:
        errors.append("All-source housing/rent inflation must include both CBI and SCI")

    cleaned = ROOT / "data" / "cleaned" / "stocks" / "housing_finance" / "mortgage_facility_certificates" / "tsetmc_bank_maskan_mortgage_certificates_daily.csv"
    derived = ROOT / "data" / "derived" / "stocks" / "housing_finance" / "tsetmc_bank_maskan_tese_continuous_daily.csv"
    tese_rows = rows(cleaned)
    aggregate_rows = rows(derived)
    instrument_keys = [(item["ins_code"], item["gregorian_date"]) for item in tese_rows]
    aggregate_keys = [item["gregorian_date"] for item in aggregate_rows]
    if len(instrument_keys) != len(set(instrument_keys)):
        errors.append("duplicate ins_code/date key in cleaned tese panel")
    if len(aggregate_keys) != len(set(aggregate_keys)):
        errors.append("duplicate date in derived tese series")
    for item in tese_rows:
        if any(float(item[field]) <= 0 for field in ("closing_price_irr", "trade_count", "trade_volume", "trade_value_irr")):
            errors.append(f"non-positive traded observation: {item['ins_code']} {item['gregorian_date']}")
            break
    for item in aggregate_rows:
        expected = float(item["total_trade_value_irr"]) / float(item["total_trade_volume"])
        if abs(float(item["volume_weighted_price_irr"]) - expected) > max(1e-6, abs(expected) * 1e-12):
            errors.append(f"derived arithmetic mismatch: {item['gregorian_date']}")
            break

    return {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "manifest_files": len(manifest),
        "catalog_datasets": len(catalog),
        "cbi_datasets": len(actual_cbi),
        "cbi_inventory_workbooks": len({item["source_file"] for item in cbi_inventory}),
        "usd_irr_rows": len(fx_rows),
        "usd_irr_coverage": [fx_keys[0], fx_keys[-1]] if fx_keys else [],
        "housing_rent_inflation_rows": len(housing_inflation_rows),
        "housing_rent_inflation_series": len(by_series),
        "all_source_housing_rent_inflation_rows": len(all_source_rows),
        "all_source_housing_rent_inflation_providers": provider_counts,
        "sci_datasets": len(actual_sci),
        "sci_inventory_sheets": len(sci_inventory),
        "tese_cleaned_rows": len(tese_rows),
        "tese_instruments": len({item["ins_code"] for item in tese_rows}),
        "tese_derived_rows": len(aggregate_rows),
        "tese_coverage": [min(aggregate_keys), max(aggregate_keys)] if aggregate_keys else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Optional JSON report path relative to the repository")
    args = parser.parse_args()
    result = validate()
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.report:
        output = (ROOT / args.report).resolve()
        if ROOT.resolve() not in output.parents:
            raise ValueError("Report path must stay inside the repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
