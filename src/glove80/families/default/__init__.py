"""MoErgo default Glove80 layouts.

Importing this package ensures the family registers itself via
``glove80.families.default.layouts``.
"""

from . import layouts

# Export the module to make the import a public API symbol.
__all__ = ["layouts"]
