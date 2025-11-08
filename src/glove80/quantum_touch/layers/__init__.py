"""QuantumTouch layer registry."""

from typing import Callable, Dict

from ...base import Layer, LayerMap
from .base_layer import build_base_layer
from .hrm import build_hrm_layer

LayerBuilder = Callable[[str], Layer]


LAYER_BUILDERS: Dict[str, LayerBuilder] = {
    "Base": build_base_layer,
    "HRM": build_hrm_layer,
}


def build_all_layers(variant: str) -> LayerMap:
    """Return every quantum layer currently codified."""

    return {name: builder(variant) for name, builder in LAYER_BUILDERS.items()}
