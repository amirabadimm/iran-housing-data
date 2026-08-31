"""Register and organize manually downloaded CBI monthly monetary reports.

The operation is byte-preserving: files are renamed and moved, never rewritten.
Run without --apply to validate and preview the complete move plan.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parents[2]
INCOMING = ROOT / "data" / "incoming"
DATASET_ID = "cbi_selected_economic_indicators_monetary_credit_monthly"
RAW_ROOT = ROOT / "data" / "raw" / "macroeconomic_environment" / "liquidity" / DATASET_ID
REGISTRY = ROOT / "metadata" / "file_registry.csv"
SUPPORTED_SUFFIXES = {".pdf", ".xls"}
CANONICAL_STEM = "cbi_selected_economic_indicators_monetary_banking"
REGISTRY_FIELDS = [
    "file_id",
    "dataset_id",
    "original_name",
    "relative_path",
    "publication_date",
    "downloaded_at",
    "checksum_sha256",
    "bytes",
    "inspection_status",
]


def parse_period(path: Path) -> tuple[int, int]:
    stem = path.stem.lower().strip()
    canonical = re.search(r"_(1[34]\d{2})_(\d{2})$", stem)
    if canonical:
        return int(canonical.group(1)), int(canonical.group(2))

    compact = re.sub(r"^pol", "", stem).lstrip(" .,_-")
    compact = compact.replace("f", "").strip()
    separated = re.fullmatch(r"(\d{2}|\d{4})\s*[.,\s]\s*(\d{1,2})", compact)
    if separated:
        year_token, month_token = separated.groups()
    elif compact.isdigit():
        if len(compact) in {6, 7} and compact[:4] in {
            str(year) for year in range(1385, 1405)
        }:
            year_token, month_token = compact[:4], compact[4:]
        elif len(compact) == 4:
            year_token, month_token = compact[:2], compact[2:]
        else:
            raise ValueError(f"Unrecognized compact period: {path.name}")
    else:
        raise ValueError(f"Unrecognized period: {path.name}")

    year = int(year_token)
    if year == 0:
        year = 1400
    elif year < 100:
        year += 1300
    month = int(month_token)
    if not 1385 <= year <= 1499 or not 1 <= month <= 12:
        raise ValueError(f"Invalid period in {path.name}: {year}-{month:02d}")
    return year, month


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    if not REGISTRY.exists():
        return [], {}
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    return rows, {row["checksum_sha256"]: row for row in rows if row.get("checksum_sha256")}


def inspect_status(path: Path, previous: dict[str, str] | None) -> str:
    if previous and previous.get("inspection_status"):
        return previous["inspection_status"]
    if path.suffix.lower() == ".xls":
        workbook = xlrd.open_workbook(path, on_demand=True)
        if not workbook.sheet_names():
            raise ValueError(f"Workbook has no sheets: {path.name}")
        workbook.release_resources()
        return "inspected_xls_readable"
    return "registered_pdf_text_layer_layout_review_required"


def incoming_files() -> list[Path]:
    return sorted(
        (
            path
            for path in INCOMING.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        ),
        key=lambda path: path.name.lower(),
    )


def build_plan() -> list[dict[str, object]]:
    files = incoming_files()
    if not files:
        return []
    plan = []
    for source in files:
        year, month = parse_period(source)
        destination = (
            RAW_ROOT
            / str(year)
            / f"{CANONICAL_STEM}_{year}_{month:02d}{source.suffix.lower()}"
        )
        plan.append(
            {
                "source": source,
                "destination": destination,
                "year": year,
                "month": month,
                "checksum": sha256(source),
                "bytes": source.stat().st_size,
                "downloaded_at": datetime.fromtimestamp(source.stat().st_mtime)
                .astimezone()
                .isoformat(timespec="seconds"),
            }
        )

    periods = [(int(item["year"]), int(item["month"])) for item in plan]
    duplicates = [period for period, count in Counter(periods).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate monthly periods: {duplicates}")
    collisions = [
        str(item["destination"])
        for item in plan
        if Path(item["destination"]).exists()
    ]
    if collisions:
        raise FileExistsError(f"Destination files already exist: {collisions}")
    return plan


def update_registry(plan: list[dict[str, object]]) -> None:
    existing, by_checksum = load_registry()
    retained = [row for row in existing if row.get("dataset_id") != DATASET_ID]
    records = []
    for item in sorted(plan, key=lambda value: (int(value["year"]), int(value["month"]))):
        checksum = str(item["checksum"])
        previous = by_checksum.get(checksum)
        destination = Path(item["destination"])
        records.append(
            {
                "file_id": f"sha256:{checksum}",
                "dataset_id": DATASET_ID,
                "original_name": Path(item["source"]).name,
                "relative_path": destination.relative_to(ROOT).as_posix(),
                "publication_date": (previous or {}).get("publication_date", ""),
                "downloaded_at": (previous or {}).get(
                    "downloaded_at", str(item["downloaded_at"])
                ),
                "checksum_sha256": checksum,
                "bytes": str(item["bytes"]),
                "inspection_status": inspect_status(destination, previous),
            }
        )

    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=REGISTRY_FIELDS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(retained + records)
    temporary.replace(REGISTRY)


def apply_plan(plan: list[dict[str, object]]) -> None:
    for item in plan:
        source = Path(item["source"])
        destination = Path(item["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        if destination.stat().st_size != item["bytes"] or sha256(destination) != item["checksum"]:
            raise OSError(f"Integrity check failed after moving {source.name}")
    update_registry(plan)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move files and atomically rewrite their file-registry entries.",
    )
    args = parser.parse_args()
    plan = build_plan()
    if not plan:
        print("No unorganized CBI monthly monetary reports found.")
        return
    for item in sorted(plan, key=lambda value: (int(value["year"]), int(value["month"]))):
        source = Path(item["source"]).relative_to(ROOT)
        destination = Path(item["destination"]).relative_to(ROOT)
        print(f"{source.as_posix()} -> {destination.as_posix()}")
    print(f"Validated {len(plan)} unique monthly files.")
    if args.apply:
        apply_plan(plan)
        print(f"Organized and registered {len(plan)} files.")
    else:
        print("Dry run only; pass --apply to perform the moves.")


if __name__ == "__main__":
    main()
