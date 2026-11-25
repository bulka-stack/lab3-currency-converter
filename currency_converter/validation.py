"""Pure input parsing and validation for the Moldova currency converter.

This module has no GUI imports and may be used in offline unit tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Only plain decimal digits with an optional single comma or period separator.
# Rejects scientific notation (1e3), leading/trailing signs, infinity, NaN,
# underscores, and anything else Decimal accepts but we do not.
_AMOUNT_RE = re.compile(r"^[0-9]+([.,][0-9]*)?$")


# Earliest date for which NBM rates are considered valid.
MIN_RATE_DATE = date(1994, 1, 1)


@dataclass(frozen=True)
class ParsedAmount:
    """Successfully parsed positive Decimal amount."""

    value: Decimal


@dataclass(frozen=True)
class AmountError:
    """Validation failure for an amount field."""

    message: str


@dataclass(frozen=True)
class ParsedDate:
    """Successfully parsed calendar date."""

    value: date


@dataclass(frozen=True)
class DateError:
    """Validation failure for a date field."""

    message: str


AmountResult = ParsedAmount | AmountError
DateResult = ParsedDate | DateError


def parse_amount(raw: str) -> AmountResult:
    """Parse and validate an amount string.

    Accepts a positive decimal with comma or period as the decimal separator.
    Rejects empty strings, non-numeric text, zero, negative values, and
    strings that contain thousands separators or whitespace.

    Returns a ParsedAmount on success or an AmountError with a short Russian
    message on failure.
    """
    text = raw.strip()
    if not text:
        return AmountError("Введите сумму для конвертации.")

    # Allow only digits with an optional single comma or period decimal separator.
    # This rejects scientific notation (1e3), signs, underscores, inf, nan, etc.
    if not _AMOUNT_RE.match(text):
        return AmountError("Введите корректную положительную сумму.")

    # Normalise decimal separator then parse; the regex already guarantees at
    # most one separator and pure digits, so InvalidOperation cannot happen here,
    # but we keep the guard for safety.
    normalised = text.replace(",", ".")
    try:
        value = Decimal(normalised)
    except InvalidOperation:
        return AmountError("Введите корректную положительную сумму.")

    if not value.is_finite():
        return AmountError("Введите корректную положительную сумму.")

    if value <= 0:
        return AmountError("Сумма должна быть больше нуля.")

    return ParsedAmount(value=value)


def parse_date(raw: str) -> DateResult:
    """Parse and validate a rate-date string.

    An empty string resolves to today's local date.  A non-empty string must
    be in DD.MM.YYYY format and fall within [01.01.1994, tomorrow] inclusive.

    Returns a ParsedDate on success or a DateError with a short Russian
    message on failure.
    """
    text = raw.strip()
    if not text:
        return ParsedDate(value=date.today())

    try:
        parsed = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return DateError("Введите дату в формате ДД.ММ.ГГГГ.")

    tomorrow = date.today() + __import__("datetime").timedelta(days=1)

    if parsed < MIN_RATE_DATE:
        return DateError(
            f"Дата не может быть раньше {MIN_RATE_DATE.strftime('%d.%m.%Y')}."
        )

    if parsed > tomorrow:
        return DateError("Дата не может быть позже завтрашнего дня.")

    return ParsedDate(value=parsed)
