"""Debounced layout validation coordinator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ..messages import ValidationCompleted
from ..state import LayoutStore
from .validation import ValidationService


@dataclass(frozen=True)
class ValidationSummary:
    """Lightweight snapshot of the latest validation pass."""

    is_valid: bool
    issue_count: int


class ValidationCoordinator:
    """Runs layout validation with debounce semantics."""

    def __init__(
        self,
        *,
        store: LayoutStore,
        post_message,
        debounce_ms: int = 300,
    ) -> None:
        self.store = store
        self._post_message = post_message
        self._debounce_seconds = max(debounce_ms, 0) / 1000
        self._timer_handle: asyncio.TimerHandle | None = None
        self._task: asyncio.Task[ValidationSummary] | None = None
        self._manual_issue_count = 0
        self._last_summary = ValidationSummary(is_valid=True, issue_count=0)

    @property
    def last_summary(self) -> ValidationSummary:
        return self._last_summary

    def begin_debounced_validation(self) -> None:
        loop = asyncio.get_running_loop()
        if self._timer_handle is not None:
            self._timer_handle.cancel()
        self._timer_handle = loop.call_later(self._debounce_seconds, self._schedule_validation)

    def cancel(self) -> None:
        if self._timer_handle is not None:
            self._timer_handle.cancel()
            self._timer_handle = None
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def validate_now(self) -> ValidationSummary:
        self.cancel()
        summary = await self._run_validation()
        return summary

    def publish_last_summary(self) -> None:
        """Emit the currently cached validation status."""

        self._post_message(
            ValidationCompleted(
                is_valid=self._last_summary.is_valid,
                issue_count=self._last_summary.issue_count,
            )
        )

    def record_manual_issues(self, issue_count: int) -> None:
        """Mark the layout invalid while a form has unsaved errors."""

        self._manual_issue_count = max(int(issue_count), 1)
        summary = ValidationSummary(is_valid=False, issue_count=self._manual_issue_count)
        self._publish_summary(summary)

    def clear_manual_issues(self) -> None:
        if not self._manual_issue_count:
            return
        self._manual_issue_count = 0
        self._schedule_validation()

    # ------------------------------------------------------------------
    def _schedule_validation(self) -> None:
        self._timer_handle = None
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_validation())

    async def _run_validation(self) -> ValidationSummary:
        loop = asyncio.get_running_loop()
        issues = await loop.run_in_executor(None, self._collect_issues)
        total = len(issues) + self._manual_issue_count
        summary = ValidationSummary(is_valid=total == 0, issue_count=total)
        self._publish_summary(summary)
        return summary

    def _collect_issues(self) -> list[str]:
        service = ValidationService(layer_names=self.store.layer_names)
        issues: list[str] = []
        for layer_index, record in enumerate(self.store.state.layers):
            for key_index, slot in enumerate(record.slots):
                value = str(slot.get("value", ""))
                params = slot.get("params")
                result = service.validate(value, self._normalize_params(params))
                for issue in result.issues:
                    issues.append(f"layer={layer_index} key={key_index} {issue.field}: {issue.message}")
        return issues

    def _normalize_params(self, params: Any) -> list[Any]:
        if params is None:
            return []
        if isinstance(params, (list, tuple)):
            normalized: list[Any] = []
            for item in params:
                normalized.extend(self._normalize_params(item))
            return normalized
        if isinstance(params, dict):
            value = params.get("value")
            if isinstance(value, str):
                return [value]
            name = params.get("name")
            if isinstance(name, str):
                return [{"name": name}]
            nested = params.get("params")
            if nested is not None:
                return self._normalize_params(nested)
            return [params]
        return [params]

    def _publish_summary(self, summary: ValidationSummary) -> None:
        self._last_summary = summary
        self._post_message(
            ValidationCompleted(
                is_valid=summary.is_valid,
                issue_count=summary.issue_count,
            )
        )
