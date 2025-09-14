"""Verify required environment settings for tests."""
from __future__ import annotations

import os
import sys

EXPECTED = "offscreen"


def main() -> None:
    value = os.environ.get("QT_QPA_PLATFORM")
    if value != EXPECTED:
        print(
            f"QT_QPA_PLATFORM is '{value}' but expected '{EXPECTED}'", file=sys.stderr
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
