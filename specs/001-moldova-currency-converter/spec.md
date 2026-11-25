# Feature Specification: Moldova Currency Converter

**Feature Branch**: `001-moldova-currency-converter`

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "A desktop currency converter for Moldova using the National Bank of Moldova's official exchange rates, with dated rates, conversion in both directions, input validation, offline fallback, and saved rates."

## Clarifications

### Session 2026-11-25

- Q: How should the converted amount be rounded for display? → A: Display converted amounts to
  2 decimal places, exchange rates to 4 decimal places, and do not round intermediate
  calculations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert currencies (Priority: P1)

A user enters a positive amount, chooses a source and target currency, selects a rate date, and
converts. The result gives the converted amount, the rate in both directions, the date of the
rates used, and the National Bank of Moldova as the data source.

**Why this priority**: Conversion with traceable rates is the core value of the application.

**Independent Test**: Provide a known rate set and convert between MDL and a listed currency;
verify the amount and both rates against the known values.

**Acceptance Scenarios**:

1. **Given** a positive amount and two supported currencies with available rates, **When** the
   user converts, **Then** the converted amount, both directional rates, actual rate date, and
   data source are shown.
2. **Given** a published rate quotes 100 units of a currency as 1,950 MDL, **When** the user
   converts 3 units of that currency to MDL, **Then** the result is 58.5 MDL using 19.5 MDL per
   unit.
3. **Given** the same currency is selected as source and target, including when no rate set is
   available, **When** the user converts, **Then** the result is the entered amount, both
   displayed rates are 1, and no error is shown. If no rate set was used, the result explicitly
   states that rate date and source are not applicable because no external rate was required.
4. **Given** a valid conversion result, **When** the user swaps the source and target currencies,
   **Then** the currencies and directional rates reverse and the result is recalculated.
5. **Given** a usable published rate set, **When** the user opens the currency choices, **Then**
   MDL and every currency with a usable rate are available.
6. **Given** a conversion whose exact amount and rates have more fractional digits than the
   display allows, **When** the result is shown, **Then** the amount has 2 decimal places, each
   directional rate has 4 decimal places, and intermediate calculations have not been rounded.

---

### User Story 2 - Use current or previously published rates (Priority: P1)

A user requests rates for a date and can tell whether the result uses that date's rates, an
earlier publication, or saved rates from a previous successful retrieval.

**Why this priority**: Exchange rates are date-sensitive, and users need to know the age and
origin of every result.

**Independent Test**: Use rate data for a weekday and a date with no publication, then simulate
an unavailable source with and without saved rates. Verify the selected rate date, message, and
application behavior in each case.

**Acceptance Scenarios**:

1. **Given** no rates are published for the requested date, **When** the user requests a
   conversion, **Then** the application checks earlier dates one day at a time for at most 10
   calendar days, uses the nearest date with published rates if found, and clearly distinguishes
   the requested date from the actual rate date.
2. **Given** no usable rates are published within 10 calendar days before the requested date,
   **When** the user requests a conversion, **Then** the application stops searching and shows
   a short Russian message; it may offer a saved rate set according to the offline fallback
   behavior.
3. **Given** the source cannot be reached and a previously received rate set is saved, **When**
   the user requests a conversion, **Then** a short Russian message offers those saved rates and
   their date; if the user accepts, the result identifies that saved date and that saved data was
   used.
4. **Given** the source cannot be reached and no usable rates are saved, **When** the user
   requests a different-currency conversion, **Then** a short Russian error message is shown,
   no conversion result is produced, and the application remains open.
5. **Given** valid rates have been received, **When** the application is closed and reopened,
   **Then** those rates remain available as a fallback with their original date and source.
6. **Given** no rates are found within the 10-day search window or source retrieval fails, and a
   saved usable rate set exists, **When** the user requests a conversion, **Then** the saved
   rates are offered with their date and are not replaced by unusable data.
7. **Given** a request for rates is still pending, **When** the user interacts with the
   application, **Then** the application remains responsive and does not terminate.
8. **Given** saved rate data is unreadable and the source is unavailable, **When** the user
   requests a different-currency conversion, **Then** a short Russian error message appears, no
   conversion is produced, and the application remains open.
