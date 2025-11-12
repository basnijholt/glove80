"""Widget exports for the Glove80 Textual TUI."""

from .footer import FooterBar
from .inspector import FeaturesTab, InspectorPanel, KeyInspector, MacroTab, HoldTapTab
from .key_canvas import KeyCanvas
from .layer_sidebar import LayerSidebar
from .rename_modal import RenameLayerModal
from .ribbon import ProjectRibbon

__all__ = [
    "FooterBar",
    "FeaturesTab",
    "InspectorPanel",
    "KeyInspector",
    "MacroTab",
    "HoldTapTab",
    "KeyCanvas",
    "LayerSidebar",
    "RenameLayerModal",
    "ProjectRibbon",
]
