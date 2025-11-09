"""Public entry point for the Glove80 toolkit.

Keep this surface minimal to avoid exposing internals inadvertently.
"""

from .layouts.family import build_layout

__all__ = ["build_layout"]
