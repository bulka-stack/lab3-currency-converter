# Research: Moldova Currency Converter

## Decisions

### Official NBM rates and nominal normalization

- **Decision**: Use the dated National Bank of Moldova XML rate feed supplied for the feature:
  `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`. Treat each
  `Value` as MDL for the number of foreign-currency units in `Nominal`; normalize to MDL per
  one unit before converting. Treat these as official reference rates, not bank cash
  buy/sell prices.
- **Rationale**: The XML root is `ValCurs` with a `Date` attribute and repeated `Valute` entries
  containing fields such as `CharCode`, `Nominal`, `Name`, and `Value`. The official NBM table
  labels the corresponding quantity and rate fields. For example, the 25 November 2026 response
  quotes JPY per 100 units.
- **Alternatives considered**: A commercial provider or bank buy/sell quotations were rejected
  because the feature requires the NBM official publication.
- **Sources**: [NBM dated XML example](https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=25.11.2026);
  [NBM official rates table](https://www.bnm.md/ro/content/ratele-de-schimb).

### Date misses and malformed source responses

- **Decision**: An empty, valid `ValCurs` is a no-rates result and triggers a search of the
  preceding dates, one day at a time, for at most 10 days. A response containing HTML or
  malformed/non-XML content is a source error, not a zero-rate dataset. An HTTP 404 with an
  empty body for an otherwise valid requested date is treated as a date miss so the configured
  fallback can proceed; a non-empty HTML error page remains a source error.
- **Rationale**: The feature distinguishes no published rate from a source failure. Direct
  checks found XML rate sets for a Sunday and a public holiday, so the application must inspect
  the actual response rather than assume that every non-business day is empty. The NBM endpoint
  returned HTTP 404 with an empty body for invalid, future, and pre-coverage requests; date
  validation prevents the invalid and future cases, while the empty-body mapping handles an
  unavailable date without treating an HTML document as valid XML.
- **Alternatives considered**: Treating every HTTP 404 as malformed source data would prevent
  date fallback when the endpoint has no document for a date. Treating every non-XML response
  as an empty date would hide genuine source errors.
- **Sources**: [NBM Sunday response](https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=22.11.2026);
  [NBM public-holiday response](https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=01.05.2026);
  [NBM invalid-date response](https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=29.02.2025).

### Tkinter and background network work

- **Decision**: Perform blocking retrieval and parsing in a daemon worker. Send plain outcomes
  through `queue.Queue`; poll with `root.after` and update widgets only on the Tkinter thread.
  Use `urllib.request.urlopen(..., timeout=10)` with a descriptive `User-Agent`.
- **Rationale**: The documented Tkinter threading model depends on the event loop for cross-thread
  calls. Keeping all widget access on the UI thread avoids that dependency. A 10-second timeout
  bounds each blocking request, but not the complete duration of a sequence of date fallbacks.
  Do not block the event loop with `join()` or a blocking queue read; use `get_nowait()` and
  handle `queue.Empty`.
- **Alternatives considered**: Fetching in the UI thread was rejected because it can freeze the
  interface. Direct worker-thread widget updates were rejected because they couple behavior to
  Tk's event loop and interpreter threading.
- **Sources**: [urllib.request](https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen);
  [Tkinter threading model](https://docs.python.org/3/library/tkinter.html#threading-model);
  [queue.Queue](https://docs.python.org/3/library/queue.html).

### XML parsing and response bounds

- **Decision**: Parse the expected XML with `xml.etree.ElementTree`; validate the root and fields
  of each entry, skip individual broken entries, and reject HTML or malformed XML as a source
  error. Bound the downloaded body to 1 MiB before parsing.
- **Rationale**: A malformed entry should not discard other valid currencies, while malformed
  top-level content cannot be trusted as a rate set. A 1 MiB ceiling is well above the observed
  feed size and avoids unbounded response reads.
- **Alternatives considered**: Treating an XML parse failure as an empty rate set was rejected
  because it would incorrectly trigger date fallback for a broken source response.
- **Sources**: [ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html);
  [Python XML security](https://docs.python.org/3/library/xml.html#xml-security).

### Decimal precision and display

- **Decision**: Parse amount and rate text directly as `decimal.Decimal`. Keep intermediate
  values unrounded; use `Decimal.quantize` with `ROUND_HALF_UP` only when displaying the amount
  to 2 decimal places and rates to 4 decimal places.
- **Rationale**: This follows the feature's monetary precision and display requirements.
  `Decimal.quantize` supports fixed-place formatting, and the rounding mode is specified
  explicitly rather than relying on the default context.
- **Alternatives considered**: Binary floating-point and intermediate rounding were rejected
  by the project constitution and the clarified specification.
- **Sources**: [decimal](https://docs.python.org/3/library/decimal.html);
  [Decimal.quantize](https://docs.python.org/3/library/decimal.html#decimal.Decimal.quantize);
  [ROUND_HALF_UP](https://docs.python.org/3/library/decimal.html#decimal.ROUND_HALF_UP).

### Persistent JSON cache

- **Decision**: Resolve `%APPDATA%` through `os.environ`, store the cache under
  `%APPDATA%\CurrencyConverterBNM`, write a temporary file in that same directory, and replace
  the destination with `os.replace`. Keep only one successful date's complete rate set and its
  UTC fetch timestamp. Treat an unreadable or corrupt cache as missing, report a short Russian
  message, and continue without cached rates.
- **Rationale**: Same-directory replacement avoids cross-filesystem replacement and prevents
  readers from seeing a partially written destination. Cache data is derived and can be
  discarded; it must not prevent a current successful conversion.
- **Alternatives considered**: Writing directly to the destination was rejected because a
  partial write could corrupt the only saved rate set. External persistence libraries were
  rejected by the standard-library-only constraint.
- **Sources**: [os.environ](https://docs.python.org/3/library/os.html#os.environ);
  [os.replace](https://docs.python.org/3/library/os.html#os.replace);
  [tempfile](https://docs.python.org/3/library/tempfile.html).

### Offline tests

- **Decision**: Test parsing with local XML fixtures and replace the rate source with fakes in
  service tests. Run tests with `python -m pytest`; tests must not make live requests.
- **Rationale**: Deterministic fixtures cover empty, valid, malformed, HTML, and partially broken
  responses without network or date dependence.
- **Alternatives considered**: Live NBM calls in unit tests were rejected because they are
  unreliable, non-repeatable, and contrary to the project constitution.
