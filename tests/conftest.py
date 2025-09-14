import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from songsearch import config


@pytest.fixture(autouse=True)
def init_data_dir() -> None:
    """Ensure required paths are initialized for tests."""
    config.init_paths()
