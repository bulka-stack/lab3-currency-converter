"""Rate retrieval and currency conversion service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import Enum

from currency_converter.bnm import FetchOutcome, FetchStatus, fetch_rates_for_date
from currency_converter.conversion import convert_currency, get_available_currencies
from currency_converter.models import ConversionRequest, ConversionResult, RateSet

RateFetcher = Callable[[date], FetchOutcome]


class ServiceStatus(str, Enum):
    """Outcome classification for RateService operations."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class ServiceOutcome:
    """Typed response returned by RateService to callers."""

    status: ServiceStatus
    result: ConversionResult | None = None
    available_currencies: tuple[str, ...] | None = None
    error_message: str | None = None


class RateService:
    """Coordinates NBM rate fetching and MDL-normalized conversions."""

    def __init__(self, *, fetcher: RateFetcher = fetch_rates_for_date) -> None:
        self._fetcher = fetcher

    def convert(self, request: ConversionRequest) -> ServiceOutcome:
        """Execute a conversion request for the requested date."""
        if request.source_currency == request.target_currency:
            result = convert_currency(request, rate_set=None)
            return ServiceOutcome(status=ServiceStatus.SUCCESS, result=result)

        fetch_outcome = self._fetcher(request.requested_date)
        if fetch_outcome.status == FetchStatus.DATE_MISS:
            return ServiceOutcome(
                status=ServiceStatus.FAILURE,
                error_message="На выбранную дату курсы НБМ не опубликованы.",
            )

        if fetch_outcome.status == FetchStatus.SOURCE_ERROR or fetch_outcome.rate_set is None:
            return ServiceOutcome(
                status=ServiceStatus.FAILURE,
                error_message=fetch_outcome.error_message or "Не удалось получить курсы НБМ.",
            )

        return self.convert_with_rate_set(request, fetch_outcome.rate_set)

    def convert_with_rate_set(
        self,
        request: ConversionRequest,
        rate_set: RateSet | None,
        *,
        used_cached_rates: bool = False,
    ) -> ServiceOutcome:
        """Convert using an already available RateSet (or bypass it for identity pairs)."""
        if request.source_currency == request.target_currency:
            result = convert_currency(request, rate_set=None)
            return ServiceOutcome(status=ServiceStatus.SUCCESS, result=result)

        if rate_set is None:
            return ServiceOutcome(
                status=ServiceStatus.FAILURE,
                error_message="Нет доступного набора курсов для конвертации.",
            )

        try:
            result = convert_currency(
                request,
                rate_set=rate_set,
                used_cached_rates=used_cached_rates,
            )
        except ValueError as exc:
            return ServiceOutcome(
                status=ServiceStatus.FAILURE,
                available_currencies=get_available_currencies(rate_set),
                error_message=str(exc),
            )

        return ServiceOutcome(
            status=ServiceStatus.SUCCESS,
            result=result,
            available_currencies=get_available_currencies(rate_set),
        )
