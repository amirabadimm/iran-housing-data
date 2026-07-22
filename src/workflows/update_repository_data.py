"""Single entry point for reproducible repository data updates and rebuilds."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(*parts: str) -> None:
    command = [sys.executable, *parts]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hydrate_cbi_incoming() -> None:
    """Recreate ignored CBI intake copies from immutable canonical raw files."""
    destination = ROOT / "data" / "incoming" / "manually_collected"
    sources = sorted((ROOT / "data" / "raw" / "housing" / "cbi_tsd_14050431").glob("*.xlsx"))
    sources += sorted((ROOT / "data" / "raw" / "macro" / "cbi_tsd_14050431").glob("*.xlsx"))
    if len(sources) != 18:
        raise ValueError(f"Expected 18 canonical CBI workbooks, found {len(sources)}")
    destination.mkdir(parents=True, exist_ok=True)
    for source in sources:
        target = destination / source.name
        if target.exists() and file_hash(target) != file_hash(source):
            raise FileExistsError(f"Incoming workbook differs from canonical raw: {target}")
        if not target.exists():
            shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update or reproducibly rebuild registered data")
    parser.add_argument("--refresh-tsetmc", action="store_true", help="Collect a new immutable official TSETMC raw snapshot")
    parser.add_argument("--rebuild-tsetmc", action="store_true", help="Rebuild TSETMC cleaned/derived outputs from retained raw")
    parser.add_argument("--rebuild-cbi", action="store_true", help="Rebuild manually exported CBI workbooks")
    parser.add_argument("--rebuild-imported-macro", action="store_true", help="Revalidate imported standardized macro CSVs")
    parser.add_argument("--all-local", action="store_true", help="Run every offline rebuild without network collection")
    parser.add_argument("--as-of", help="Gregorian TSETMC snapshot date YYYY-MM-DD")
    parser.add_argument("--report", default="outputs/validation/latest_repository_validation.json", help="Validation report path")
    args = parser.parse_args()

    selected = any((args.refresh_tsetmc, args.rebuild_tsetmc, args.rebuild_cbi, args.rebuild_imported_macro, args.all_local))
    if not selected:
        parser.error("select an update/rebuild action")
    if args.refresh_tsetmc and args.rebuild_tsetmc:
        parser.error("choose either --refresh-tsetmc or --rebuild-tsetmc")

    if args.all_local or args.rebuild_cbi:
        hydrate_cbi_incoming()
        run("src/common/process_cbi_tsd_exports.py")
    if args.all_local or args.rebuild_imported_macro:
        run("src/macro/register_standardized_macro_csvs.py")
    if args.refresh_tsetmc:
        command = ["src/stocks/collect_tsetmc_housing_market.py", "--refresh"]
        if args.as_of:
            command += ["--as-of", args.as_of]
        run(*command)
    elif args.all_local or args.rebuild_tsetmc:
        command = ["src/stocks/collect_tsetmc_housing_market.py"]
        if args.as_of:
            command += ["--as-of", args.as_of]
        run(*command)

    run("src/workflows/validate_repository.py", "--report", args.report)


if __name__ == "__main__":
    main()
