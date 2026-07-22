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
