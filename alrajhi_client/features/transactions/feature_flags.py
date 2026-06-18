from __future__ import annotations

from core.services.settings_service import settings_service


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
