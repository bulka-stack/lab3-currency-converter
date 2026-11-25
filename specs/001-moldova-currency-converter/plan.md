# Implementation Plan: Moldova Currency Converter

**Branch**: `plan/001-moldova-currency-converter` | **Date**: 2026-11-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-moldova-currency-converter/spec.md`

## Summary

Build a Windows desktop currency converter around the National Bank of Moldova's dated official
rates. Fetch the specified XML source with `urllib.request`, parse usable entries into MDL-based
rates, and convert using `Decimal` with nominal quantities applied. Keep the Tkinter event loop
responsive by doing fetch and parsing work in a daemon worker and delivering results through a
queue polled with `root.after`. Search backward by calendar day for at most 10 preceding days
when a valid `ValCurs` with no `Valute` entries or an empty-body HTTP 404 is returned. Treat
every other HTTP error or network/transport failure as source unavailable and do not continue
the date search. Persist the last successful rate set in one JSON cache file using an atomic
replacement. Keep core parsing, conversion, validation, caching, and fallback behavior
independent of GUI imports; cover it with offline pytest tests and fixtures.
An identical source/target pair is an identity conversion, never requests or uses a rate set,
and shows explicit not-applicable date/source labels.

The latest planning input also refines the spec's date boundary and no-cache currency list. The
spec records an empty date field as today and accepts dates from 01.01.1994 through tomorrow.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library only: tkinter/ttk, urllib.request,
xml.etree.ElementTree, json, decimal, threading, queue, os, tempfile, and os.replace. pytest is
for development only.

**Storage**: One JSON file at `%APPDATA%\CurrencyConverterBNM\rates.json`, containing the last
successful rate set for one date, all currencies in that response, and its fetch time. Write a
temporary file in the same directory and replace the cache atomically. Treat corrupt or
unreadable cache data as missing.

**Testing**: `python -m pytest`; unit tests run offline with XML fixtures and fake rate sources.
No test contacts the real NBM service.

**Target Platform**: Windows desktop; Python 3.11 or newer with Tkinter available.

**Project Type**: Desktop GUI application.

**Performance Goals**: Each blocking network operation uses a 10-second timeout; this is not a
total-deadline guarantee for a complete response or fallback sequence. The interface remains
responsive during network work. A requested date plus up to 10 preceding dates may require
separate requests, so no total completion-time guarantee is made for that sequence.

**Constraints**: Runtime uses only the standard library. Use a `daemon=True` worker, a
thread-safe queue, and `root.after`; the worker MUST NOT access widgets and the Tkinter main
thread owns all UI updates. Use the request's `DD.MM.YYYY` date, `User-Agent`, and timeout.
Skip broken individual `Valute` entries. A valid `ValCurs` with no `Valute` entries or an
empty-body HTTP 404 means no rates for that date and triggers earlier-date search; every other
HTTP error or network/transport failure means source unavailable and stops date search. An HTML
document or other non-XML content is a source error.
Cache only successful usable responses. Amount displays use two decimals, rates four decimals,
and intermediate calculations are not rounded; use `ROUND_HALF_UP` only for display.

**Scale/Scope**: One local user and one cached rate set. Currency options are the available
published currencies plus MDL, or the specified 11-currency default when neither current nor
saved rates are available; the default list does not enable cross-currency conversion. Date
fallback checks up to 10 preceding calendar days.

## Constitution Check

| Principle or constraint | Gate | Evidence |
|---|---|---|
| Specification-first | PASS | Feature requirements and clarification are recorded before this plan; no implementation is included. |
| Resilient user experience | PASS | Network and cache failures have Russian messages and fallbacks; fetch work is off the UI thread. |
| Testable core | PASS | Parsing, conversion, validation, caching, and service logic are planned outside GUI imports with offline pytest fixtures and fakes. |
| Minimal dependencies and exact money | PASS | Runtime is standard-library-only; monetary operations use `Decimal`. |
| Transparent rate data | PASS | Rate-based results include actual date and source and disclose earlier/cache use; identity results explicitly mark rate date/source as not applicable when no rates were used. |
| Desktop GUI | PASS | The selected interface is Tkinter/ttk, not a console UI. |
| Branch and merge workflow | PASS | Planning is on `plan/001-moldova-currency-converter`, separate from the specification branch; no merge to main is performed here. |

No constitution violations require an exception.

### Post-Design Gate

**Result: PASS.** The Phase 1 design keeps all domain logic independent of Tkinter, assigns every
widget update to the UI thread, preserves offline-only core tests, uses `Decimal` without
intermediate rounding, and reports source/cache fallback dates or explicitly marks rate data as
not applicable for an identity conversion. The plan is on a distinct planning-stage branch and
does not merge to main.

## Project Structure

### Documentation (this feature)

```text
specs/001-moldova-currency-converter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── bnm-feed.md
│   └── ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # Created by /speckit-tasks
```

### Repository Documentation

```text
README.md
REPORT.md                 # Created after implementation and offline tests are verified
```

### Source Code (repository root)

```text
currency_converter/
├── __init__.py
├── models.py
├── bnm.py
├── conversion.py
├── validation.py
├── cache.py
├── service.py
└── gui.py
main.py
tests/
├── fixtures/
│   ├── valid_rates.xml
│   ├── empty_rates.xml
│   ├── partially_broken_rates.xml
│   ├── html_error.html
│   └── malformed_rates.xml
├── test_bnm.py
├── test_conversion.py
├── test_validation.py
├── test_cache.py
└── test_service.py
```

**Structure Decision**: Use the package layout requested for the feature. Keep domain models,
source handling, validation, conversion, cache, and orchestration in importable non-GUI modules;
the Tkinter view is isolated in `gui.py`, with `main.py` as the desktop entry point. Keep pytest
fixtures and tests separate from runtime modules.

## Complexity Tracking

No constitution violations or additional architectural complexity require justification.
