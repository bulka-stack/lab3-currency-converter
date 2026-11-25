# Desktop UI Contract

## Main Form

The form provides:

- Amount input accepting a positive decimal amount with comma or period as the decimal
  separator; thousands separators are not accepted.
- Source and target currency choices.
- Rate date text input in `DD.MM.YYYY`; an empty field means the current local date.
- Convert and Swap actions.
- A result area for converted amount, both directional rates, actual rate date, and source.

Convert remains disabled until amount and both currency choices are non-empty. A touched,
empty amount shows a short Russian validation message. Invalid non-empty amounts show the same
kind of short Russian message when conversion is requested; no invalid result is shown.

The date input accepts 01.01.1994 through tomorrow. Dates outside that range are rejected with a
short Russian message. If tomorrow has no published rates, the normal earlier-date search
applies.

## Loading and Result States

- While network work is running, show a loading state without blocking the window event loop.
  The worker does not access widgets; UI changes are applied after the main thread receives a
  queued outcome.
- Each displayed result shows the National Bank of Moldova as source, the actual rate date, the
  converted amount to 2 decimal places, and source-to-target and target-to-source rates to
  4 decimal places.
- If an earlier date is used, distinguish the requested date from the actual rate date and
  state that an earlier available rate was used.
- Swap exchanges the selected currencies and recalculates both the result and directional
  rates from the same rate set.
- Identical source and target currencies produce the entered amount and rates of 1 without an
  error.

## Fallback and Error States

- For a no-rates result, search earlier dates one day at a time, up to 10 preceding calendar
  days. If none has usable rates, stop searching.
- If source retrieval fails or the search is exhausted and a saved set exists, offer it with
  its rate date and source. Do not calculate from it until the user accepts. Mark the resulting
  conversion as using saved rates.
- If no usable current or accepted saved rates exist, show a short Russian error message and
  do not show a conversion for different-currency pairs.
- A same-currency selection returns the entered amount and unit rates of 1 without requiring
  network or saved rates. If no rate set is used, explicitly show that the rate date and source
  are not applicable because no external rate was required.
- A corrupt or unreadable cache is treated as missing, reported with a short Russian message,
  and does not terminate the application.
- When neither current nor saved rates are available, show the built-in currency choices
  (MDL, USD, EUR, RUB, RON, UAH, GBP, CHF, TRY, JPY, CNY); a conversion request still reports
  that rates are unavailable.

## State and Thread Ownership

The GUI submits an immutable request snapshot to the rate service. Only one fetch/search
operation is active at a time. While it runs, disable fields and actions that could change or
resubmit that request, while keeping the main window repaintable and closeable. Results and
failures are passed back as plain data through a thread-safe queue; only the Tkinter main thread
updates widgets. The network worker is a daemon; closing the application cancels UI polling and
does not wait synchronously for the worker.
