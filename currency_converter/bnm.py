"""National Bank of Moldova XML feed client and parser."""

from __future__ import annotations

import http.client
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

from currency_converter.models import CurrencyQuote, RateSet

BNM_URL_TEMPLATE = "https://www.bnm.md/en/official_exchange_rates?get_xml=1&date={date}"
DEFAULT_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_USER_AGENT = "CurrencyConverterBNM/1.0 (Desktop Python urllib)"
NBM_SOURCE_NAME = "Национальный банк Молдовы"


class FetchStatus(str, Enum):
    """Classification of an NBM rate-feed response."""

    OK = "ok"
    DATE_MISS = "date_miss"
    SOURCE_ERROR = "source_error"


@dataclass(frozen=True)
class FetchOutcome:
    """Typed result of fetching or parsing an NBM XML document."""

    status: FetchStatus
    rate_set: RateSet | None = None
    error_message: str | None = None


def build_bnm_url(rate_date: date) -> str:
    """Build the dated NBM XML feed URL."""
    return BNM_URL_TEMPLATE.format(date=rate_date.strftime("%d.%m.%Y"))


def _parse_positive_decimal(raw_text: str) -> Decimal | None:
    """Parse a positive finite Decimal from NBM numeric text, or return None."""
    normalized = raw_text.strip().replace(",", ".")
    if not normalized:
        return None
    try:
        value = Decimal(normalized)
    except InvalidOperation:
        return None
    if not value.is_finite() or value <= 0:
        return None
    return value


def _child_text(element: ET.Element, tag: str) -> str:
    """Return stripped text of a direct XML child element, or empty string."""
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _parse_valute_element(element: ET.Element) -> CurrencyQuote | None:
    """Parse one <Valute> element into a CurrencyQuote, or None if invalid."""
    num_code = _child_text(element, "NumCode")
    char_code = _child_text(element, "CharCode").upper()
    name = _child_text(element, "Name")
    nominal = _parse_positive_decimal(_child_text(element, "Nominal"))
    value_mdl = _parse_positive_decimal(_child_text(element, "Value"))

    if not num_code or not char_code or not name or nominal is None or value_mdl is None:
        return None

    try:
        return CurrencyQuote(
            code=char_code,
            numeric_code=num_code,
            name=name,
            nominal=nominal,
            value_mdl=value_mdl,
        )
    except ValueError:
        return None


def _parse_valcurs_date(raw_date: str) -> date | None:
    """Parse ValCurs Date attribute in DD.MM.YYYY format."""
    text = raw_date.strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return None


def parse_bnm_xml(
    payload: bytes | str,
    *,
    fetched_at_utc: datetime | None = None,
) -> FetchOutcome:
    """Parse and classify an NBM XML payload into a FetchOutcome."""
    raw_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    if len(raw_bytes) > MAX_RESPONSE_BYTES:
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="Ответ НБМ превышает допустимый размер.",
        )

    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError:
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="Источник вернул некорректные данные вместо XML курсов НБМ.",
        )

    if root.tag != "ValCurs":
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="Источник вернул неожиданный формат данных вместо курсов НБМ.",
        )

    valute_elements = root.findall("Valute")
    if not valute_elements:
        return FetchOutcome(status=FetchStatus.DATE_MISS)

    rate_date = _parse_valcurs_date(root.attrib.get("Date", ""))
    if rate_date is None:
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="В ответе НБМ отсутствует корректная дата курсов.",
        )

    quotes: dict[str, CurrencyQuote] = {}
    for valute in valute_elements:
        quote = _parse_valute_element(valute)
        if quote is not None and quote.code not in quotes:
            quotes[quote.code] = quote

    if not quotes:
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="Ответ НБМ не содержит пригодных курсов валют.",
        )

    timestamp = fetched_at_utc if fetched_at_utc is not None else datetime.now(timezone.utc)
    rate_set = RateSet(
        rate_date=rate_date,
        fetched_at_utc=timestamp,
        source=NBM_SOURCE_NAME,
        quotes=quotes,
    )
    return FetchOutcome(status=FetchStatus.OK, rate_set=rate_set)


def fetch_rates_for_date(
    rate_date: date,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> FetchOutcome:
    """Fetch and parse official NBM exchange rates for a single calendar date."""
    request = urllib.request.Request(
        build_bnm_url(rate_date),
        headers={"User-Agent": user_agent},
    )

    try:
        with opener(request, timeout=timeout) as response:
            raw_bytes = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        try:
            if exc.code == 404:
                error_body = exc.read(MAX_RESPONSE_BYTES + 1)
                if not error_body.strip():
                    return FetchOutcome(status=FetchStatus.DATE_MISS)
                return FetchOutcome(
                    status=FetchStatus.SOURCE_ERROR,
                    error_message="Сервер НБМ вернул ошибку 404.",
                )
            return FetchOutcome(
                status=FetchStatus.SOURCE_ERROR,
                error_message=f"Ошибка сервиса НБМ (HTTP {exc.code}).",
            )
        finally:
            exc.close()
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException, ValueError):
        return FetchOutcome(
            status=FetchStatus.SOURCE_ERROR,
            error_message="Не удалось получить курсы НБМ. Проверьте подключение к интернету.",
        )

    return parse_bnm_xml(raw_bytes)
