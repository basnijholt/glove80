"""Compose QuantumTouch layouts from the canonical sources."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict

from ..metadata import get_variant_metadata

ROOT = Path(__file__).resolve().parents[3]


def _load_canonical_variant(variant: str) -> Dict:
    meta = get_variant_metadata(variant, layout="quantum_touch")
    path = ROOT / meta["output"]
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_layout(variant: str = "default") -> Dict:
    """Return the canonical QuantumTouch layout (placeholder for future code-gen)."""

    canonical = _load_canonical_variant(variant)
    return deepcopy(canonical)
