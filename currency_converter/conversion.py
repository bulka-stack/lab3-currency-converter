"""MDL-normalized currency conversion math and display formatting."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from currency_converter.models import (
    BASE_CURRENCY,
    DEFAULT_CURRENCY_CHOICES,
    ConversionRequest,
    ConversionResult,
    RateSet,
)

AMOUNT_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.0001")


def get_mdl_per_unit(currency_code: str, rate_set: RateSet) -> Decimal:
    """Return unrounded MDL per one unit of currency_code."""
    if currency_code == BASE_CURRENCY:
        return Decimal("1")
    quote = rate_set.quotes.get(currency_code)
    if quote is None:
        raise ValueError(f"Валюта {currency_code} отсутствует в выбранном наборе курсов.")
    return quote.mdl_per_unit


def convert_currency(
    request: ConversionRequest,
    rate_set: RateSet | None = None,
    *,
    used_cached_rates: bool = False,
) -> ConversionResult:
    """Convert an amount according to NBM MDL-normalized rates without intermediate rounding."""
    if request.source_currency == request.target_currency:
        return ConversionResult(
            amount_exact=request.amount,
            source_to_target_rate_exact=Decimal("1"),
            target_to_source_rate_exact=Decimal("1"),
            rate_set=None,
            requested_date=request.requested_date,
            used_cached_rates=False,
            used_earlier_date=False,
        )

    if rate_set is None or not rate_set.quotes:
        raise ValueError("Для конвертации разных валют необходим пригодный набор курсов.")

    source_mdl = get_mdl_per_unit(request.source_currency, rate_set)
    target_mdl = get_mdl_per_unit(request.target_currency, rate_set)

    if request.source_currency == BASE_CURRENCY:
        amount_exact = request.amount / target_mdl
        source_to_target = Decimal("1") / target_mdl
        target_to_source = target_mdl
    elif request.target_currency == BASE_CURRENCY:
        amount_exact = request.amount * source_mdl
        source_to_target = source_mdl
        target_to_source = Decimal("1") / source_mdl
    else:
        amount_exact = request.amount * source_mdl / target_mdl
        source_to_target = source_mdl / target_mdl
        target_to_source = target_mdl / source_mdl

    return ConversionResult(
        amount_exact=amount_exact,
        source_to_target_rate_exact=source_to_target,
        target_to_source_rate_exact=target_to_source,
        rate_set=rate_set,
        requested_date=request.requested_date,
        used_cached_rates=used_cached_rates,
        used_earlier_date=rate_set.rate_date < request.requested_date,
    )


def format_amount(value: Decimal) -> str:
    """Format an exact monetary amount to 2 decimal places using ROUND_HALF_UP."""
    quantized = value.quantize(AMOUNT_QUANTUM, rounding=ROUND_HALF_UP)
    return f"{quantized:f}"


def format_rate(value: Decimal) -> str:
    """Format an exact exchange rate to 4 decimal places using ROUND_HALF_UP."""
    quantized = value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)
    return f"{quantized:f}"


def get_available_currencies(rate_set: RateSet | None) -> tuple[str, ...]:
    """Return available currency choices for the form."""
    if rate_set is None or not rate_set.quotes:
        return DEFAULT_CURRENCY_CHOICES
    foreign_codes = sorted(code for code in rate_set.quotes if code != BASE_CURRENCY)
    return (BASE_CURRENCY, *foreign_codes)
