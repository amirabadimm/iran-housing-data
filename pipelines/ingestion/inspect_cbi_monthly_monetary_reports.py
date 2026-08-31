"""Inspect incoming CBI monthly monetary reports without modifying source files."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import xlrd
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
INCOMING = ROOT / "data" / "incoming"
OUTPUT = ROOT / "data" / "staging" / "cbi_monthly_report_inspection.json"

TERMS = {
    "liquidity": ("نقدینگی", "نقدينگي"),
    "money": ("پول",),
    "quasi_money": ("شبه پول", "شبه‌پول"),
    "currency_with_public": ("اسکناس و مسکوک در دست اشخاص",),
    "demand_deposits": ("سپرده های دیداری", "سپرده‌هاي ديداري", "سپرده هاي ديداري"),
    "non_demand_deposits": ("سپرده های غیردیداری", "سپرده‌هاي غيرديداري", "سپرده هاي غيرديداري"),
    "monetary_base": ("پایه پولی", "پايه پولي"),
    "liquidity_multiplier": ("ضریب فزاینده نقدینگی", "ضريب فزاينده نقدينگي"),
}


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.translate(str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"}))
    return re.sub(r"[\s\u200c]+", " ", text).strip()


def hits(text: str) -> dict[str, bool]:
    normalized = normalize(text)
    return {
        key: any(normalize(term) in normalized for term in variants)
        for key, variants in TERMS.items()
    }


def inspect_pdf(path: Path) -> dict[str, object]:
    try:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
        return {
            "pages": len(reader.pages),
            "text_chars": len(normalize(text)),
            "term_hits": hits(text),
            "error": None,
        }
    except Exception as exc:
        return {"pages": None, "text_chars": 0, "term_hits": hits(""), "error": repr(exc)}


def inspect_xls(path: Path) -> dict[str, object]:
    try:
        workbook = xlrd.open_workbook(path, on_demand=True)
        sheet_info = []
        combined = []
        for sheet in workbook.sheets():
            values = []
            for row_index in range(sheet.nrows):
                values.extend(normalize(value) for value in sheet.row_values(row_index) if value not in (None, ""))
            text = "\n".join(values)
            combined.append(text)
            sheet_info.append({"name": sheet.name, "rows": sheet.nrows, "cols": sheet.ncols})
        all_text = "\n".join(combined)
        return {
            "sheets": sheet_info,
            "text_chars": len(normalize(all_text)),
            "term_hits": hits(all_text),
            "error": None,
        }
    except Exception as exc:
        return {"sheets": [], "text_chars": 0, "term_hits": hits(""), "error": repr(exc)}


def main() -> None:
    records = []
    for path in sorted(INCOMING.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or path.name == "README.md":
            continue
        result = inspect_pdf(path) if path.suffix.lower() == ".pdf" else inspect_xls(path)
        records.append({"file": path.name, "extension": path.suffix.lower(), **result})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(records), "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
