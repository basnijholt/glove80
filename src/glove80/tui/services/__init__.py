"""Service-layer helpers for the Glove80 TUI."""

from .builder_bridge import BuilderBridge, FeatureDiff
from .validation import (
    AutocompleteSuggestions,
    ValidationIssue,
    ValidationResult,
    ValidationService,
)

__all__ = [
    "BuilderBridge",
    "FeatureDiff",
    "AutocompleteSuggestions",
    "ValidationIssue",
    "ValidationResult",
    "ValidationService",
]
