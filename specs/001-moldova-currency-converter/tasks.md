---
description: "Implementation tasks for Moldova Currency Converter"
---

# Tasks: Moldova Currency Converter

**Input**: Design documents from `specs/001-moldova-currency-converter/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and
`quickstart.md`

**Test policy**: All unit-test code and XML fixtures are deferred to the final phase and a
separate test branch, as requested. GUI acceptance checks are manual tasks in that final phase;
no unit-test task appears in a user-story phase.

**Code gate**: T001 must be complete before any task writes application or test code. It verifies
that the feature specification and design documents have been merged to `main` through a Pull
Request.

**Organization**: Tasks are grouped by user story and ordered by priority. User Story 1 and
User Story 2 are P1; User Story 3 is P2.

## Format

Every task follows `- [ ] T### [P?] [Story?] Description with exact file path`.

- **[P]** means the task can run in parallel with other tasks because it changes separate files
  and has no dependency on unfinished work.
- **[Story]** maps a task to its user story: `[US1]`, `[US2]`, or `[US3]`.
- All code tasks are blocked by the T001 specification-merge gate.

## Path Conventions

- Runtime package: `currency_converter/` at the repository root.
- Desktop entry point: `main.py` at the repository root.
- Offline tests and XML fixtures: `tests/` at the repository root.
- Feature documentation: `specs/001-moldova-currency-converter/`.

## Phase 1: Setup

**Purpose**: Require approved specifications before code work and establish the implementation
branch and package skeleton.

- [x] T001 Verify that `specs/001-moldova-currency-converter/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md` are merged to `main` through a Pull Request; do not start source or test code before this gate.
- [x] T002 After T001, create the implementation-stage branch `implementation/001-moldova-currency-converter` from the updated `main` before editing `currency_converter/__init__.py` or `main.py`.
- [x] T003 After T002, create the application package marker in `currency_converter/__init__.py` and the desktop entry point in `main.py` using only the Python standard library.

---

## Phase 2: Foundational

**Purpose**: Define shared domain records required by the source, conversion, cache, service,
and GUI layers.

**Blocking**: Complete this phase before starting any user-story implementation.

- [x] T004 Define the shared records in `currency_converter/models.py`: a quote has a unique alphabetic `code`, text `numeric_code` preserving leading zeroes, source `name`, and positive `Decimal` `nominal` and `value_mdl`; a rate set contains one actual date and its usable quotes; a request amount is a positive `Decimal`; and a conversion result may have no rate set for the no-rate identity case.

**Checkpoint**: Shared data shapes and constraints are ready; user-story code can begin.

---

## Phase 3: User Story 1 - Convert currencies (Priority: P1) - MVP

**Goal**: Convert between MDL and NBM currencies with nominal-aware cross rates, bidirectional
rates, date/source transparency, swap, and same-currency identity behavior.

**Independent Test**: With a known NBM quote set, convert between two different currencies and
verify amount, both directions, actual rate date, and source. Also verify a same-currency
conversion returns the entered amount and unit rates, shows the required not-applicable labels
when no rate set is used, and that Swap recalculates both directions from the same rate set.

### Implementation for User Story 1

- [x] T005 [P] [US1] Implement the NBM request and XML parser in `currency_converter/bnm.py` for `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`, with a descriptive `User-Agent` and 10-second timeout; parse `ValCurs`/`Valute`, preserve `NumCode` as text, skip broken entries, treat a valid `ValCurs` with no `Valute` entries and empty-body HTTP 404 as date misses, and classify any other HTTP error, network/transport error, HTML/malformed XML, or a response with entries but no usable quotes as source errors.
- [x] T006 [P] [US1] Implement MDL-normalized conversion and display formatting in `currency_converter/conversion.py`: normalize `Value / Nominal`, calculate cross rates through MDL, preserve full intermediate precision, display amounts to 2 decimals and rates to 4 using `ROUND_HALF_UP`, and return amount unchanged with rates of 1 for an identity pair.
- [x] T007 [US1] Implement the requested-date rate service in `currency_converter/service.py`, combining `currency_converter/bnm.py` and `currency_converter/conversion.py`; return typed success/failure outcomes and bypass rate retrieval and rate-set association for every identity conversion.
- [x] T008 [P] [US1] Build the main form and result area in `currency_converter/gui.py` with amount, source/target currencies, `DD.MM.YYYY` rate date, Convert, Swap, converted amount, both rates, actual rate date, and NBM source; keep Convert disabled until amount and both currency selections are non-empty. For every identity result, show `Дата курса: не применимо` and `Источник: внешний курс не запрашивался`; make Swap exchange currencies, preserve amount/date, and recalculate result and both rates from the same rate set.
- [x] T009 [US1] Connect `currency_converter/gui.py` to `currency_converter/service.py` and start the application from `main.py` using `threading.Thread(daemon=True)`, `queue.Queue`, and `root.after`; keep all widget access on the Tk thread, disable request-changing controls while busy, keep the window responsive, and show source failures in short Russian messages.

