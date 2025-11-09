"""Layout family packages.

Kept intentionally minimal — no side-effect imports here. Registration of
families happens when their ``layouts`` submodules are imported explicitly
by command handlers (e.g., in ``glove80.layouts.generator``).
"""

__all__: list[str] = []
