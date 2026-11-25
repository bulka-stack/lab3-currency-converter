"""Shared domain models for the Moldova currency converter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

BASE_CURRENCY = "MDL"
DEFAULT_CURRENCY_CHOICES: tuple[str, ...] = (
    "MDL",
    "USD",
    "EUR",
    "RUB",
    "RON",
    "UAH",
    "GBP",
    "CHF",
    "TRY",
    "JPY",
    "CNY",
)


def _require_non_empty_text(value: str, field_name: str) -> None:
    """Validate that a string field is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_positive_decimal(value: Decimal, field_name: str) -> None:
    """Validate that a numeric field is a finite positive Decimal."""
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ValueError(f"{field_name} must be a positive finite Decimal.")


def _require_date(value: date, field_name: str) -> None:
    """Validate that a date field is a calendar date (not a datetime)."""
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime.date instance.")


@dataclass(frozen=True)
class CurrencyQuote:
    """One usable currency entry from an NBM exchange-rate publication."""

    code: str
    numeric_code: str
    name: str
    nominal: Decimal
    value_mdl: Decimal

    def __post_init__(self) -> None:
        _require_non_empty_text(self.code, "code")
        if not self.code.isascii() or not self.code.isalpha():
            raise ValueError("code must be an alphabetic currency code.")
        _require_non_empty_text(self.numeric_code, "numeric_code")
        _require_non_empty_text(self.name, "name")
        _require_positive_decimal(self.nominal, "nominal")
        _require_positive_decimal(self.value_mdl, "value_mdl")

    @property
    def mdl_per_unit(self) -> Decimal:
        """Return the unrounded MDL value for one foreign currency unit."""
        return self.value_mdl / self.nominal


@dataclass(frozen=True)
class RateSet:
    """Dated collection of usable currency quotes from the NBM."""

    rate_date: date
    fetched_at_utc: datetime
    source: str
    quotes: Mapping[str, CurrencyQuote]

    def __post_init__(self) -> None:
        _require_date(self.rate_date, "rate_date")
        if not isinstance(self.fetched_at_utc, datetime):
            raise ValueError("fetched_at_utc must be a datetime instance.")
        _require_non_empty_text(self.source, "source")
        if not isinstance(self.quotes, Mapping):
            raise ValueError("quotes must be a mapping of currency codes to CurrencyQuote.")
        for key, quote in self.quotes.items():
            if not isinstance(quote, CurrencyQuote):
                raise ValueError("All quote values must be CurrencyQuote instances.")
            if key != quote.code:
                raise ValueError(f"Quote key {key!r} does not match quote code {quote.code!r}.")


@dataclass(frozen=True)
class ConversionRequest:
    """Validated user request snapshot for currency conversion."""

    amount: Decimal
    source_currency: str
    target_currency: str
    requested_date: date

    def __post_init__(self) -> None:
        _require_positive_decimal(self.amount, "amount")
        _require_non_empty_text(self.source_currency, "source_currency")
        _require_non_empty_text(self.target_currency, "target_currency")
        _require_date(self.requested_date, "requested_date")


@dataclass(frozen=True)
class ConversionResult:
    """Full-precision conversion outcome and rate-origin metadata."""

    amount_exact: Decimal
    source_to_target_rate_exact: Decimal
    target_to_source_rate_exact: Decimal
    rate_set: RateSet | None
    requested_date: date
    used_cached_rates: bool = False
    used_earlier_date: bool = False

    def __post_init__(self) -> None:
        _require_positive_decimal(self.amount_exact, "amount_exact")
        _require_positive_decimal(
            self.source_to_target_rate_exact, "source_to_target_rate_exact"
        )
        _require_positive_decimal(
            self.target_to_source_rate_exact, "target_to_source_rate_exact"
        )
        if self.rate_set is not None and not isinstance(self.rate_set, RateSet):
            raise ValueError("rate_set must be a RateSet instance or None.")
        _require_date(self.requested_date, "requested_date")
        if not isinstance(self.used_cached_rates, bool):
            raise ValueError("used_cached_rates must be a bool.")
        if not isinstance(self.used_earlier_date, bool):
            raise ValueError("used_earlier_date must be a bool.")
        if self.rate_set is None and (self.used_cached_rates or self.used_earlier_date):
            raise ValueError(
                "used_cached_rates and used_earlier_date must be False when rate_set is None."
            )