**Checkpoint**: The GUI can convert a valid currency pair, swap directions, and complete an
identity conversion without requiring rate data.

---

## Phase 4: User Story 2 - Use current or previously published rates (Priority: P1)

**Goal**: Search for the latest available dated rates within the ten-day limit, persist one
successful rate set, and offer it transparently when current rates are unavailable.

**Independent Test**: Simulate an empty valid response, empty-body 404, another HTTP error, a
prior-date success, a valid saved set, and no saved set. Verify date-search behavior, prompt and
approval, Russian messages, cache persistence, and default currency list without live network
access.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Implement JSON cache load/save in `currency_converter/cache.py` at `%APPDATA%\CurrencyConverterBNM\rates.json`, storing only one successful date's complete usable rate set and UTC fetch time; write a same-directory temporary file and replace with `os.replace`, treat corrupt data as missing, and never replace good cache data with empty or unusable rates.
- [ ] T011 [US2] Extend `currency_converter/service.py` to try the requested date, then each preceding date one day at a time for at most 10 preceding days; a valid `ValCurs` with no `Valute` entries and empty-body HTTP 404 are date misses, while any other HTTP or network/transport error stops date searching as source unavailable. Update cache only for usable results and offer saved rates after source failure or exhausted search.
- [ ] T012 [US2] Add fallback states to `currency_converter/gui.py`: ask before using saved rates and show their rate date/source, distinguish requested and actual dates, label cached/earlier rates, display short Russian failure messages, and show MDL, USD, EUR, RUB, RON, UAH, GBP, CHF, TRY, JPY, and CNY when neither current nor saved rates are available.

**Checkpoint**: Date fallback stops at the specified limit; approved cache use is explicit and
persists across restarts; absent rates never crash the application.

---

## Phase 5: User Story 3 - Enter and correct a conversion (Priority: P2)

**Goal**: Reject invalid amount/date input clearly and keep conversion actions aligned with form
state.

**Independent Test**: Try blank, alphabetic, zero, and negative amounts; empty, malformed,
pre-1994, and later-than-tomorrow dates; and valid boundaries. Verify the button state, Russian
messages, today's-date default, and absence of invalid conversions.

### Implementation for User Story 3

- [ ] T013 [P] [US3] Implement pure input parsing and validation in `currency_converter/validation.py`: amount must be a positive `Decimal`, accept comma or period as the decimal separator, reject thousands separators, parse dates as `DD.MM.YYYY`, map blank date to local today, and accept only 01.01.1994 through tomorrow.
- [ ] T014 [US3] Integrate `currency_converter/validation.py` with `currency_converter/gui.py` so touched-empty, non-numeric, zero, negative, malformed, too-early, and too-late inputs show short Russian messages, invalid requests produce no result, and valid form state enables Convert.

**Checkpoint**: All three stories are implemented; valid requests work and invalid input cannot
produce a conversion.

---

## Phase 6: Final Phase - Offline Tests, GUI Acceptance, and Documentation

**Purpose**: Add every unit test only after application code is merged, on a distinct test
branch based on the merged implementation. Run GUI acceptance checks and document usage without
writing application code.

