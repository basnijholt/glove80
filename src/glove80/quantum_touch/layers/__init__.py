"""QuantumTouch layer registry."""

from typing import Callable, Dict

from ...base import Layer, LayerMap
from .base_layer import build_base_layer
from .hrm import build_hrm_layer
from .left_index_layer import build_left_index_layer
from .left_middle_layer import build_left_middle_layer
from .left_ring_layer import build_left_ring_layer
from .lower_layer import build_lower_layer
from .magic_layer import build_magic_layer
from .mouse_fast_layer import build_mouse_fast_layer
from .mouse_layer import build_mouse_layer
from .mouse_slow_layer import build_mouse_slow_layer
from .mouse_warp_layer import build_mouse_warp_layer
from .original_layer import build_original_layer

LayerBuilder = Callable[[str], Layer]


LAYER_BUILDERS: Dict[str, LayerBuilder] = {
    "Base": build_base_layer,
    "HRM": build_hrm_layer,
    "Lower": build_lower_layer,
    "Mouse": build_mouse_layer,
    "MouseFast": build_mouse_fast_layer,
    "MouseSlow": build_mouse_slow_layer,
    "MouseWarp": build_mouse_warp_layer,
    "Magic": build_magic_layer,
    "LeftIndex": build_left_index_layer,
    "LeftMiddle": build_left_middle_layer,
    "LeftRing": build_left_ring_layer,
    "Original": build_original_layer,
}


def build_all_layers(variant: str) -> LayerMap:
    """Return every quantum layer currently codified."""

    return {name: builder(variant) for name, builder in LAYER_BUILDERS.items()}
