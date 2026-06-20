"""ResponseBuilder: unified response factory.

Produces standard ``dict`` responses that match the V0.1 schema (§1).
All factory methods auto-inject ``request_id``, ``meta``, and optional
``warnings`` / ``cache`` / ``error`` fields.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from stockhub_mcp.enums import Market


class ResponseBuilder:
    """Build standardised tool-response dicts.

    Usage::

        builder = ResponseBuilder()
        resp = builder.success(data=quote.model_dump(), meta={...})
        resp = builder.error(
            error_dict={"code": "SYMBOL_NOT_FOUND", "type": "input_error", ...},
            meta={...},
        )
        resp = builder.partial_success(
            data=batch.model_dump(), warnings=[...], meta={...}
        )
    """

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def success(
        data: Any,
        meta: Optional[dict[str, Any]] = None,
        *,
        cache: Optional[dict[str, Any]] = None,
        warnings: Optional[list[dict[str, Any]]] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build a successful response.

        Args:
            data: The tool-specific data payload (dict or pydantic model).
            meta: Metadata dict.  If None, a minimal ``meta`` skeleton is used.
            cache: Optional cache-info dict (for price-class tools).
            warnings: Optional list of warning dicts.
            request_id: Optional request ID (auto-generated if omitted).

        Returns:
            Full response dict conforming to V0.1 schema.
        """
        response: dict[str, Any] = {
            "success": True,
            "data": data,
            "meta": ResponseBuilder._build_meta(meta, request_id=request_id),
        }

        if warnings:
            response["warnings"] = warnings
        if cache is not None:
            response["cache"] = cache

        return response

    @staticmethod
    def partial_success(
        data: Any,
        meta: Optional[dict[str, Any]] = None,
        *,
        warnings: Optional[list[dict[str, Any]]] = None,
        cache: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build a partial-success response (some data returned, some failed).

        Automatically sets ``partial_success = true``.
        """
        response: dict[str, Any] = {
            "success": True,
            "partial_success": True,
            "data": data,
            "meta": ResponseBuilder._build_meta(meta, request_id=request_id),
        }

        if warnings:
            response["warnings"] = warnings
        if cache is not None:
            response["cache"] = cache

        return response

    @staticmethod
    def error(
        error: dict[str, Any],
        meta: Optional[dict[str, Any]] = None,
        *,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build an error response.

        Args:
            error: Error dict with ``code``, ``type``, ``message``,
                   ``retryable``, and optional ``details``.
            meta: Optional metadata dict.
            request_id: Optional request ID.

        Returns:
            Full error response dict.
        """
        return {
            "success": False,
            "data": None,
            "meta": ResponseBuilder._build_meta(meta, request_id=request_id),
            "error": {
                "code": error.get("code", "INTERNAL_ERROR"),
                "type": error.get("type", "system_error"),
                "message": error.get("message", "An unexpected error occurred."),
                "retryable": error.get("retryable", False),
                "details": error.get("details", {}),
            },
        }

    @staticmethod
    def not_implemented(tool_name: str) -> dict[str, Any]:
        """Convenience: build a ``NOT_IMPLEMENTED`` response."""
        return ResponseBuilder.error(
            error={
                "code": "NOT_IMPLEMENTED",
                "type": "system_error",
                "message": f"Tool '{tool_name}' has not been implemented yet.",
                "retryable": False,
                "details": {},
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_meta(
        meta: Optional[dict[str, Any]] = None,
        *,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Merge caller-supplied *meta* with auto-generated fields.

        Auto-injected fields: ``request_id``, ``responded_at``.
        Missing optional fields are filled with sensible defaults.
        """
        if meta is None:
            meta = {}

        rid = request_id or meta.get("request_id") or ResponseBuilder._generate_request_id()
        now_iso = datetime.now(timezone.utc).isoformat()

        defaults: dict[str, Any] = {
            "request_id": rid,
            "market": meta.get("market", ""),
            "symbol": meta.get("symbol", ""),
            "source": meta.get("source", ""),
            "currency": meta.get("currency", ""),
            "timezone": meta.get("timezone", ""),
            "market_session": meta.get("market_session", ""),
            "is_realtime": meta.get("is_realtime", False),
            "data_delay_seconds": meta.get("data_delay_seconds", 0),
            "quality_flag": meta.get("quality_flag", ""),
            "fallback_used": meta.get("fallback_used", False),
            "responded_at": meta.get("responded_at", now_iso),
        }

        return defaults

    @staticmethod
    def _generate_request_id() -> str:
        """Generate a short unique request ID."""
        return uuid.uuid4().hex[:12]