- [ ] T015 After T003-T014, merge the implementation branch through a Pull Request and verify `currency_converter/` and `main.py` are present on `main` before creating the test branch.
- [ ] T016 After T015, create the separate test-stage branch `test/001-moldova-currency-converter` from the updated `main` for all unit-test files under `tests/`.
- [ ] T017 Create offline response fixtures in `tests/fixtures/valid_rates.xml`, `empty_rates.xml`, `partially_broken_rates.xml`, `malformed_rates.xml`, and `html_error.html`; represent an empty-body 404 with a fake response rather than a live request.
- [ ] T018 [P] [US1] Add parser tests in `tests/test_bnm.py` using `tests/fixtures/valid_rates.xml`, `partially_broken_rates.xml`, and `malformed_rates.xml`; verify nominal/text fields, leading-zero numeric codes, valid sibling retention, skipped invalid entries, and that malformed XML and a response with no usable quotes are source errors rather than date misses.
- [ ] T019 [P] [US1] Add conversion tests in `tests/test_conversion.py` for MDL and foreign-currency directions, nominal-aware cross rates, identity conversion with and without a rate set, exact intermediate precision, 2-place amount display, and 4-place rate display with `ROUND_HALF_UP`.
- [ ] T020 [P] [US2] Add cache tests in `tests/test_cache.py` for one-date/all-currency JSON round-trip, fetch timestamp, atomic replacement, corrupt-cache-as-missing behavior, and preservation of the prior cache after empty or unusable input.
- [ ] T021 [P] [US2] Add service tests in `tests/test_service.py` with fake sources for empty-`ValCurs` and empty-body-404 date fallback, nearest usable date, the 10-day stop, non-empty 404 and other HTTP errors stopping date search as source unavailable, `tests/fixtures/html_error.html` and network errors, explicit cache approval, no-cache default currencies, and no real network access.
- [ ] T022 [P] [US3] Add validation tests in `tests/test_validation.py` for positive amount parsing, comma/period decimal separators, rejected thousands separators, empty/letters/zero/negative values, empty date as today, `DD.MM.YYYY`, the 01.01.1994 lower bound, tomorrow upper bound, and out-of-range dates.
- [ ] T023 Run `python -m pytest` from the repository root against `tests/`; confirm every unit test passes offline and no test accesses the real NBM service.
- [ ] T024 [US1] Perform GUI acceptance on `main.py`/`currency_converter/gui.py`: verify Swap exchanges currencies and recalculates the result and both rates from the same rate set, and verify an identity conversion shows the exact not-applicable labels and neither requests nor uses rates.
- [ ] T025 [US2] Perform GUI acceptance on `main.py`/`currency_converter/gui.py`: with network unavailable and no usable cache, then with a corrupt cache, verify short Russian messages, no different-currency result, and that the application remains open; with a valid saved set, verify the user is asked before use and its date/source are shown; interact with the window during a pending request and verify it remains responsive.
- [ ] T026 [US3] Perform GUI acceptance on `main.py`/`currency_converter/gui.py`: verify empty/invalid amounts and out-of-range dates show short Russian messages, invalid requests produce no result, and Convert remains disabled until required fields are filled.
- [ ] T027 Create/update `README.md` with Python 3.11+/Tkinter prerequisites, setup instructions (no runtime package install; install development-only pytest with `python -m pip install pytest`), the application launch command `python main.py`, and the one-command offline test run `python -m pytest`.
- [ ] T028 After T023-T027 pass, open and merge a Pull Request for the test branch containing `tests/` and `README.md` through the repository's required PR workflow.
- [ ] T029 After T028, create a documentation-stage branch `report/001-moldova-currency-converter` from updated `main`, write `REPORT.md` with verified feature behavior, setup/run instructions, and actual test results, then merge it through a Pull Request.

**Final Checkpoint**: Runtime, offline unit tests, README instructions, and the final report are
merged through their designated Pull Requests; the application and test command are documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: T001 is a documentation-merge gate and writes no code. T002 and T003
  depend on T001; no source or test code may be written before the gate passes.
- **Phase 2 (Foundational)**: T004 depends on T003 and blocks all user-story implementation.
- **Phase 3 (US1)**: Depends on T004. T005, T006, and T008 can run in parallel; T007 depends
  on T005 and T006; T009 depends on T007 and T008.
- **Phase 4 (US2)**: Depends on US1's rate service and GUI. T010 provides the cache used by
  T011; T012 integrates the service fallback with the UI.
- **Phase 5 (US3)**: T013 depends on T004 and can run alongside independent US2 files; T014
  depends on T013 and the US1/US2 GUI.
