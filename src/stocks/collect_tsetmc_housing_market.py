"""Collect housing-linked TSETMC instruments and construction-material indices.

Discovery uses algotik-tse's TSETMC industry mappings plus current official
TSETMC JSON APIs. A refresh is all-or-nothing: every required response and
history is validated in memory before any raw or cleaned file is written.
Existing raw files are never overwritten. Without ``--refresh``, cleaned files
and metadata are rebuilt reproducibly from the retained raw JSON responses.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import re
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import jdatetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from algotik_tse.core.search import _INDUSTRY_DICT, _normalize_fa


ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL_DATE = "2026-07-22"
TASK_ID = "collect_tsetmc_housing_market_20260722"
API = "https://cdn.tsetmc.com/api"
RAW_STOCKS = ROOT / "data" / "raw" / "stocks" / "tsetmc_housing_market_complete_tese_20260722"
RAW_RELATED = ROOT / "data" / "raw" / "related_industries" / "tsetmc_construction_materials_complete_tese_20260722"
COLLECTION_JALALI_YEAR = 1405

INDEXES = {
    "real_estate": ("انبوه سازی، املاک و مستغلات", "4654922806626448"),
    "cement": ("سیمان، آهک و گچ", "70077233737515808"),
    "tile_ceramic": ("کاشی و سرامیک", "57616105980228781"),
}

CATALOG_FIELDS = "dataset_id,dataset_name,topic,category,subcategory,category_status,description,source_organization,source_url,collection_method,date_collected,original_filename,stored_filename,raw_path,cleaned_path,derived_path,file_format,sheet_names,time_coverage_start,time_coverage_end,frequency,geographic_coverage,unit,language,access_status,cleaning_status,validation_status,current_use,related_task,confidentiality,checksum_sha256,notes".split(",")
VARIABLE_FIELDS = "dataset_id,variable_name,variable_label,description,data_type,unit,language,allowed_values,missing_value_codes,source_definition,notes".split(",")
CLEANING_FIELDS = "cleaning_id,dataset_id,date,input_path,output_path,script,transformation,reason,rows_before,rows_after,columns_before,columns_after,performed_by,review_status,notes".split(",")
SOURCE_FIELDS = "source_id,source_organization,source_name,source_url,access_method,date_accessed,license,access_status,contact,notes".split(",")
ISSUE_FIELDS = "issue_id,dataset_id,date_identified,issue_type,description,severity,status,resolution,related_file,notes".split(",")


def configure_batch(as_of: str) -> None:
    """Set dated immutable raw paths and discovery horizon for one run."""
    global RETRIEVAL_DATE, TASK_ID, RAW_STOCKS, RAW_RELATED, COLLECTION_JALALI_YEAR
    parsed = datetime.strptime(as_of, "%Y-%m-%d").date()
    compact = parsed.strftime("%Y%m%d")
    RETRIEVAL_DATE = parsed.isoformat()
    TASK_ID = f"collect_tsetmc_housing_market_{compact}"
    RAW_STOCKS = ROOT / "data" / "raw" / "stocks" / f"tsetmc_housing_market_complete_tese_{compact}"
    RAW_RELATED = ROOT / "data" / "raw" / "related_industries" / f"tsetmc_construction_materials_complete_tese_{compact}"
    COLLECTION_JALALI_YEAR = jdatetime.date.fromgregorian(date=parsed).year


def latest_retained_batch_date() -> str:
    candidates = []
    for path in (ROOT / "data" / "raw" / "stocks").glob("tsetmc_housing_market_complete_tese_????????"):
        match = re.fullmatch(r"tsetmc_housing_market_complete_tese_(\d{8})", path.name)
        if match and path.is_dir():
            candidates.append(match.group(1))
    if not candidates:
        raise FileNotFoundError("No complete retained TSETMC raw batch exists")
    return datetime.strptime(max(candidates), "%Y%m%d").date().isoformat()


@dataclass(frozen=True)
class Instrument:
    group: str
    ins_code: str
    symbol: str
    name: str
    market: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(text: Any) -> str:
    return _normalize_fa(str(text or "")).replace("\t", " ")


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    retry = Retry(total=1, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "Mozilla/5.0 (research data collection; contact repository owner)"})
    return session


def fetch_bytes(url: str) -> bytes:
    session = new_session()
    response = session.get(url, timeout=(10, 30), verify=False)
    response.raise_for_status()
    if not response.content:
        raise ValueError(f"Empty response: {url}")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError(f"Non-JSON response: {url}") from error
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"Invalid JSON object: {url}")
    return response.content


def parse_json(raw: bytes, key: str, url: str) -> list[dict[str, Any]]:
    payload = json.loads(raw.decode("utf-8-sig"))
    rows = payload.get(key)
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Missing or empty {key}: {url}")
    return rows


def discovery_urls() -> dict[str, str]:
    # The broad search endpoint is ranked/capped and omits most expired monthly
    # certificates. Query every plausible exact symbol instead. Monthly symbols
    # use YYMM; from 1400 onward TSETMC also publishes annual YYYY symbols.
    tese_terms = [f"تسه{year:02d}{month:02d}" for year in range(89, 100) for month in range(1, 13)]
    short_year_end = max(0, COLLECTION_JALALI_YEAR - 1400)
    tese_terms += [f"تسه{year:02d}{month:02d}" for year in range(0, short_year_end + 1) for month in range(1, 13)]
    tese_terms += [f"تسه{year}" for year in range(1400, COLLECTION_JALALI_YEAR + 1)]
    urls = {
        "search_real_estate": f"{API}/Instrument/GetInstrumentSearch/{quote('املاک')}",
        "search_real_estate_alt": f"{API}/Instrument/GetInstrumentSearch/{quote('مستغلات')}",
        "real_estate_constituents": f"{API}/ClosingPrice/GetIndexCompany/{INDEXES['real_estate'][1]}",
    }
    urls.update({f"search_tese_{term.removeprefix('تسه')}": f"{API}/Instrument/GetInstrumentSearch/{quote(term)}" for term in tese_terms})
    return urls


def discover(raw: dict[str, bytes]) -> list[Instrument]:
    expected_ids = {
        "انبوه سازی": INDEXES["real_estate"][1],
        "سیمان": INDEXES["cement"][1],
        "کاشی و سرامیک": INDEXES["tile_ceramic"][1],
    }
    for label, ins_code in expected_ids.items():
        resolved = _INDUSTRY_DICT.get(_normalize_fa(label))
        if resolved != ins_code:
            raise ValueError(f"algotik-tse industry mapping mismatch for {label}: {resolved}")

    mortgage_by_code: dict[str, Instrument] = {}
    mortgage_name = normalize("امتياز تسهيلات مسكن")
    for key, content in raw.items():
        if not key.startswith("search_tese_"):
            continue
        expected_symbol = normalize("تسه" + key.removeprefix("search_tese_"))
        search_rows = json.loads(content.decode("utf-8-sig")).get("instrumentSearch")
        if not isinstance(search_rows, list):
            raise ValueError(f"Invalid instrumentSearch schema: {key}")
        for row in search_rows:
            symbol = normalize(row.get("lVal18AFC"))
            name = normalize(row.get("lVal30"))
            if symbol == expected_symbol and mortgage_name in name:
                item = Instrument("mortgage_certificates", str(row["insCode"]), symbol, name, normalize(row.get("flowTitle")))
                mortgage_by_code[item.ins_code] = item
    mortgage = list(mortgage_by_code.values())

    fund_candidates: dict[str, dict[str, Any]] = {}
    for key in ("search_real_estate", "search_real_estate_alt"):
        for row in parse_json(raw[key], "instrumentSearch", key):
            fund_candidates[str(row.get("insCode"))] = row
    funds = []
    for row in fund_candidates.values():
        symbol = normalize(row.get("lVal18AFC"))
        name = normalize(row.get("lVal30"))
        # TSETMC abbreviates "صندوق سرمايه گذاري" as "ص.س." in lVal30.
        fund_marker = normalize("صندوق") in name or name.startswith(normalize("ص.س."))
        is_real_estate_fund = fund_marker and (
            normalize("املاك") in name or normalize("مستغلات") in name
        )
        if is_real_estate_fund:
            funds.append(Instrument("real_estate_funds", str(row["insCode"]), symbol, name, normalize(row.get("flowTitle"))))

    constituent_rows = parse_json(raw["real_estate_constituents"], "indexCompany", "real_estate_constituents")
    developers = []
    for row in constituent_rows:
        instrument = row.get("instrument") or {}
        ins_code = str(instrument.get("insCode") or row.get("insCode") or "")
        symbol = normalize(instrument.get("lVal18AFC"))
        name = normalize(instrument.get("lVal30"))
        if ins_code and symbol and name:
            developers.append(Instrument("real_estate_developers", ins_code, symbol, name, "TSETMC real-estate sector constituent"))

    instruments = sorted(mortgage + funds + developers, key=lambda x: (x.group, x.symbol, x.ins_code))
    if len(mortgage) < 1 or len(funds) < 1 or len(developers) < 1:
        raise ValueError(f"Incomplete discovery: mortgage={len(mortgage)}, funds={len(funds)}, developers={len(developers)}")
    if len({item.ins_code for item in instruments}) != len(instruments):
        raise ValueError("An instrument appears in more than one requested universe")
    return instruments


def history_urls(instruments: list[Instrument]) -> dict[str, str]:
    urls = {f"instrument_{item.ins_code}": f"{API}/ClosingPrice/GetClosingPriceDailyList/{item.ins_code}/0" for item in instruments}
    urls.update({f"index_{key}": f"{API}/Index/GetIndexB2History/{ins_code}" for key, (_, ins_code) in INDEXES.items()})
    return urls


def fetch_all(urls: dict[str, str], workers: int = 6) -> dict[str, bytes]:
    def fetch_item(item: tuple[str, str]) -> tuple[str, bytes]:
        key, url = item
        return key, fetch_bytes(url)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = dict(executor.map(fetch_item, urls.items()))
    if set(results) != set(urls):
        raise RuntimeError("Not every required URL returned")
    return results


def jalali_parts(gregorian_date: str) -> tuple[str, int, int, int]:
    year, month, day = map(int, gregorian_date.split("-"))
    value = jdatetime.date.fromgregorian(day=day, month=month, year=year)
    return f"{value.year:04d}/{value.month:02d}/{value.day:02d}", value.year, value.month, value.day


def clean_instrument_history(item: Instrument, raw: bytes) -> list[dict[str, Any]]:
    rows = parse_json(raw, "closingPriceDaily", item.ins_code)
    cleaned = []
    seen = set()
    for source in rows:
        date_raw = str(source.get("dEven") or "")
        if not re.fullmatch(r"\d{8}", date_raw):
            continue
        close = float(source.get("pClosing") or 0)
        volume = float(source.get("qTotTran5J") or 0)
        trades = float(source.get("zTotTran") or 0)
        value = float(source.get("qTotCap") or 0)
        if close <= 0 or volume <= 0 or trades <= 0 or value <= 0:
            continue
        gregorian = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
        key = (item.ins_code, gregorian)
        if key in seen:
            raise ValueError(f"Duplicate instrument-date: {key}")
        seen.add(key)
        jalali_date, jy, jm, jd = jalali_parts(gregorian)
        cleaned.append({
            "gregorian_date": gregorian,
            "jalali_date": jalali_date,
            "jalali_year": jy,
            "jalali_month": jm,
            "jalali_day": jd,
            "instrument_group": item.group,
            "symbol": item.symbol,
            "instrument_name_fa": item.name,
            "ins_code": item.ins_code,
            "market": item.market,
            "open_price_irr": source.get("priceFirst"),
            "high_price_irr": source.get("priceMax"),
            "low_price_irr": source.get("priceMin"),
            "last_price_irr": source.get("pDrCotVal"),
            "closing_price_irr": source.get("pClosing"),
            "yesterday_price_irr": source.get("priceYesterday"),
            "trade_count": source.get("zTotTran"),
            "trade_volume": source.get("qTotTran5J"),
            "trade_value_irr": source.get("qTotCap"),
            "price_adjustment": "unadjusted",
            "source": "TSETMC",
        })
    cleaned.sort(key=lambda row: (row["gregorian_date"], row["ins_code"]))
    if not cleaned:
        raise ValueError(f"No valid traded observations for {item.symbol} ({item.ins_code})")
    return cleaned


def clean_index_history(key: str, raw: bytes) -> list[dict[str, Any]]:
    label, ins_code = INDEXES[key]
    rows = parse_json(raw, "indexB2", ins_code)
    cleaned = []
    seen = set()
    for source in rows:
        date_raw = str(source.get("dEven") or "")
        close = float(source.get("xNivInuClMresIbs") or 0)
        if not re.fullmatch(r"\d{8}", date_raw) or close <= 0:
            continue
        gregorian = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
        if gregorian in seen:
            raise ValueError(f"Duplicate index date for {key}: {gregorian}")
        seen.add(gregorian)
        jalali_date, jy, jm, jd = jalali_parts(gregorian)
        cleaned.append({
            "gregorian_date": gregorian,
            "jalali_date": jalali_date,
            "jalali_year": jy,
            "jalali_month": jm,
            "jalali_day": jd,
            "index_key": key,
            "index_name_fa": label,
            "ins_code": ins_code,
            "high_index_points": source.get("xNivInuPhMresIbs"),
            "low_index_points": source.get("xNivInuPbMresIbs"),
            "closing_index_points": source.get("xNivInuClMresIbs"),
            "source": "TSETMC",
        })
    cleaned.sort(key=lambda row: row["gregorian_date"])
    if not cleaned:
        raise ValueError(f"No valid index observations for {key}")
    return cleaned


def read_raw() -> tuple[dict[str, bytes], dict[str, bytes]]:
    discovery = {path.stem: path.read_bytes() for path in (RAW_STOCKS / "discovery").glob("*.json")}
    instruments = {}
    for path in (RAW_STOCKS / "histories").glob("**/*.json"):
        instruments[f"instrument_{path.stem}"] = path.read_bytes()
    indexes = {}
    for path in (RAW_STOCKS / "indices").glob("*.json"):
        indexes[f"index_{path.stem}"] = path.read_bytes()
    for path in (RAW_RELATED / "indices").glob("*.json"):
        indexes[f"index_{path.stem}"] = path.read_bytes()
    core = {"search_real_estate", "search_real_estate_alt", "real_estate_constituents"}
    if not core.issubset(discovery) or any(key not in discovery_urls() for key in discovery):
        raise ValueError("Retained discovery raw files are incomplete or unrecognized")
    return discovery, instruments | indexes


def write_raw(discovery: dict[str, bytes], histories: dict[str, bytes], instruments: list[Instrument]) -> None:
    if RAW_STOCKS.exists() or RAW_RELATED.exists():
        raise FileExistsError("Raw extraction directory already exists; use the retained raw mode or choose a new dated batch")
    item_by_code = {item.ins_code: item for item in instruments}
    with tempfile.TemporaryDirectory(prefix="tsetmc_housing_", dir=ROOT) as temp_name:
        temp = Path(temp_name)
        stock_temp = temp / "stocks"
        related_temp = temp / "related"
        for key, content in discovery.items():
            if key.startswith("search_tese_"):
                rows = json.loads(content.decode("utf-8-sig")).get("instrumentSearch")
                if rows == []:
                    continue
            path = stock_temp / "discovery" / f"{key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        for key, content in histories.items():
            if key.startswith("instrument_"):
                code = key.removeprefix("instrument_")
                item = item_by_code[code]
                path = stock_temp / "histories" / item.group / f"{code}.json"
            elif key == "index_real_estate":
                path = stock_temp / "indices" / "real_estate.json"
            else:
                path = related_temp / "indices" / f"{key.removeprefix('index_')}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        RAW_STOCKS.parent.mkdir(parents=True, exist_ok=True)
        RAW_RELATED.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(stock_temp), RAW_STOCKS)
        shutil.move(str(related_temp), RAW_RELATED)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def replace_rows(path: Path, fields: list[str], key: str, prefixes: tuple[str, ...], new_rows: list[dict[str, Any]]) -> None:
    retained = [row for row in read_csv(path) if not row.get(key, "").startswith(prefixes)]
    write_csv(path, fields, retained + new_rows)


def persist_outputs(instruments: list[Instrument], raw_histories: dict[str, bytes]) -> dict[str, tuple[Path, list[dict[str, Any]], list[str]]]:
    instrument_rows: dict[str, list[dict[str, Any]]] = {group: [] for group in ("mortgage_certificates", "real_estate_funds", "real_estate_developers")}
    for item in instruments:
        instrument_rows[item.group].extend(clean_instrument_history(item, raw_histories[f"instrument_{item.ins_code}"]))
    for rows in instrument_rows.values():
        rows.sort(key=lambda row: (row["gregorian_date"], row["symbol"], row["ins_code"]))

    index_rows = {key: clean_index_history(key, raw_histories[f"index_{key}"]) for key in INDEXES}
    material_rows = sorted(index_rows["cement"] + index_rows["tile_ceramic"], key=lambda row: (row["gregorian_date"], row["index_key"]))
    registry_rows = [{"instrument_group": item.group, "symbol": item.symbol, "instrument_name_fa": item.name, "ins_code": item.ins_code, "market": item.market, "source": "TSETMC", "retrieval_date": RETRIEVAL_DATE} for item in instruments]

    # A continuous market-level series is analytical rather than a source-level
    # observation, so it belongs in derived/. Aggregate only across certificates
    # that actually traded on each date; do not fill non-trading dates.
    by_date: dict[str, list[dict[str, Any]]] = {}
    for row in instrument_rows["mortgage_certificates"]:
        by_date.setdefault(row["gregorian_date"], []).append(row)
    tese_aggregate_rows = []
    for gregorian, rows in sorted(by_date.items()):
        volumes = [float(row["trade_volume"]) for row in rows]
        values = [float(row["trade_value_irr"]) for row in rows]
        closes = sorted(float(row["closing_price_irr"]) for row in rows)
        total_volume = sum(volumes)
        total_value = sum(values)
        middle = len(closes) // 2
        median = closes[middle] if len(closes) % 2 else (closes[middle - 1] + closes[middle]) / 2
        first = rows[0]
        tese_aggregate_rows.append({
            "gregorian_date": gregorian,
            "jalali_date": first["jalali_date"],
            "jalali_year": first["jalali_year"],
            "jalali_month": first["jalali_month"],
            "jalali_day": first["jalali_day"],
            "traded_instrument_count": len(rows),
            "total_trade_count": sum(float(row["trade_count"]) for row in rows),
            "total_trade_volume": total_volume,
            "total_trade_value_irr": total_value,
            "volume_weighted_price_irr": total_value / total_volume,
            "mean_closing_price_irr": sum(closes) / len(closes),
            "median_closing_price_irr": median,
            "minimum_closing_price_irr": min(closes),
            "maximum_closing_price_irr": max(closes),
            "aggregation_scope": "all valid TSETMC Bank Maskan mortgage-facility certificates traded that day",
            "source": "Derived from standardized TSETMC instrument-day observations",
        })

    price_fields = ["gregorian_date", "jalali_date", "jalali_year", "jalali_month", "jalali_day", "instrument_group", "symbol", "instrument_name_fa", "ins_code", "market", "open_price_irr", "high_price_irr", "low_price_irr", "last_price_irr", "closing_price_irr", "yesterday_price_irr", "trade_count", "trade_volume", "trade_value_irr", "price_adjustment", "source"]
    index_fields = ["gregorian_date", "jalali_date", "jalali_year", "jalali_month", "jalali_day", "index_key", "index_name_fa", "ins_code", "high_index_points", "low_index_points", "closing_index_points", "source"]
    registry_fields = ["instrument_group", "symbol", "instrument_name_fa", "ins_code", "market", "source", "retrieval_date"]
    aggregate_fields = ["gregorian_date", "jalali_date", "jalali_year", "jalali_month", "jalali_day", "traded_instrument_count", "total_trade_count", "total_trade_volume", "total_trade_value_irr", "volume_weighted_price_irr", "mean_closing_price_irr", "median_closing_price_irr", "minimum_closing_price_irr", "maximum_closing_price_irr", "aggregation_scope", "source"]
    outputs = {
        "tsetmc_housing_market_instrument_registry": (ROOT / "data" / "cleaned" / "stocks" / "reference" / "tsetmc_housing_market_instrument_registry.csv", registry_rows, registry_fields),
        "tsetmc_bank_maskan_mortgage_certificates_daily": (ROOT / "data" / "cleaned" / "stocks" / "housing_finance" / "mortgage_facility_certificates" / "tsetmc_bank_maskan_mortgage_certificates_daily.csv", instrument_rows["mortgage_certificates"], price_fields),
        "tsetmc_real_estate_funds_daily": (ROOT / "data" / "cleaned" / "stocks" / "real_estate_funds" / "tsetmc_real_estate_funds_daily.csv", instrument_rows["real_estate_funds"], price_fields),
        "tsetmc_real_estate_developer_stocks_daily": (ROOT / "data" / "cleaned" / "stocks" / "real_estate_developers" / "tsetmc_real_estate_developer_stocks_daily.csv", instrument_rows["real_estate_developers"], price_fields),
        "tsetmc_real_estate_sector_index_daily": (ROOT / "data" / "cleaned" / "stocks" / "real_estate_developers" / "tsetmc_real_estate_sector_index_daily.csv", index_rows["real_estate"], index_fields),
        "tsetmc_cement_tile_ceramic_sector_indices_daily": (ROOT / "data" / "cleaned" / "related_industries" / "construction_materials" / "market_indices" / "tsetmc_cement_tile_ceramic_sector_indices_daily.csv", material_rows, index_fields),
        "tsetmc_bank_maskan_tese_continuous_daily": (ROOT / "data" / "derived" / "stocks" / "housing_finance" / "tsetmc_bank_maskan_tese_continuous_daily.csv", tese_aggregate_rows, aggregate_fields),
    }
    for path, rows, fields in outputs.values():
        if not rows:
            raise ValueError(f"Refusing to write empty dataset: {path}")
        write_csv(path, fields, rows)
    return outputs


def update_metadata(outputs: dict[str, tuple[Path, list[dict[str, Any]], list[str]]], instruments: list[Instrument]) -> None:
    definitions = {
        "tsetmc_housing_market_instrument_registry": ("TSETMC housing-market instrument registry", "stocks", "instrument_registry", "mixed", "Reference list for the exact discovered universes."),
        "tsetmc_bank_maskan_mortgage_certificates_daily": ("Bank Maskan mortgage-facility certificate prices", "stocks", "mortgage_facility_certificates", "Iranian rial", "All exhaustively discovered monthly and annual تسه instruments with valid traded days; unadjusted official prices."),
        "tsetmc_real_estate_funds_daily": ("Listed Iranian real-estate fund prices", "stocks", "real_estate_funds", "Iranian rial", "Active instruments whose official TSETMC name identifies a real-estate fund; valid traded days; unadjusted official prices."),
        "tsetmc_real_estate_developer_stocks_daily": ("Mass-construction and real-estate constituent stock prices", "stocks", "real_estate_developers", "Iranian rial", "Current constituents of the official TSETMC real-estate sector index; valid traded days; unadjusted prices."),
        "tsetmc_real_estate_sector_index_daily": ("TSETMC mass-construction and real-estate sector index", "stocks", "real_estate_sector_index", "index points", "Official market-sector index; not a physical housing-production index."),
        "tsetmc_cement_tile_ceramic_sector_indices_daily": ("TSETMC cement and tile/ceramic sector indices", "related_industries", "construction_materials_market_indices", "index points", "Official stock-market sector indices; not physical production-volume indices."),
        "tsetmc_bank_maskan_tese_continuous_daily": ("Continuous daily Bank Maskan mortgage-certificate market series", "stocks", "mortgage_facility_certificates_aggregate", "Iranian rial", "Derived across every valid certificate traded per day; volume-weighted price equals total trade value divided by total traded volume."),
    }
    raw_stock_paths = "; ".join(sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in RAW_STOCKS.glob("**/*.json")))
    raw_related_paths = "; ".join(sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in RAW_RELATED.glob("**/*.json")))
    catalog_rows = []
    cleaning_rows = []
    variable_rows = []
    for dataset_id, (path, rows, fields) in outputs.items():
        name, category, subcategory, unit, note = definitions[dataset_id]
        dates = [row.get("gregorian_date") for row in rows if row.get("gregorian_date")]
        raw_paths = raw_related_paths if category == "related_industries" else raw_stock_paths
        relative_output = str(path.relative_to(ROOT)).replace("\\", "/")
        is_derived = relative_output.startswith("data/derived/")
        catalog_rows.append({"dataset_id": dataset_id, "dataset_name": name, "topic": "Tehran securities market housing-linked instruments", "category": category, "subcategory": subcategory, "category_status": "confirmed", "description": name, "source_organization": "Tehran Securities Exchange Technology Management Co. (TSETMC)", "source_url": "https://cdn.tsetmc.com/api/", "collection_method": f"algotik-tse {importlib.metadata.version('algotik-tse')} discovery mappings with direct official TSETMC JSON APIs", "date_collected": RETRIEVAL_DATE, "original_filename": "TSETMC JSON responses", "stored_filename": "multiple retained JSON responses", "raw_path": raw_paths, "cleaned_path": "" if is_derived else relative_output, "derived_path": relative_output if is_derived else "", "file_format": "CSV", "sheet_names": "", "time_coverage_start": min(dates) if dates else RETRIEVAL_DATE, "time_coverage_end": max(dates) if dates else RETRIEVAL_DATE, "frequency": "daily trading observations" if dates else "snapshot registry", "geographic_coverage": "Tehran Stock Exchange / Iran Fara Bourse", "unit": unit, "language": "English fields; Persian instrument names", "access_status": "public API", "cleaning_status": "completed", "validation_status": "non-empty source and output; schema, date, key, positive trading activity/price, uniqueness, and raw retention validated", "current_use": "available", "related_task": TASK_ID, "confidentiality": "public", "checksum_sha256": sha256(path), "notes": f"{note} Rows={len(rows)}. Instruments={len({row.get('ins_code') for row in rows})}."})
        cleaning_rows.append({"cleaning_id": f"clean_{dataset_id}", "dataset_id": dataset_id, "date": RETRIEVAL_DATE, "input_path": raw_paths, "output_path": str(path.relative_to(ROOT)).replace("\\", "/"), "script": "src/stocks/collect_tsetmc_housing_market.py", "transformation": "Parsed official JSON; normalized Persian text and Gregorian/Jalali dates; retained valid positive traded instrument-days or positive index observations; sorted and combined requested universe.", "reason": "User-requested collection and standardization", "rows_before": "see retained raw responses", "rows_after": len(rows), "columns_before": "source JSON schema", "columns_after": len(fields), "performed_by": "Codex", "review_status": "completed", "notes": "No interpolation, imputation, resampling, return calculation, or price adjustment."})
        for field in fields:
            variable_rows.append({"dataset_id": dataset_id, "variable_name": field, "variable_label": field.replace("_", " "), "description": field.replace("_", " "), "data_type": "numeric" if field.endswith(("_irr", "_points", "_count", "_volume", "_year", "_month", "_day")) else "string", "unit": "Iranian rial" if field.endswith("_irr") else "index points" if field.endswith("_points") else "as named", "language": "English field; Persian values where applicable", "allowed_values": "", "missing_value_codes": "blank", "source_definition": "TSETMC official API field standardized without analytical transformation", "notes": "See methodology notes for source-field mapping."})

    replace_rows(ROOT / "metadata" / "data_catalog.csv", CATALOG_FIELDS, "dataset_id", ("tsetmc_",), catalog_rows)
    replace_rows(ROOT / "metadata" / "cleaning_log.csv", CLEANING_FIELDS, "dataset_id", ("tsetmc_",), cleaning_rows)
    replace_rows(ROOT / "metadata" / "variable_dictionary.csv", VARIABLE_FIELDS, "dataset_id", ("tsetmc_",), variable_rows)

    source_row = {"source_id": "tsetmc_housing_linked_market", "source_organization": "Tehran Securities Exchange Technology Management Co. (TSETMC)", "source_name": "Instrument search, sector constituents, daily prices, and industry index histories", "source_url": "https://cdn.tsetmc.com/api/", "access_method": f"algotik-tse {importlib.metadata.version('algotik-tse')} mappings plus direct JSON API", "date_accessed": RETRIEVAL_DATE, "license": "not stated in API responses; requires review", "access_status": "retrieved and raw responses retained", "contact": "", "notes": "TLS verification was disabled after verified requests stalled; HTTPS official host and response schemas were validated. No empty or timed-out response was retained."}
    replace_rows(ROOT / "metadata" / "source_registry.csv", SOURCE_FIELDS, "source_id", ("tsetmc_housing_linked_market",), [source_row])

    issues = [{"issue_id": "issue_tsetmc_real_estate_fund_endpoint_empty", "dataset_id": "tsetmc_real_estate_funds_daily", "date_identified": RETRIEVAL_DATE, "issue_type": "discovery_endpoint_limitation", "description": "algotik-tse list_funds(fund_type='real_estate') returned an empty TSETMC Fund API array during discovery.", "severity": "low", "status": "documented", "resolution": "Used official TSETMC instrument-search results with an explicit real-estate-fund identity rule; retained the non-empty search responses.", "related_file": "data/raw/stocks/tsetmc_housing_market_20260722/discovery/", "notes": "The empty Fund API result was not saved as a dataset. Search candidates whose history had no valid traded observations were also excluded, and their empty histories were not retained."}]
    replace_rows(ROOT / "metadata" / "data_issues.csv", ISSUE_FIELDS, "issue_id", ("issue_tsetmc_",), issues)

    manifest_rows = []
    for layer in ("raw", "cleaned", "derived"):
        for path in sorted((ROOT / "data" / layer).glob("**/*")):
            if path.is_file() and path.name not in {".gitkeep", "README.md"}:
                relative = path.relative_to(ROOT)
                # Dated TSETMC API caches are intentionally local/reproducible
                # rather than distributed through Git. Catalog provenance still
                # records their paths; the repository manifest covers files a
                # fresh clone is expected to contain.
                if layer == "raw" and any(part.startswith(("tsetmc_housing_market_", "tsetmc_construction_materials_")) for part in relative.parts):
                    continue
                manifest_rows.append({"layer": layer, "category": path.relative_to(ROOT / "data" / layer).parts[0], "path": str(path.relative_to(ROOT)).replace("\\", "/"), "file_format": path.suffix.lower().lstrip("."), "size_bytes": path.stat().st_size, "checksum_sha256": sha256(path)})
    write_csv(ROOT / "metadata" / "file_manifest.csv", ["layer", "category", "path", "file_format", "size_bytes", "checksum_sha256"], manifest_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Retrieve a new raw batch from official TSETMC APIs")
    parser.add_argument("--as-of", help="Gregorian collection date YYYY-MM-DD; defaults to today for refresh or latest retained batch for rebuild")
    args = parser.parse_args()

    if args.refresh:
        configure_batch(args.as_of or date.today().isoformat())
    else:
        configure_batch(args.as_of or latest_retained_batch_date())

    if args.refresh:
        urls = discovery_urls()
        discovery = fetch_all(urls, workers=4)
        candidates = discover(discovery)
        history_raw = fetch_all(history_urls(candidates), workers=6)
        instruments = []
        for item in candidates:
            try:
                clean_instrument_history(item, history_raw[f"instrument_{item.ins_code}"])
            except ValueError:
                # A search hit can be a never-traded/empty legacy series. It is
                # not a usable dataset and its response must not be retained.
                history_raw.pop(f"instrument_{item.ins_code}")
            else:
                instruments.append(item)
        groups = {item.group for item in instruments}
        if groups != {"mortgage_certificates", "real_estate_funds", "real_estate_developers"}:
            raise ValueError(f"A requested instrument group has no valid histories: {sorted(groups)}")
        for key in INDEXES:
            clean_index_history(key, history_raw[f"index_{key}"])
        write_raw(discovery, history_raw, instruments)
    else:
        discovery, history_raw = read_raw()
        candidates = discover(discovery)
        instruments = [item for item in candidates if f"instrument_{item.ins_code}" in history_raw]
        required = {f"instrument_{item.ins_code}" for item in instruments} | {f"index_{key}" for key in INDEXES}
        if set(history_raw) != required:
            raise ValueError(f"Retained raw histories incomplete: missing={sorted(required-set(history_raw))}, extra={sorted(set(history_raw)-required)}")

    outputs = persist_outputs(instruments, history_raw)
    update_metadata(outputs, instruments)
    counts = {group: sum(item.group == group for item in instruments) for group in {item.group for item in instruments}}
    print(f"Validated TSETMC extraction: instruments={counts}; datasets={len(outputs)}")


if __name__ == "__main__":
    main()
