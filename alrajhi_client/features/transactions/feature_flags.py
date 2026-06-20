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



def allow_legacy_transaction_documents() -> bool:
    """Emergency compatibility switch for old invoice/return dialogs.

    The unified TransactionDocumentTab is the official route.  Legacy dialogs
    may be enabled only for rollback diagnostics via the settings key below or
    the environment variable, which is useful before settings are reachable in a
    broken client/server install.
    """
    env = os.environ.get("ALRAJHI_ALLOW_LEGACY_TRANSACTION_DOCUMENTS")
    if env is not None:
        return _env_bool(env, False)
    return _bool_setting("features/allow_legacy_transaction_documents", False)


def transaction_shell_unification_enabled() -> bool:
    return use_new_transaction_documents() and use_new_transaction_returns()
