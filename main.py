"""Desktop entry point for the Moldova currency converter application."""

from __future__ import annotations

from currency_converter.gui import run_app


def main() -> None:
    """Launch the desktop application."""
    run_app()


if __name__ == "__main__":
    main()