9. **Given** neither current nor saved rates are available, **When** the user opens the currency
   choices, **Then** MDL, USD, EUR, RUB, RON, UAH, GBP, CHF, TRY, JPY, and CNY are listed, while
   the application clearly indicates that different-currency conversion requires available
   rates; same-currency identity conversion remains available.

---

### User Story 3 - Enter and correct a conversion (Priority: P2)

A user can identify missing or invalid input before relying on a conversion. The application
keeps the Convert button unavailable until an amount and both currencies are filled in.

**Why this priority**: Clear validation prevents misleading or accidental results.

**Independent Test**: Exercise empty, non-numeric, zero, and negative amounts, plus missing
currency selections; verify the button state, Russian validation message, and absence of an
invalid result.

**Acceptance Scenarios**:

1. **Given** the amount or either currency is empty, **When** the user views the form, **Then**
   Convert is disabled.
2. **Given** the user has interacted with the amount field and leaves it empty, **When** the
   field loses focus, **Then** a short Russian validation message appears and no conversion is
   produced.
3. **Given** the amount contains letters, zero, or a negative value, **When** the user attempts
   conversion, **Then** a short Russian validation message appears and no conversion is
   produced.
4. **Given** the amount is positive and both currencies are selected, **When** the user converts,
   **Then** validation permits the conversion if usable rates are available.
5. **Given** the user enters a date earlier than 01.01.1994 or later than tomorrow, **When** the
   date is checked, **Then** a short Russian validation message appears and the date is rejected.
6. **Given** the user leaves the date field empty, **When** a conversion is requested, **Then**
   the current local date is used.

---

### Edge Cases

- The requested date is a weekend or public holiday with no published rate.
- The source returns no rates, incomplete rates, or rates that cannot be used.
- The source is unavailable while a saved rate set exists, or while none exists.
- Saved rate data is damaged or cannot be read; the application remains open and reports the
  problem in a short Russian message.
- A published rate applies to a nominal quantity greater than one; conversion uses the
  per-unit value.
- The selected currencies are identical.
- A date earlier than 01.01.1994 or later than tomorrow is entered.
- No published rates are found within 10 calendar days before the requested date.
- A network request is still in progress; the application remains responsive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The desktop application MUST provide a graphical form for users to enter an
  amount, choose source and target currencies, choose a rate date, and request a conversion.
- **FR-002**: When rates are available, the currency choices MUST include MDL and currencies
  with usable rates in the National Bank of Moldova's official exchange-rate publication. When
  neither current nor saved rates are available, the choices MUST use the built-in set MDL,
  USD, EUR, RUB, RON, UAH, GBP, CHF, TRY, JPY, and CNY; users MUST still be told that conversion
  is unavailable without rates.
- **FR-003**: The application MUST calculate conversions using the published nominal quantity,
  so a rate quoted for multiple units is normalized correctly for the entered amount.
  Intermediate calculations MUST NOT be rounded.
- **FR-004**: Each result using a rate set MUST show the converted amount, the selected pair's
  rate in both directions, the actual date of the rates used, and the National Bank of Moldova
  as the source. An identity conversion without a rate set MUST explicitly state that rate date
  and source are not applicable because no external rate was required. The displayed amount MUST
  have 2 decimal places and each displayed rate MUST have 4 decimal places.
- **FR-005**: When the actual rate date differs from the requested date, the application MUST
  identify both dates and explain that an earlier available rate was used.
- **FR-006**: When a requested date has no published rates, the application MUST check earlier
  dates one calendar day at a time for up to 10 calendar days. It MUST use the nearest earlier
  date with usable published rates and tell the user that it did so; if none is found, it MUST
  stop searching and show a short Russian message.
- **FR-007**: When source retrieval fails or no usable rates are found within the 10-day search
  window, the application MUST offer the last successfully received usable rates, including
  their date and source. The user MUST be told when saved rates are used. A valid empty rate set
  MUST trigger earlier-date searching before saved rates are offered.
- **FR-008**: The last successfully received usable rate set MUST be saved locally and remain
  available after the application is closed and reopened. Empty or unusable source data MUST
  NOT replace it.
