<!--
Sync Impact Report
Version change: unversioned scaffold -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. Specification-First Development
- PRINCIPLE_2_NAME -> II. Resilient User Experience (NON-NEGOTIABLE)
- PRINCIPLE_3_NAME -> III. Testable Core
- PRINCIPLE_4_NAME -> IV. Minimal Runtime Dependencies
- PRINCIPLE_5_NAME -> V. Transparent Currency Data
Added sections: Platform and Technical Constraints; Development Workflow
Removed sections: None
Follow-up TODO: Confirm the original ratification date.
-->
# Moldova Currency Converter Constitution

## Core Principles

### I. Specification-First Development
Every change MUST follow the sequence spec -> plan -> tasks -> implementation. Specification
commits MUST precede implementation commits. This keeps implementation aligned with reviewed
requirements.

### II. Resilient User Experience (NON-NEGOTIABLE)
The desktop application MUST NOT terminate because of network errors, empty or invalid source
responses, broken cache files, or invalid user input. Each failure MUST be reported with a short
message in Russian. Network calls MUST NOT freeze the user interface.

### III. Testable Core
Parsing, conversion, validation, caching, and fallback logic MUST reside in modules that do not
import GUI code. These modules MUST have pytest unit tests that run offline with one command.
Tests MUST use fixtures and fakes and MUST NOT access the real network.

### IV. Minimal Runtime Dependencies
Runtime dependencies MUST be limited to the Python standard library. The supported runtime MUST
use Python 3.11 or newer; pytest is permitted for development and testing only. Monetary values
and calculations MUST use decimal.Decimal, never float.

### V. Transparent Currency Data
Every conversion result MUST display its rate date and data source. If the application uses a
rate from a different date or from cache, it MUST state that explicitly so users can assess the
freshness and origin of the result.

## Platform and Technical Constraints

The application MUST be a desktop GUI for currency conversion in Moldova; a console UI is not
acceptable. The GUI MUST use Tkinter/ttk. Runtime functionality MUST use only the standard
library, including tkinter, urllib, xml.etree, json, and decimal as needed.

## Development Workflow

Each stage (specification, plan, tasks, and implementation) MUST use a separate Git branch.
Changes MUST be merged to the main branch only through a Pull Request.

## Governance

This constitution governs project decisions and implementation. Amendments MUST be documented
and reviewed before implementation; project changes MUST continue to follow the
specification-first sequence above. The constitution version MUST follow semantic versioning:
MAJOR for incompatible changes to principles or governance, MINOR for new principles or
materially expanded requirements, and PATCH for clarifications that do not change requirements.

Every implementation Pull Request MUST be reviewed for compliance with this constitution and
include relevant offline test results. Non-compliant changes MUST be revised or explicitly
addressed through a constitution amendment before merge.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2026-11-25