- **Phase 6 (Final test and documentation branches)**: T015 requires all implementation tasks
  complete and merged through a PR; T016 requires T015; T017 requires T016; T018-T022 require
  fixtures and the merged implementation; T023 requires all unit-test tasks; T024-T026 require
  T023 and the merged GUI; T027 requires verified launch/test commands; T028 requires T023-T027;
  T029 requires T028.

### User Story Dependencies

- **US1 (P1)**: Starts after the foundation; no dependency on another user story. Its GUI
  acceptance check is in the final phase after tests are available.
- **US2 (P1)**: Follows US1 because fallback, caching, and prompts extend its rate service and
  result UI.
- **US3 (P2)**: GUI validation integrates after US1/US2; the pure `validation.py` task can be
  parallelized with independent US2 tasks after the foundation.
- **Offline unit tests**: All three stories' unit tests are deferred to the final phase and
  separate test branch, after implementation is merged. GUI acceptance checks in that phase are
  manual and do not add unit-test files to earlier branches.

### Parallel Opportunities

- **US1**: T005 (`bnm.py`), T006 (`conversion.py`), and T008 (`gui.py`) can proceed in parallel
  after T004 because they edit different files.
- **US2**: T010 (`cache.py`) must finish before T011 integrates cache use into `service.py`;
  T012 then integrates the completed service with `gui.py`.
- **US3**: T013 (`validation.py`) can run in parallel with T010 or T011; T014 must wait for
  T012 because both integrate into `gui.py`.
- **Final test phase**: After T017, T018-T022 can run in parallel because each owns a distinct
  test module.

---

## Parallel Examples

### User Story 1

```text
After T004, run in parallel:
Task: T005 - Implement NBM request/parser in currency_converter/bnm.py
Task: T006 - Implement conversion math/formatting in currency_converter/conversion.py
Task: T008 - Build the form/result view in currency_converter/gui.py
Then run T007, followed by T009.
```

### User Story 2

```text
After US1:
Task: T010 - Implement the independent cache module in currency_converter/cache.py
Then run T011 (service fallback) and T012 (GUI cache/fallback flow) in dependency order.
```

### User Story 3

```text
After T004, T013 in currency_converter/validation.py may run alongside US2's independent
cache/service work. Run T014 in currency_converter/gui.py after T012 and T013.
```

### Final Unit-Test Phase

```text
After T017 creates tests/fixtures/:
Task: T018 - tests/test_bnm.py (including malformed XML classification)
Task: T019 - tests/test_conversion.py
Task: T020 - tests/test_cache.py
Task: T021 - tests/test_service.py (including empty-body 404 vs other HTTP errors)
Task: T022 - tests/test_validation.py
Run T023 only after all five test modules are complete; then complete T024-T029.
```

---

## Implementation Strategy

### MVP First

1. Complete T001-T004; no application code begins until the specification/design PR is merged.
2. Complete US1 (T005-T009) for a visible, useful conversion increment with safe Russian error
   handling and an offline identity-conversion path.
3. Use the US1 independent acceptance criteria for an MVP demonstration only; do not release
   the full feature before US2/US3 and the final offline test branch are complete.

### Incremental Delivery

1. Merge the reviewed specification and design artifacts through a PR.
2. Implement and integrate US1 on the implementation branch.
3. Add US2 cache, fallback, and source-transparency flows.
4. Add US3 validation and date-bound behavior.
5. Merge the implementation branch through a PR.
6. Create the separate test branch from updated `main`, add all unit tests and fixtures, run
   `python -m pytest`, complete GUI acceptance, document setup and execution in `README.md`,
   and merge that branch through a PR.
7. Write verified results in `REPORT.md` on its separate documentation-stage branch after the
   test branch has merged.

### Test Ordering Exception

Unit tests are intentionally not test-first and are not written during the story phases. The
user explicitly requires all unit tests to be authored in a separate final branch; the
constitution requires offline pytest coverage before final delivery, so that final test branch
is a release prerequisite.

## Notes

- `[P]` tasks edit separate files and have no unfinished prerequisite.
- Every implementation task depends on the T001 spec/design merge gate, directly or through
  earlier setup/foundation tasks.
- All unit-test modules and XML fixtures appear only in the final, separate test-branch phase.
- GUI acceptance checks are manual and do not create unit-test code before the final test phase.
- No console UI or third-party runtime dependency is planned.
