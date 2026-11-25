"""Tkinter desktop user interface for the Moldova currency converter."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from currency_converter.conversion import format_amount, format_rate
from currency_converter.models import (
    DEFAULT_CURRENCY_CHOICES,
    ConversionRequest,
    ConversionResult,
)
from currency_converter.service import RateService, ServiceOutcome, ServiceStatus

POLL_INTERVAL_MS = 50


class CurrencyConverterApp:
    """Main Tkinter form and result presenter for currency conversion."""

    def __init__(self, root: tk.Tk, service: RateService | None = None) -> None:
        self.root = root
        self._service = service if service is not None else RateService()
        self._outcome_queue: queue.Queue[tuple[int, ServiceOutcome]] = queue.Queue()
        self._request_seq = 0
        self._is_busy = False
        self._closing = False
        self._after_id: str | None = None
        self._last_result: ConversionResult | None = None

        self.root.title("Конвертер валют Молдовы (НБМ)")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.amount_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.date_var = tk.StringVar()

        self.status_var = tk.StringVar()
        self.result_amount_var = tk.StringVar(value="Результат: —")
        self.forward_rate_var = tk.StringVar(value="Прямой курс: —")
        self.reverse_rate_var = tk.StringVar(value="Обратный курс: —")
        self.rate_date_var = tk.StringVar(value="Дата курса: —")
        self.rate_source_var = tk.StringVar(value="Источник: —")

        self._build_widgets()
        self._bind_state_traces()
        self._update_convert_button_state()

    def _build_widgets(self) -> None:
        """Create and lay out all Tkinter/ttk form and result widgets."""
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        ttk.Label(container, text="Сумма:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.amount_entry = ttk.Entry(container, textvariable=self.amount_var, width=28)
        self.amount_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(container, text="Из валюты:").grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.source_combo = ttk.Combobox(
            container,
            textvariable=self.source_var,
            values=list(DEFAULT_CURRENCY_CHOICES),
            state="readonly",
            width=25,
        )
        self.source_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(container, text="В валюту:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.target_combo = ttk.Combobox(
            container,
            textvariable=self.target_var,
            values=list(DEFAULT_CURRENCY_CHOICES),
            state="readonly",
            width=25,
        )
        self.target_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(container, text="Дата курса (ДД.ММ.ГГГГ):").grid(
            row=3, column=0, sticky="w", pady=(0, 2)
        )
        self.date_entry = ttk.Entry(container, textvariable=self.date_var, width=28)
        self.date_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(0, 2))

        ttk.Label(container, text="Оставьте пустым для сегодняшней даты").grid(
            row=4, column=1, columnspan=2, sticky="w", pady=(0, 10)
        )

        buttons_frame = ttk.Frame(container)
        buttons_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)

        self.convert_button = ttk.Button(
            buttons_frame,
            text="Конвертировать",
            command=self.on_convert,
            state="disabled",
        )
        self.convert_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.swap_button = ttk.Button(
            buttons_frame,
            text="Поменять местами",
            command=self.on_swap,
        )
        self.swap_button.grid(row=0, column=1, sticky="ew")

        self.status_label = ttk.Label(
            container,
            textvariable=self.status_var,
            foreground="#a40000",
            wraplength=380,
            justify="left",
        )
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 10))

        result_frame = ttk.LabelFrame(container, text="Результат", padding=12)
        result_frame.grid(row=7, column=0, columnspan=3, sticky="ew")

        ttk.Label(result_frame, textvariable=self.result_amount_var).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(result_frame, textvariable=self.forward_rate_var).grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(result_frame, textvariable=self.reverse_rate_var).grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(result_frame, textvariable=self.rate_date_var).grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(result_frame, textvariable=self.rate_source_var).grid(
            row=4, column=0, sticky="w"
        )

    def _bind_state_traces(self) -> None:
        """Keep the Convert button state synchronised with required inputs."""
        for var in (self.amount_var, self.source_var, self.target_var):
            var.trace_add("write", lambda *_args: self._update_convert_button_state())

    def _has_required_fields(self) -> bool:
        return bool(
            self.amount_var.get().strip()
            and self.source_var.get().strip()
            and self.target_var.get().strip()
        )

    def _update_convert_button_state(self) -> None:
        if self._is_busy or not self._has_required_fields():
            self.convert_button.configure(state="disabled")
        else:
            self.convert_button.configure(state="normal")

    def _set_busy(self, busy: bool) -> None:
        self._is_busy = busy
        entry_state = "disabled" if busy else "normal"
        combo_state = "disabled" if busy else "readonly"
        swap_state = "disabled" if busy else "normal"
        self.amount_entry.configure(state=entry_state)
        self.date_entry.configure(state=entry_state)
        self.source_combo.configure(state=combo_state)
        self.target_combo.configure(state=combo_state)
        self.swap_button.configure(state=swap_state)
        self._update_convert_button_state()

    def _clear_result(self) -> None:
        self._last_result = None
        self.result_amount_var.set("Результат: —")
        self.forward_rate_var.set("Прямой курс: —")
        self.reverse_rate_var.set("Обратный курс: —")
        self.rate_date_var.set("Дата курса: —")
        self.rate_source_var.set("Источник: —")

    def _set_currency_choices(self, currencies: tuple[str, ...] | None) -> None:
        """Update combobox values to reflect the available currency set."""
        choices = list(currencies) if currencies else list(DEFAULT_CURRENCY_CHOICES)
        current_source = self.source_var.get()
        current_target = self.target_var.get()
        self.source_combo.configure(values=choices)
        self.target_combo.configure(values=choices)
        if current_source not in choices:
            self.source_var.set("")
        if current_target not in choices:
            self.target_var.set("")

    def _build_request(self) -> ConversionRequest | None:
        raw_amount = self.amount_var.get().strip()
        if not raw_amount:
            self._clear_result()
            self.status_var.set("Введите сумму для конвертации.")
            return None

        if any(ch.isspace() for ch in raw_amount) or "_" in raw_amount:
            self._clear_result()
            self.status_var.set("Введите корректную положительную сумму.")
            return None

        normalized_amount = raw_amount.replace(",", ".")
        try:
            amount = Decimal(normalized_amount)
        except InvalidOperation:
            self._clear_result()
            self.status_var.set("Введите корректную положительную сумму.")
            return None

        if not amount.is_finite() or amount <= 0:
            self._clear_result()
            self.status_var.set("Сумма должна быть больше нуля.")
            return None

        source_currency = self.source_var.get().strip()
        target_currency = self.target_var.get().strip()
        if not source_currency or not target_currency:
            self._clear_result()
            self.status_var.set("Выберите исходную и целевую валюты.")
            return None

        raw_date = self.date_var.get().strip()
        if not raw_date:
            requested_date = date.today()
        else:
            try:
                requested_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
            except ValueError:
                self._clear_result()
                self.status_var.set("Введите дату в формате ДД.ММ.ГГГГ.")
                return None

        return ConversionRequest(
            amount=amount,
            source_currency=source_currency,
            target_currency=target_currency,
            requested_date=requested_date,
        )

    def _run_conversion_worker(self, req_id: int, request: ConversionRequest) -> None:
        """Execute rate retrieval and conversion off the Tkinter thread."""
        try:
            outcome = self._service.convert(request)
        except Exception:
            outcome = ServiceOutcome(
                status=ServiceStatus.FAILURE,
                error_message="Произошла ошибка при получении курсов НБМ.",
            )
        self._outcome_queue.put((req_id, outcome))

    def _schedule_poll(self) -> None:
        if not self._closing and self._after_id is None:
            self._after_id = self.root.after(POLL_INTERVAL_MS, self._poll_queue)

    def _poll_queue(self) -> None:
        self._after_id = None
        if self._closing:
            return

        while True:
            try:
                req_id, outcome = self._outcome_queue.get_nowait()
            except queue.Empty:
                break
            if req_id == self._request_seq:
                self._set_busy(False)
                self._handle_outcome(outcome)

        if self._is_busy and not self._closing:
            self._schedule_poll()

    def _handle_outcome(self, outcome: ServiceOutcome) -> None:
        """Route a ServiceOutcome to the appropriate UI response on the main thread."""
        # Always update currency list when provided
        if outcome.available_currencies is not None:
            self._set_currency_choices(outcome.available_currencies)

        if outcome.status == ServiceStatus.OFFER_CACHED:
            self._handle_offer_cached(outcome)
            return

        if outcome.status == ServiceStatus.SUCCESS:
            self._apply_success_result(outcome)
            return

        # FAILURE
        self._clear_result()
        self.status_var.set(outcome.error_message or "Не удалось выполнить конвертацию.")

    def _handle_offer_cached(self, outcome: ServiceOutcome) -> None:
        """Ask the user whether to use the saved rate set; apply or discard accordingly."""
        saved_set = outcome.cached_rate_set
        if saved_set is None:
            self._clear_result()
            self.status_var.set("Сохранённые курсы недоступны.")
            return

        # Build a human-readable offer prompt
        date_str = saved_set.rate_date.strftime("%d.%m.%Y")
        prompt = (
            f"Курсы НБМ за запрошенный период недоступны.\n\n"
            f"Доступны сохранённые курсы от {date_str}.\n"
            f"Использовать их для конвертации?"
        )
        use_saved = messagebox.askyesno(
            title="Использовать сохранённые курсы?",
            message=prompt,
            parent=self.root,
        )

        if not use_saved:
            self._clear_result()
            self.status_var.set(
                f"Конвертация не выполнена. Сохранённые курсы от {date_str} не были использованы."
            )
            return

        request = self._build_request()
        if request is None:
            return

        result_outcome = self._service.convert_with_rate_set(
            request,
            saved_set,
            used_cached_rates=True,
        )
        if result_outcome.available_currencies is not None:
            self._set_currency_choices(result_outcome.available_currencies)
        self._apply_success_result(result_outcome)

    def _apply_success_result(self, outcome: ServiceOutcome) -> None:
        """Display a successful conversion result in the result area."""
        if outcome.result is None:
            self._clear_result()
            self.status_var.set(outcome.error_message or "Не удалось выполнить конвертацию.")
            return

        result = outcome.result
        self._last_result = result

        source_currency = self.source_var.get()
        target_currency = self.target_var.get()

        amount_text = format_amount(result.amount_exact)
        forward_text = format_rate(result.source_to_target_rate_exact)
        reverse_text = format_rate(result.target_to_source_rate_exact)

        self.result_amount_var.set(f"Результат: {amount_text} {target_currency}")
        self.forward_rate_var.set(
            f"Прямой курс: 1 {source_currency} = {forward_text} {target_currency}"
        )
        self.reverse_rate_var.set(
            f"Обратный курс: 1 {target_currency} = {reverse_text} {source_currency}"
        )

        if result.rate_set is None:
            # Identity conversion
            self.rate_date_var.set("Дата курса: не применимо")
            self.rate_source_var.set("Источник: внешний курс не запрашивался")
            self.status_var.set("")
            return

        actual_date_str = result.rate_set.rate_date.strftime("%d.%m.%Y")
        requested_date_str = result.requested_date.strftime("%d.%m.%Y")

        # Build status note about rate freshness
        status_parts: list[str] = []
        if result.used_cached_rates:
            status_parts.append(
                f"Использованы сохранённые курсы от {actual_date_str}."
            )
        elif result.used_earlier_date:
            status_parts.append(
                f"За {requested_date_str} курсы не опубликованы. "
                f"Использованы курсы от {actual_date_str}."
            )
        self.status_var.set(" ".join(status_parts))

        self.rate_date_var.set(f"Дата курса: {actual_date_str}")
        self.rate_source_var.set(f"Источник: {result.rate_set.source}")

    def on_convert(self) -> None:
        if self._is_busy:
            return

        request = self._build_request()
        if request is None:
            return

        if request.source_currency == request.target_currency:
            outcome = self._service.convert(request)
            self._handle_outcome(outcome)
            return

        self.status_var.set("Загрузка курсов НБМ...")
        self._clear_result()
        self._set_busy(True)
        self._request_seq += 1
        req_id = self._request_seq

        worker = threading.Thread(
            target=self._run_conversion_worker,
            args=(req_id, request),
            daemon=True,
        )
        worker.start()
        self._schedule_poll()

    def on_swap(self) -> None:
        if self._is_busy:
            return

        previous_result = self._last_result
        source = self.source_var.get()
        target = self.target_var.get()

        self.source_var.set(target)
        self.target_var.set(source)

        if previous_result is None:
            return

        request = self._build_request()
        if request is None:
            return

        if request.source_currency == request.target_currency:
            outcome = self._service.convert_with_rate_set(request, None)
            self._handle_outcome(outcome)
            return

        if previous_result.rate_set is None:
            self._clear_result()
            return

        outcome = self._service.convert_with_rate_set(
            request,
            previous_result.rate_set,
            used_cached_rates=previous_result.used_cached_rates,
        )
        self._handle_outcome(outcome)

    def on_close(self) -> None:
        self._closing = True
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.root.destroy()


def run_app(service: RateService | None = None) -> None:
    """Create the Tk root window, attach CurrencyConverterApp, and start the event loop."""
    root = tk.Tk()
    CurrencyConverterApp(root, service=service)
    root.mainloop()
