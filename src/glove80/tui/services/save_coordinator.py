"""Dirty tracking and atomic save helper."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Callable

from ..messages import SaveStateChanged
from ..state import LayoutStore


class SaveCoordinator:
    """Tracks dirty state and writes layouts atomically."""

    def __init__(
        self,
        *,
        store: LayoutStore,
        post_message: Callable[[SaveStateChanged], None],
    ) -> None:
        self.store = store
        self._post_message = post_message
        self._dirty = False
        self._save_task: asyncio.Task[Path] | None = None

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        if self._dirty:
            return
        self._dirty = True
        self._post_message(SaveStateChanged(is_dirty=True, save_in_progress=False, path=None, error=None))

    def mark_clean(self) -> None:
        if not self._dirty:
            return
        self._dirty = False
        self._post_message(SaveStateChanged(is_dirty=False, save_in_progress=False, path=None, error=None))

    def publish_state(self, *, path: str | Path | None = None) -> None:
        """Emit the current dirty/save status."""

        self._post_message(
            SaveStateChanged(
                is_dirty=self._dirty,
                save_in_progress=False,
                path=str(path) if path is not None else None,
                error=None,
            )
        )

    async def save_atomic(self, target_path: str | Path) -> Path:
        path = Path(target_path)
        if self._save_task is not None:
            return await self._save_task

        loop = asyncio.get_running_loop()
        self._post_message(
            SaveStateChanged(
                is_dirty=self._dirty,
                save_in_progress=True,
                path=str(path),
                error=None,
            )
        )

        async def _run() -> Path:
            payload = self.store.export_payload()
            data = json.dumps(payload, indent=2, sort_keys=True)
            tmp_path = await loop.run_in_executor(
                None,
                self._write_temp_file,
                path,
                data,
            )
            await loop.run_in_executor(None, os.replace, tmp_path, path)
            self._dirty = False
            self._post_message(
                SaveStateChanged(
                    is_dirty=False,
                    save_in_progress=False,
                    path=str(path),
                    error=None,
                )
            )
            return path

        self._save_task = asyncio.create_task(_run())
        try:
            return await self._save_task
        except Exception as exc:  # pragma: no cover - surfaced to user
            self._post_message(
                SaveStateChanged(
                    is_dirty=self._dirty,
                    save_in_progress=False,
                    path=str(path),
                    error=str(exc),
                )
            )
            raise
        finally:
            self._save_task = None

    def _write_temp_file(self, path: Path, data: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(data)
        return tmp_path
