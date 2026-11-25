"""Rate retrieval and currency conversion service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from currency_converter.bnm import FetchOutcome, FetchStatus, fetch_rates_for_date
from currency_converter.cache import load_cached_rates, save_cached_rates
from currency_converter.conversion import convert_currency, get_available_currencies
from currency_converter.models import ConversionRequest, ConversionResult, RateSet

RateFetcher = Callable[[date], FetchOutcome]

MAX_SEARCH_DAYS = 10


class ServiceStatus(str, Enum):
    """Outcome classification for RateService operations."""

    SUCCESS = "success"
    FAILURE = "failure"
    OFFER_CACHED = "offer_cached"


@dataclass(frozen=True)
class ServiceOutcome:
    """Typed response returned by RateService to callers."""

    status: ServiceStatus
    result: ConversionResult | None = None
    available_currencies: tuple[str, ...] | None = None
    error_message: str | None = None
    # Non-None when status == OFFER_CACHED: saved rate set being offered
    cached_rate_set: RateSet | None = None


class RateService:
    """Coordinates NBM rate fetching, date fallback, caching and MDL-normalized conversions."""

    def __init__(self, *, fetcher: RateFetcher = fetch_rates_for_date) -> None:
        self._fetcher = fetcher

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(self, request: ConversionRequest) -> ServiceOutcome:
        """Execute a conversion request, searching earlier dates and offering cache as needed."""
        if request.source_currency == request.target_currency:
            result = convert_currency(request, rate_set=None)
            return ServiceOutcome(status=ServiceStatus.SUCCESS, result=result)

        rate_set, cache_error = self._fetch_with_date_fallback(request.requested_date)

        if cache_error is not None and rate_set is None:
            # Cache was corrupt; we'll try live fetch normally, error propagated below
            pass

        if rate_set is not None:
            save_error = save_cached_rates(rate_set)
            outcome = self.convert_with_rate_set(request, rate_set)
            if save_error and outcome.status == ServiceStatus.SUCCESS:
                # Annotate with the cache-write warning via error_message while keeping SUCCESS
                return ServiceOutcome(
                    status=outcome.status,
                    result=outcome.result,
                    available_currencies=outcome.available_currencies,
                    error_message=save_error,
                )
            return outcome

        # No live rate found; check for cache offer
        saved_set, load_error = load_cached_rates()
        if saved_set is not None:
            return ServiceOutcome(
                status=ServiceStatus.OFFER_CACHED,
                cached_rate_set=saved_set,
                available_currencies=get_available_currencies(saved_set),
                error_message=(
                    f"Курсы НБМ за запрошенный период недоступны. "
                    f"Доступны сохранённые курсы от "
                    f"{saved_set.rate_date.strftime('%d.%m.%Y')}. Использовать их?"
                ),
            )

        error_msg = cache_error or load_error or (
            "Курсы НБМ за запрошенный период недоступны. Сохранённых курсов нет."
        )
        return ServiceOutcome(
            status=ServiceStatus.FAILURE,
            available_currencies=get_available_currencies(None),
            error_message=error_msg,
        )

    def convert_with_rate_set(
        self,
        request: ConversionRequest,
        rate_set: RateSet | None,
        *,
        used_cached_rates: bool = False,
    ) -> ServiceOutcome:
        """Convert using an already available RateSet (or bypass for identity pairs)."""
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_with_date_fallback(self, requested_date: date) -> tuple[RateSet | None, str | None]:
        """Try requested_date then up to MAX_SEARCH_DAYS preceding days.

        Returns (rate_set, None) on success, (None, error_message) on failure, or
        (None, None) if the search window is exhausted with no result.
        """
        candidate = requested_date
        for _ in range(MAX_SEARCH_DAYS + 1):
            outcome = self._fetcher(candidate)

            if outcome.status == FetchStatus.OK and outcome.rate_set is not None:
                return outcome.rate_set, None

            if outcome.status == FetchStatus.DATE_MISS:
                candidate = candidate - timedelta(days=1)
                continue

            # SOURCE_ERROR: stop date searching immediately
            return None, outcome.error_message or "Не удалось получить курсы НБМ."

        return None, None
