"""V0.4 – Pipeline: lightweight analysis pipeline (借鉴 daily_stock_analysis).

Chains: fetch → analyze → compose, reusable across tools.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class Pipeline:
    """Minimal sequential pipeline: each stage is an async function.

    Usage::

        result = await Pipeline()
            .stage(fetch_data)
            .stage(compute_indicators)
            .stage(build_report)
            .run(input_data)
    """

    def __init__(self):
        self._stages: list[Callable[[Any], Awaitable[Any]]] = []

    def stage(self, fn: Callable[[Any], Awaitable[Any]]) -> "Pipeline":
        self._stages.append(fn)
        return self

    async def run(self, initial: Any = None) -> dict[str, Any]:
        ctx = initial
        results: dict[str, Any] = {}
        for i, fn in enumerate(self._stages):
            try:
                ctx = await fn(ctx)
                results[f"stage_{i}"] = "ok"
            except Exception as exc:
                results[f"stage_{i}"] = f"failed: {exc}"
                logger.error("Pipeline stage %d failed: %s", i, exc)
                break
        return {"success": True, "results": results, "final": ctx}
