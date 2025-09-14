"""Entry point for the :mod:`songsearch` package."""

from __future__ import annotations

import sys
from typing import Optional

try:  # pragma: no cover - import side effects are environment dependent
    from PyQt5.QtWidgets import QApplication  # type: ignore
    _IMPORT_ERROR: Optional[Exception] = None
except Exception as exc:  # noqa: BLE001 - we want to catch anything import might raise
    QApplication = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def main() -> None:
    """Launch the application.

    If PyQt5 (or its native dependencies such as ``libGL``) is not available,
    a friendly message is printed instead of raising an ``ImportError`` at
    import time.  This makes the module usable in headless environments and
    provides clearer feedback to the user.
    """

    if QApplication is None:  # pragma: no cover - only triggered when Qt missing
        print(
            "PyQt5 is required to run the GUI but could not be imported:\n"
            f"{_IMPORT_ERROR}",
            file=sys.stderr,
        )
        sys.exit(1)

    from .app import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
