from __future__ import annotations

import os

from core.services.settings_service import settings_service


def _env_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _bool_setting(key: str, default: bool = True) -> bool:
    value = settings_service.get(key, "true" if default else "false")
    return str(value).lower() in ("1", "true", "yes", "on")


def use_new_transaction_documents() -> bool:
    return _bool_setting("features/use_new_transaction_documents", True)


def use_new_transaction_documents_for_existing() -> bool:
    return _bool_setting("features/use_new_transaction_documents_for_existing", True)


def use_new_transaction_returns() -> bool:
    return _bool_setting("features/use_new_transaction_returns", True)


def use_new_transaction_returns_for_existing() -> bool:
    return _bool_setting("features/use_new_transaction_returns_for_existing", True)



LEGACY_TRANSACTION_DOCUMENTS_DISABLED = True


def allow_legacy_transaction_documents() -> bool:
    """Phase414 hard stop: legacy invoice/return dialogs are never routed.

    The unified TransactionDocumentTab is the only supported transaction editor.
    Environment variables and settings are intentionally ignored here to prevent
    old dialog/grid code from re-entering production navigation.
    """
    return False


def transaction_shell_unification_enabled() -> bool:
    return use_new_transaction_documents() and use_new_transaction_returns()
