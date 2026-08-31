"""Build a validated monthly CBI liquidity series from registered reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
import xlrd

ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "cbi_selected_economic_indicators_monetary_credit_monthly"
RAW_ROOT = (
    ROOT / "data" / "raw" / "macroeconomic_environment" / "liquidity" / DATASET_ID
)
OUTPUT = (
    ROOT
    / "data"
    / "standardized"
    / "macroeconomic_environment"
    / "liquidity"
    / DATASET_ID
    / "monthly_liquidity.csv"
)
FILE_RE = re.compile(r"_(1[34]\d{2})_(\d{2})\.(pdf|xls)$", re.IGNORECASE)


@dataclass(frozen=True)
class Record:
    solar_hijri_period: str
    solar_hijri_year: int
    solar_hijri_month: int
    liquidity_thousand_billion_rials: float
    money_thousand_billion_rials: float
    quasi_money_thousand_billion_rials: float
    source_unit: str
    source_format: str
    source_file: str
    source_location: str
    extraction_method: str
    accounting_identity_difference: float
    validation_status: str
    source_sha256: str


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value)).translate(
        str.maketrans("كي", "کی")
    )
    return re.sub(r"\s+", " ", text).strip()


def number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = normalize(value).translate(
        str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    )
    text = (
        text.replace(",", "")
        .replace("٬", "")
        .replace("٫", ".")
        .replace("−", "-")
    )
    if len(text) % 2 == 0 and all(
        text[index] == text[index + 1] for index in range(0, len(text), 2)
    ):
        text = text[::2]
    if not re.fullmatch(r"-?\d+(?:[/.]\d+)?", text):
        return None
    return float(text.replace("/", "."))


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def get_period(path: Path) -> tuple[int, int]:
    match = FILE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot determine period: {path.name}")
    return int(match.group(1)), int(match.group(2))


def record(
    path: Path,
    year: int,
    month: int,
    values: tuple[float, float, float],
    unit: str,
    location: str,
    method: str,
) -> Record:
    liquidity, money, quasi = values
    difference = round(liquidity - money - quasi, 6)
    if abs(difference) > 0.11:
        raise ValueError(f"Accounting identity failed for {path.name}: {values}")
    return Record(
        f"{year:04d}-{month:02d}",
        year,
        month,
        round(liquidity, 3),
        round(money, 3),
        round(quasi, 3),
        unit,
        path.suffix[1:].lower(),
        path.relative_to(ROOT).as_posix(),
        location,
        method,
        difference,
        "passed_liquidity_equals_money_plus_quasi_money",
        digest(path),
    )


def extract_xls(path: Path, year: int, month: int) -> Record:
    workbook = xlrd.open_workbook(path, on_demand=True)
    try:
        sheet_name = next(
            name for name in workbook.sheet_names() if normalize(name).startswith("متغیرهای")
        )
        sheet = workbook.sheet_by_name(sheet_name)
        rows = [
            [cell.value for cell in sheet.row(row_index)]
            for row_index in range(sheet.nrows)
        ]
    finally:
        workbook.release_resources()
    def value_for(label: str) -> float:
        compact_label = re.sub(r"[\s\u200c]+", "", label)
        row = next(
            (
                candidate
                for candidate in rows
                if any(
                    re.sub(r"[\s\u200c]+", "", normalize(cell)).startswith(
                        compact_label
                    )
                    for cell in candidate
                )
            ),
            None,
        )
        if row is None:
            raise ValueError(f"Could not find {label} in {path.name}")
        numeric = [
            parsed for cell in row if (parsed := number(cell)) is not None
        ]
        if len(numeric) < 3:
            raise ValueError(f"Could not extract {label} from {path.name}")
        return numeric[2]

    values = tuple(value_for(label) for label in ("نقدینگی", "پول", "شبه پول"))
    return record(
        path,
        year,
        month,
        values,
        "thousand_billion_rials",
        "sheet:major_monetary_variables",
        "xls_cell_extraction",
    )


def page_rows(page: object) -> list[list[dict[str, object]]]:
    words = page.extract_words(x_tolerance=2, y_tolerance=2)
    rows: list[list[dict[str, object]]] = []
    for word in sorted(words, key=lambda item: (float(item["top"]), float(item["x0"]))):
        if not rows or abs(float(word["top"]) - float(rows[-1][0]["top"])) > 3:
            rows.append([word])
        else:
            rows[-1].append(word)
    return rows


def kind(row: list[dict[str, object]]) -> str | None:
    def label_variants(value: object) -> set[str]:
        text = normalize(value)
        variants = {text, text[::-1]}
        if len(text) % 2 == 0 and all(
            text[index] == text[index + 1] for index in range(0, len(text), 2)
        ):
            collapsed = text[::2]
            variants.update((collapsed, collapsed[::-1]))
        return variants

    word_variants = {
        variant
        for word in row
        for variant in label_variants(word["text"])
    }
    text = normalize(
        " ".join(
            str(word["text"])
            for word in sorted(row, key=lambda item: float(item["x0"]), reverse=True)
        )
    )
    variants = (text, text[::-1])
    if any("نقدینگی" in item for item in variants):
        return "liquidity"
    has_money = any(
        item.startswith("پول") or item.endswith("پول") for item in word_variants
    )
    has_quasi = any("شبه" in item for item in word_variants)
    if any("شبه پول" in item for item in variants) or (has_money and has_quasi):
        return "quasi"
    if has_money or any(re.search(r"(^| )پول( |$)", item) for item in variants):
        return "money"
    return None


def numeric_cells(row: list[dict[str, object]]) -> list[tuple[float, float, str]]:
    result = []
    for word in row:
        parsed = number(word["text"])
        x = float(word["x0"])
        if parsed is not None and x > 150:
            result.append((x, parsed, str(word["text"])))
    return result


def scale(value: float, token: str, year: int, month: int) -> float:
    if (year, month) < (1394, 5):
        return value / 1000
    return value if "/" in token or "." in token else value / 10


def extract_pdf(path: Path, year: int, month: int) -> Record:
    with pdfplumber.open(path) as document:
        for page_number, page in enumerate(document.pages, 1):
            rows = page_rows(page)
            labels = [(index, kind(row)) for index, row in enumerate(rows)]
            for index, label in labels:
                if label != "liquidity":
                    continue
                nearby = [
                    (other_index, other_label)
                    for other_index, other_label in labels
                    if abs(index - other_index) <= 20
                ]
                money_rows = [i for i, value in nearby if value == "money"]
                quasi_rows = [i for i, value in nearby if value == "quasi"]
                if not money_rows or not quasi_rows:
                    continue
                components = (
                    numeric_cells(rows[index]),
                    numeric_cells(rows[money_rows[0]]),
                    numeric_cells(rows[quasi_rows[0]]),
                )
                for lx, liquidity, lt in sorted(components[0]):
                    if lx < 170:
                        continue
                    money_cells = sorted(components[1], key=lambda item: abs(item[0] - lx))
                    quasi_cells = sorted(components[2], key=lambda item: abs(item[0] - lx))
                    for mx, money, mt in money_cells[:2]:
                        for qx, quasi, qt in quasi_cells[:2]:
                            if max(abs(mx - lx), abs(qx - lx)) > 22:
                                continue
                            values = (
                                scale(liquidity, lt, year, month),
                                scale(money, mt, year, month),
                                scale(quasi, qt, year, month),
                            )
                            if (
                                values[0] > 100
                                and abs(values[0] - values[1] - values[2]) <= 0.11
                            ):
                                unit = (
                                    "billion_rials"
                                    if (year, month) < (1394, 5)
                                    else "thousand_billion_rials"
                                )
                                return record(
                                    path,
                                    year,
                                    month,
                                    values,
                                    unit,
                                    f"page:{page_number}",
                                    "pdf_coordinate_extraction",
                                )
    raise ValueError(f"No validated liquidity table found in {path.name}")


def build() -> list[Record]:
    files = sorted(
        path
        for path in RAW_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".xls"}
    )
    records = []
    failures = []
    for path in files:
        year, month = get_period(path)
        extractor = extract_xls if path.suffix.lower() == ".xls" else extract_pdf
        try:
            records.append(extractor(path, year, month))
        except ValueError as error:
            failures.append(str(error))
    if failures:
        raise ValueError("Extraction failures:\n" + "\n".join(failures))
    expected = {
        (year, month) for year in range(1385, 1405) for month in range(1, 13)
    }
    actual = {
        (item.solar_hijri_year, item.solar_hijri_month) for item in records
    }
    if actual != expected or len(records) != len(actual):
        raise ValueError(
            f"Coverage failed; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    return sorted(
        records, key=lambda item: (item.solar_hijri_year, item.solar_hijri_month)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without writing.")
    args = parser.parse_args()
    records = build()
    if not args.check:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(".csv.tmp")
        with temporary.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=list(asdict(records[0])))
            writer.writeheader()
            writer.writerows(asdict(item) for item in records)
        temporary.replace(OUTPUT)
    print(f"Validated {len(records)} monthly periods (1385-01 through 1404-12).")


if __name__ == "__main__":
    main()
