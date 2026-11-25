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
3. **Given** the same currency is selected as source and target, **When** the user converts,
   **Then** the result is the entered amount, both displayed rates are 1, and no error is shown.
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
   conversion, **Then** the most recent earlier date with published rates is used and both the
   requested date and actual rate date are clearly distinguished.
2. **Given** the source cannot be reached and a previously received rate set is saved, **When**
   the user requests a conversion, **Then** a short Russian message offers those saved rates and
   their date; if the user accepts, the result identifies that saved date and that saved data was
   used.
3. **Given** the source cannot be reached and no usable rates are saved, **When** the user
   requests a conversion, **Then** a short Russian error message is shown, no conversion result
   is produced, and the application remains open.
4. **Given** valid rates have been received, **When** the application is closed and reopened,
   **Then** those rates remain available as a fallback with their original date and source.
5. **Given** the source returns empty or unusable rates and a saved usable rate set exists,
   **When** the user requests a conversion, **Then** the saved rates are offered with their date
   and are not replaced by the unusable data.
6. **Given** a request for rates is still pending, **When** the user interacts with the
   application, **Then** the application remains responsive and does not terminate.
7. **Given** saved rate data is unreadable and the source is unavailable, **When** the user
   requests a conversion, **Then** a short Russian error message appears, no conversion is
   produced, and the application remains open.

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
5. **Given** the user enters a date later than the current date, **When** the date is checked,
   **Then** a short Russian message explains that future rates are unavailable and no future
   rate is offered.

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
- A date later than the current date is entered.
- A network request is still in progress; the application remains responsive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The desktop application MUST provide a graphical form for users to enter an
  amount, choose source and target currencies, choose a rate date, and request a conversion.
- **FR-002**: The currency choices MUST include MDL and currencies with usable rates in the
  National Bank of Moldova's official exchange-rate publication.
- **FR-003**: The application MUST calculate conversions using the published nominal quantity,
  so a rate quoted for multiple units is normalized correctly for the entered amount.
  Intermediate calculations MUST NOT be rounded.
- **FR-004**: Each result MUST show the converted amount, the selected pair's rate in both
  directions, the actual date of the rates used, and the National Bank of Moldova as the source.
  The displayed amount MUST have 2 decimal places and each displayed rate MUST have 4 decimal
  places.
- **FR-005**: When the actual rate date differs from the requested date, the application MUST
  identify both dates and explain that an earlier available rate was used.
- **FR-006**: When a requested date has no published rates, the application MUST use the most
  recent earlier date with usable published rates and tell the user that it did so.
- **FR-007**: When current rates cannot be retrieved or the source returns empty or unusable
  rates, the application MUST offer the last successfully received usable rates, including their
  date and source. The user MUST be told when saved rates are used.
- **FR-008**: The last successfully received usable rate set MUST be saved locally and remain
  available after the application is closed and reopened. Empty or unusable source data MUST
  NOT replace it.
- **FR-009**: If no usable current or saved rates are available, the application MUST show a
  short error message in Russian and MUST NOT produce a conversion result.
- **FR-010**: Invalid, empty, zero, or negative amounts MUST NOT produce a conversion. The
  application MUST display a short Russian validation message for invalid amounts.
- **FR-011**: Convert MUST be disabled until the amount and both currency selections are
  non-empty. A touched amount field left empty MUST show a Russian validation message.
- **FR-012**: Selecting the same source and target currency MUST be valid and return the same
  amount with a rate of 1 in both directions.
- **FR-013**: A swap control MUST exchange the selected source and target currencies and update
  the conversion and both directional rates.
- **FR-014**: Network activity MUST NOT make the application unresponsive.
- **FR-015**: Network errors, empty or unusable source data, unreadable saved rates, and bad user
  input MUST NOT terminate the application. Each failure MUST be reported with a short message
  in Russian.
- **FR-016**: The user MUST NOT be offered a future rate date.

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
- **SC-002**: In 100% of conversion results, users can identify the source, actual rate date,
  and both directional rates, displayed to 4 decimal places.
- **SC-003**: In 100% of test cases where the requested date has no publication but an earlier
  rate exists, the earlier rate is used and its date is clearly disclosed.
- **SC-004**: In 100% of offline, invalid-input, empty-source, or damaged-saved-data test cases,
  the application remains open, shows a short Russian message, and produces no invalid result.
- **SC-005**: In 100% of cases with usable saved rates, those rates remain available after
  restart and are offered with their date when current rates are unavailable.
- **SC-006**: In 100% of tests with a pending rate request, users can interact with the
  application without it becoming unresponsive or terminating.

## Assumptions

- The rate date defaults to the current local date. Users may choose current or past dates; a
  future date is rejected with a short Russian message.
- The source is the National Bank of Moldova's official exchange-rate publication. The
  application uses only currencies with usable rates in the selected or fallback rate set.
- A blank amount is validated after the user has interacted with the field; other invalid
  non-empty amounts are validated when conversion is requested.
- A saved rate set is offered for user approval rather than applied silently.
- Positive amounts may use either a comma or a period as the decimal separator; thousands
  separators are not required.
- If no usable saved rate set exists, an unavailable source means no conversion can be made.
