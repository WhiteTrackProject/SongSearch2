"""Tests for :func:`songsearch.musicbrainz.detect_fpcalc`."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch import detect_fpcalc


def test_detect_fpcalc_checks_executable_bit(tmp_path, monkeypatch):
    """A non-executable ``fpcalc`` on PATH should be ignored."""

    # Create a temporary directory added to PATH
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_fpcalc = bin_dir / "fpcalc"
    fake_fpcalc.write_text("echo")

    # Ensure the file exists but lacks execute permissions
    os.chmod(fake_fpcalc, 0o644)
    monkeypatch.setenv("PATH", str(bin_dir))

    # Because the file is not executable, the detector must return ``None``
    assert detect_fpcalc() is None

    # Once execute permissions are granted the path should be returned
    os.chmod(fake_fpcalc, 0o755)
    assert detect_fpcalc() == str(fake_fpcalc)

