"""Public entry point for the Glove80 toolkit.

Minimal, obvious surface for common tasks:
 - Discover families via :func:`list_families`.
 - Build a variant via :func:`build_layout`.
 - Apply a feature bundle via :func:`apply_feature`.
 - Grab a batteries-included example via :func:`bilateral_home_row_components`.
"""

from .features import apply_feature, bilateral_home_row_components
from .layouts.family import build_layout, list_families

__all__ = [
    "build_layout",
    "list_families",
    "apply_feature",
    "bilateral_home_row_components",
]
