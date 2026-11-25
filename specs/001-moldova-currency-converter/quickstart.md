# Quickstart: Moldova Currency Converter

## Prerequisites

- Windows with Python 3.11 or newer and Tkinter available.
- pytest installed for development validation. Runtime execution uses only the Python standard
  library.
- Network access is needed for current NBM rates; offline unit tests do not require a network.

If pytest is not installed, add it as a development tool:

```powershell
py -3.11 -m pip install pytest
```

## Validate Offline

From the repository root, run:

```powershell
py -3.11 -m pytest
```

Expected result: all unit tests pass without contacting the NBM service. Tests use local XML
fixtures and fake rate sources.

## Launch the Desktop Application

```powershell
py -3.11 main.py
```

Expected result: the desktop form opens with amount, source/target currencies, date, Convert,
and Swap controls. The date field may be left blank to use today's date.

## End-to-End Validation Scenarios

1. **Nominal and cross-rate conversion**: Use a fixture with EUR `Nominal=1`, `Value=20.0996`
   and JPY `Nominal=100`, `Value=11.5217`. Convert 3 EUR to MDL; expect 60.30 MDL, the actual
   fixture date, the NBM source, and both directional rates at four decimal places. Convert
   between EUR and JPY to verify both nominal normalization and the cross-rate.
2. **No rates for requested date**: Use an empty `ValCurs` fixture for the requested date and
   a valid fixture for a prior date within 10 days. Expect the prior set to be used and both
   requested and actual dates to be shown.
3. **Saved rates after restart**: Run once with a fake successful source, close and reopen, then
   simulate source failure. Expect a Russian prompt with the saved rate date; accept it and
   verify that the result states saved rates were used.
4. **Unavailable source and cache**: Simulate an HTML source error with no saved set. Expect a
   short Russian error for a different-currency conversion and a responsive, open window.
   Currency choices use the built-in default set; a same-currency conversion still succeeds.
5. **Validation and same currency**: Verify Convert stays disabled until required fields are
   populated; invalid amounts do not convert; same-currency conversion returns the same amount
   and unit rates. Repeat the same-currency case without network or cache and verify the result
   labels rate date/source as not applicable.
6. **Thread responsiveness**: Use a fake source that waits before returning. Confirm the
   window remains responsive while the request runs and only the main thread updates widgets.

For automated tests, every scenario above must use fixtures/fakes. A manual live-service smoke
test is optional and is not part of the test command.
