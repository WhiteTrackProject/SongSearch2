"""Utilities for organizing files.

Currently exposes :func:`build_destination` which builds the output path
for a song based on its metadata.
"""

from .destination import build_destination

__all__ = ["build_destination"]
