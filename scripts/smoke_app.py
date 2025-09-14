"""Smoke test for launching the GUI."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch import __main__ as main_module


def main() -> None:
    if main_module.QApplication is None:
        print("PyQt5 not available; skipping GUI smoke test")
        return

    main_module.QApplication([])
    from songsearch.app import MainWindow

    MainWindow()
    print("GUI instantiated successfully")


if __name__ == "__main__":
    main()
