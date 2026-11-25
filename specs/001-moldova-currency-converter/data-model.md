# Data Model: Moldova Currency Converter

## Currency Quote

Represents one usable currency entry from an NBM rate set.

| Field | Type | Constraints |
|---|---|---|
| `code` | string | Alphabetic currency code from `CharCode`; unique within a rate set. |
| `numeric_code` | string | Preserve `NumCode` as text, including leading zeroes. |
| `name` | string | Currency name from the source. |
| `nominal` | `Decimal` | Positive quantity of foreign units covered by the quote. |
| `value_mdl` | `Decimal` | Positive MDL value for `nominal` foreign units. |

Derived value:

- `mdl_per_unit = value_mdl / nominal`, without intermediate rounding.
- MDL itself is represented as 1 MDL per unit and does not require an NBM quote.

An individual source entry missing required fields, containing invalid numeric text, or having
non-positive nominal/value is skipped. Valid sibling entries remain usable.

## Rate Set

Represents one dated collection of published currency quotes.

| Field | Type | Constraints |
|---|---|---|
| `rate_date` | date | Actual date reported by the `ValCurs` document. |
| `fetched_at_utc` | timestamp | UTC time when this response was successfully received and parsed. |
| `source` | string | National Bank of Moldova official exchange rates. |
| `quotes` | map of currency code to `Currency Quote` | Contains all usable entries from one response; MDL is implicit. |

An empty valid rate set has no quotes and means no published rates for that date. It is not
eligible for cache replacement. The cache stores at most one usable rate set.

The JSON cache file is `%APPDATA%\CurrencyConverterBNM\rates.json`. It stores one serialized
usable `Rate Set` with every valid quote and its UTC fetch timestamp. The file is replaced only
after a complete temporary file has been written in the same directory.

## Conversion Request

| Field | Type | Constraints |
|---|---|---|
| `amount` | `Decimal` | Must be greater than zero; decimal comma or decimal point accepted, no thousands separator. |
| `source_currency` | string | MDL or a currency present in the selected usable rate set. |
| `target_currency` | string | MDL or a currency present in the selected usable rate set. |
| `requested_date` | date | Text input `DD.MM.YYYY`; blank means local today; allowed from 1994-01-01 through tomorrow. |

Selecting the same source and target currency is valid.

## Conversion Result

| Field | Type | Constraints |
|---|---|---|
| `amount_exact` | `Decimal` | Full-precision result before display formatting. |
| `source_to_target_rate_exact` | `Decimal` | Full-precision rate for one source unit in target units. |
| `target_to_source_rate_exact` | `Decimal` | Full-precision inverse rate. |
| `rate_set` | optional `Rate Set` | The set used for a rate-based result; absent for a same-currency identity result that needs no external rate. |
| `requested_date` | date | Date chosen or inferred from the blank field. |
| `used_cached_rates` | boolean | True only after user approval to use the saved rate set. |
| `used_earlier_date` | boolean | True if the actual rate date is earlier than the requested date. |

Only presentation rounds values: amount to 2 decimal places and both rates to 4 decimal places,
using `ROUND_HALF_UP`. No intermediate value is rounded.

An identity result without a `Rate Set` displays the rate date and source as not applicable,
with a note that no external rate was required.

For currency A to currency B:

- `MDL -> B`: `amount / mdl_per_unit(B)`
- `A -> MDL`: `amount * mdl_per_unit(A)`
- `A -> B`: `amount * mdl_per_unit(A) / mdl_per_unit(B)`
- `A -> A`: unchanged amount and rates of 1 in both directions.

The `A -> A` identity case does not require a `Rate Set`. Other currency pairs require usable
current or user-approved saved rates.

## Currency Choices

When a usable rate set is available, choices are MDL and every currency with a usable quote in
that set. If current and saved rates are both unavailable, show the built-in choices:
MDL, USD, EUR, RUB, RON, UAH, GBP, CHF, TRY, JPY, and CNY. Those fallback choices do not imply
that conversion is possible without rate data.

## Cache State and Service State

Cache load has three outcomes: usable saved set, missing/corrupt/unreadable set, or cache I/O
failure. Corrupt data is treated as missing and never terminates the application. Cache writes
replace the prior usable set only after a complete usable source response has been parsed. A
cache write failure does not invalidate a current in-memory rate set; it produces a short Russian
message and the current conversion may still complete.

The rate service moves through:

1. **Idle**: accepts a validated request.
2. **Fetching requested date**: performs a network request off the UI thread.
3. **Searching earlier dates**: entered only for a valid no-rates result; checks one preceding
   day at a time, up to 10 preceding calendar days.
4. **Offering saved rates**: entered after source failure or exhausted no-rates search when a
   usable saved set exists; waits for explicit user approval.
5. **Completed**: returns a current, earlier, or user-approved cached result to the UI thread.
6. **Unavailable**: returns a Russian-message error when no usable source or approved saved set
   exists.

Every transition returns data or a typed failure result to the UI thread; worker code does not
read or mutate Tkinter widgets.
