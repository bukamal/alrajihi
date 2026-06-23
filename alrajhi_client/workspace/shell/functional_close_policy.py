# -*- coding: utf-8 -*-
"""Function-aware workspace close policy (Phase 351).

Phase 350 fixed the Close button inside invoice/return tabs.  Phase 351 makes
that behavior a functional contract for every document-like workspace page:
material, transaction, return, inventory, finance, branch, user and
manufacturing screens must all delegate to the same tab lifecycle used by the
TabBar X button.

The policy stays intentionally small and PyQt-light.  Widgets can call
``request_function_workspace_close(self, "finance")`` or simply inherit
``BaseDocumentTab.request_workspace_close()``.  The helper then closes the
owning workspace tab via ``close_tab_at()`` so confirmation, neighbour
selection and fixed-dashboard fallback remain centralized.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple

from .workspace_tab_close import close_owning_workspace_tab


@dataclass(frozen=True)
class FunctionalCloseTarget:
    """Inspectable mapping used by guards and documentation."""

    function_key: str
    title: str
    expected_close_method: str = "request_workspace_close"
    workspace_lifecycle: str = "close_tab_at"


WORKSPACE_FUNCTION_CLOSE_TARGETS: Tuple[FunctionalCloseTarget, ...] = (
    FunctionalCloseTarget("transactions", "Sales/purchase invoice and return document tabs"),
    FunctionalCloseTarget("returns", "Legacy/direct return editor tabs"),
    FunctionalCloseTarget("materials", "Material and item editor tabs"),
    FunctionalCloseTarget("inventory", "Warehouse and inventory transfer document tabs"),
    FunctionalCloseTarget("finance", "Cashbox and bank account document tabs"),
    FunctionalCloseTarget("branches", "Branch document tabs"),
    FunctionalCloseTarget("users", "User document tabs"),
    FunctionalCloseTarget("manufacturing", "BOM, production order and lifecycle document tabs"),
    FunctionalCloseTarget("dialog_documents", "DialogDocumentTab-hosted legacy business documents"),
)

# Fast lookup for runtime/debugging without importing guard modules.
_FUNCTION_KEYS: Dict[str, FunctionalCloseTarget] = {target.function_key: target for target in WORKSPACE_FUNCTION_CLOSE_TARGETS}


def function_close_targets() -> Tuple[FunctionalCloseTarget, ...]:
    """Return the registered close targets for diagnostics and tests."""

    return WORKSPACE_FUNCTION_CLOSE_TARGETS


def is_workspace_function(function_key: str | None) -> bool:
    """Return whether ``function_key`` is managed by the tab lifecycle."""

    return bool(function_key in _FUNCTION_KEYS) if function_key else True


def request_function_workspace_close(widget: Any, function_key: str | None = None) -> bool:
    """Close ``widget`` through its functional workspace lifecycle.

    For all registered business-document functions this delegates to
    ``close_owning_workspace_tab``.  Standalone/modal widgets still fall back to
    their own ``close()`` through that helper, preserving legacy dialog behavior
    outside the tabbed shell.
    """

    # Unknown keys are treated conservatively as document-like if the widget is
    # already inside the tabbed workspace; the helper itself decides the fallback.
    return bool(close_owning_workspace_tab(widget))


def target_keys() -> Tuple[str, ...]:
    return tuple(target.function_key for target in WORKSPACE_FUNCTION_CLOSE_TARGETS)


__all__ = [
    "FunctionalCloseTarget",
    "WORKSPACE_FUNCTION_CLOSE_TARGETS",
    "function_close_targets",
    "is_workspace_function",
    "request_function_workspace_close",
    "target_keys",
]