- **FR-009**: If no usable current or saved rates are available, the application MUST show a
  short error message in Russian and MUST NOT produce a conversion result for currency pairs
  that require an exchange rate. An identity conversion does not require rate data.
- **FR-010**: Invalid, empty, zero, or negative amounts MUST NOT produce a conversion. The
  application MUST display a short Russian validation message for invalid amounts.
- **FR-011**: Convert MUST be disabled until the amount and both currency selections are
  non-empty. A touched amount field left empty MUST show a Russian validation message.
- **FR-012**: Selecting the same source and target currency MUST be valid even when no rate set
  is available, and MUST return the same amount with a rate of 1 in both directions.
- **FR-013**: A swap control MUST exchange the selected source and target currencies and update
  the conversion and both directional rates.
- **FR-014**: Network activity MUST NOT make the application unresponsive.
- **FR-015**: Network errors, empty or unusable source data, unreadable saved rates, and bad user
  input MUST NOT terminate the application. Each failure MUST be reported with a short message
  in Russian.
- **FR-016**: The rate date field MUST accept dates from 01.01.1994 through tomorrow in
  DD.MM.YYYY format. An empty field MUST mean today's local date. Dates outside that range MUST
  be rejected with a short Russian validation message.

### Key Entities

- **Conversion request**: The user's amount, source currency, target currency, and requested
  rate date.
- **Published rate set**: A dated set of rates from the National Bank of Moldova, including each
  currency's nominal quantity and quoted value relative to MDL.
- **Conversion result**: The converted amount, both directional rates, actual rate date, source,
  and whether earlier or saved rates were used.
- **Saved rate set**: The last successfully received usable published rate set, saved locally
  and retained for fallback after an application restart.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of valid conversion test cases, the displayed result agrees with the
  expected value rounded to 2 decimal places for the selected currencies and published rates,
  including rates quoted per nominal quantities.
- **SC-002**: In 100% of rate-based conversion results, users can identify the source, actual
  rate date, and both directional rates, displayed to 4 decimal places.
- **SC-003**: In 100% of test cases where the requested date has no publication but an earlier
  rate exists within the 10-day search window, the earlier rate is used and its date is clearly
  disclosed.
- **SC-004**: In 100% of offline, invalid-input, empty-source, or damaged-saved-data test cases,
  the application remains open, shows a short Russian message, and produces no invalid result.
- **SC-005**: In 100% of cases with usable saved rates, those rates remain available after
  restart and are offered with their date when current rates are unavailable.
- **SC-006**: In 100% of tests with a pending rate request, users can interact with the
  application without it becoming unresponsive or terminating.
- **SC-007**: In 100% of no-rates test cases, the search stops after the requested date and at
  most 10 preceding calendar dates; no different-currency conversion is produced unless the
  user approves a saved rate set.
- **SC-008**: In 100% of date-input tests, an empty value resolves to today's local date, dates
  from 01.01.1994 through tomorrow are accepted, and dates outside that range are rejected with
  a short Russian message.
- **SC-009**: In 100% of tests with neither current nor saved rates, the 11 specified default
  currencies are available and the user is told that different-currency conversion is
  unavailable; same-currency identity conversion remains available.
- **SC-010**: In 100% of same-currency test cases without a usable rate set, the entered amount
  is returned, both rates are 1, and the result identifies that no external rate date or source
  was required.

## Assumptions

- The rate date is entered as DD.MM.YYYY. An empty field means today's local date; allowed
  dates run from 01.01.1994 through tomorrow. If tomorrow has no published rates, normal
  earlier-date fallback applies.
- The source is the National Bank of Moldova's official exchange-rate publication. The
  application uses only currencies with usable rates in the selected or fallback rate set.
- A blank amount is validated after the user has interacted with the field; other invalid
  non-empty amounts are validated when conversion is requested.
- A saved rate set is offered for user approval rather than applied silently.
- Positive amounts may use either a comma or a period as the decimal separator; thousands
  separators are not required.
- If no usable saved rate set exists, an unavailable source means no conversion can be made.
