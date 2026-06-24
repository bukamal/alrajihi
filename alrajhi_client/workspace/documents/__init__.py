# -*- coding: utf-8 -*-
"""Document workspace public API.

Contract-only tools import this package in CI and build scripts where PyQt5 may
not be installed.  Keep the Qt tab classes optional so data-only audits can run
without importing PyQt widgets.
"""
from __future__ import annotations

try:  # pragma: no cover - exercised only when PyQt5 is available
    from .base_document_tab import BaseDocumentTab, DocumentState
except Exception:  # PyQt5 can be absent in static/audit environments
    BaseDocumentTab = None  # type: ignore
    DocumentState = None  # type: ignore

from .document_contract import (
    DocumentCapabilities,
    DocumentContractError,
    DocumentDescriptor,
    DocumentPermissions,
    all_descriptors,
    contract_matrix,
    descriptor_for,
    validate_all_descriptors,
    validate_descriptor,
)

try:  # pragma: no cover - permission binder may import Qt-adjacent modules indirectly
    from .document_permission_binder import (
        DOCUMENT_ACTIONS,
        DocumentPermissionBinder,
        DocumentPermissionDecision,
        document_permission_allowed,
    )
except Exception:
    DOCUMENT_ACTIONS = tuple()  # type: ignore
    DocumentPermissionBinder = None  # type: ignore
    DocumentPermissionDecision = None  # type: ignore
    document_permission_allowed = None  # type: ignore

__all__ = [
    "BaseDocumentTab",
    "DocumentState",
    "DocumentCapabilities",
    "DocumentContractError",
    "DocumentDescriptor",
    "DocumentPermissions",
    "all_descriptors",
    "contract_matrix",
    "descriptor_for",
    "validate_all_descriptors",
    "validate_descriptor",
    "DOCUMENT_ACTIONS",
    "DocumentPermissionBinder",
    "DocumentPermissionDecision",
    "document_permission_allowed",
    "KIND_CARD_FORM",
    "KIND_FINANCIAL_DOCUMENT",
    "KIND_TABULAR_DOCUMENT",
    "apply_document_layout_policy",
    "infer_document_layout_kind",
]

try:  # pragma: no cover - layout policy imports Qt sizing classes
    from .document_layout_policy import (
        KIND_CARD_FORM,
        KIND_FINANCIAL_DOCUMENT,
        KIND_TABULAR_DOCUMENT,
        apply_document_layout_policy,
        infer_document_layout_kind,
    )
except Exception:
    KIND_CARD_FORM = "card_form"  # type: ignore
    KIND_FINANCIAL_DOCUMENT = "financial_document"  # type: ignore
    KIND_TABULAR_DOCUMENT = "tabular_document"  # type: ignore
    apply_document_layout_policy = None  # type: ignore
    infer_document_layout_kind = None  # type: ignore
