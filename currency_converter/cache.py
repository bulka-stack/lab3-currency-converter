"""JSON cache for the last successfully received NBM rate set."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from currency_converter.models import CurrencyQuote, RateSet
from currency_converter.bnm import NBM_SOURCE_NAME

CACHE_APP_DIR = "CurrencyConverterBNM"
CACHE_FILENAME = "rates.json"


def _get_cache_path() -> str:
    """Return the absolute path to the JSON cache file."""
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    cache_dir = os.path.join(app_data, CACHE_APP_DIR)
    return os.path.join(cache_dir, CACHE_FILENAME)


def _ensure_cache_dir(cache_path: str) -> None:
    """Create the cache directory if it does not exist."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)


def _rate_set_to_dict(rate_set: RateSet) -> dict:
    """Serialise a RateSet to a plain-dict structure suitable for JSON."""
    quotes_list = []
    for code, quote in rate_set.quotes.items():
        quotes_list.append({
            "code": quote.code,
            "numeric_code": quote.numeric_code,
            "name": quote.name,
            "nominal": str(quote.nominal),
            "value_mdl": str(quote.value_mdl),
        })
    return {
        "rate_date": rate_set.rate_date.strftime("%Y-%m-%d"),
        "fetched_at_utc": rate_set.fetched_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": rate_set.source,
        "quotes": quotes_list,
    }


def _dict_to_rate_set(data: dict) -> RateSet:
    """Deserialise a plain dict (from JSON) into a RateSet; raise ValueError if invalid."""
    rate_date = datetime.strptime(data["rate_date"], "%Y-%m-%d").date()
    fetched_at_utc = datetime.strptime(data["fetched_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    source = data["source"]
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Invalid source in cache.")

    quotes: dict[str, CurrencyQuote] = {}
    for entry in data["quotes"]:
        code = entry["code"]
        numeric_code = entry["numeric_code"]
        name = entry["name"]
        try:
            nominal = Decimal(entry["nominal"])
            value_mdl = Decimal(entry["value_mdl"])
        except (InvalidOperation, KeyError):
            continue
        try:
            quote = CurrencyQuote(
                code=code,
                numeric_code=numeric_code,
                name=name,
                nominal=nominal,
                value_mdl=value_mdl,
            )
            quotes[code] = quote
        except (ValueError, KeyError):
            continue

    if not quotes:
        raise ValueError("No usable quotes in cached data.")

    return RateSet(
        rate_date=rate_date,
        fetched_at_utc=fetched_at_utc,
        source=source,
        quotes=quotes,
    )


def load_cached_rates() -> tuple[RateSet | None, str | None]:
    """Load the saved rate set from disk.

    Returns (rate_set, None) on success, (None, None) if missing, or
    (None, error_message) if the cache exists but is unreadable/corrupt.
    """
    cache_path = _get_cache_path()
    if not os.path.exists(cache_path):
        return None, None

    try:
        with open(cache_path, encoding="utf-8") as fh:
            data = json.load(fh)
        rate_set = _dict_to_rate_set(data)
        return rate_set, None
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError):
        return None, (
            "Сохранённые курсы повреждены или не читаются. Данные кэша будут проигнорированы."
        )


def save_cached_rates(rate_set: RateSet) -> str | None:
    """Atomically write a usable rate set to the JSON cache.

    Returns None on success or a short Russian error message on failure.
    Does nothing (returns None) if rate_set has no quotes.
    """
    if not rate_set.quotes:
        return None

    cache_path = _get_cache_path()
    try:
        _ensure_cache_dir(cache_path)
        data = _rate_set_to_dict(rate_set)
        cache_dir = os.path.dirname(cache_path)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=cache_dir,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, cache_path)
        return None
    except OSError:
        return "Не удалось сохранить курсы НБМ. Кэш не обновлён."
