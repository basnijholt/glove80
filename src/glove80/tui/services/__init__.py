"""Service-layer helpers for the Glove80 TUI."""

from .builder_bridge import BuilderBridge, FeatureDiff, FeatureInfo
from .command_registry import Command, CommandRegistry
from .save_coordinator import SaveCoordinator
from .validation_coordinator import ValidationCoordinator, ValidationSummary
from .validation import (
    AutocompleteSuggestions,
    ValidationIssue,
    ValidationResult,
    ValidationService,
)

__all__ = [
    "BuilderBridge",
    "FeatureDiff",
    "FeatureInfo",
    "Command",
    "CommandRegistry",
    "SaveCoordinator",
    "ValidationCoordinator",
    "ValidationSummary",
    "AutocompleteSuggestions",
    "ValidationIssue",
    "ValidationResult",
    "ValidationService",
]
