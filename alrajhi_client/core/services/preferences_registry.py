# -*- coding: utf-8 -*-
"""Central runtime preference registry (Phase 419).

The registry gives every UI preference a declared owner and a stable key shape.
It deliberately avoids importing PyQt at module import time so it can be used by
headless guards, CI and packaging tools.  Runtime persistence can be backed by
QSettings through ``QSettingsPreferenceBackend`` or by any compatible backend in
tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional


class PreferenceScope(str, Enum):
    SYSTEM = "system"
    COMPANY = "company"
    BRANCH = "branch"
    USER = "user"
    USER_BRANCH = "user_branch"
    WORKSTATION = "workstation"
    TABLE_LAYOUT = "table_layout"
    DOCUMENT_TYPE = "document_type"
    POS_TERMINAL = "pos_terminal"


@dataclass(frozen=True)
class PreferenceContext:
    user_id: str = "anonymous"
    branch_id: str = "global"
    profile_id: str = "1"
    workstation_id: str = "local"
    company_id: str = "default"
    table_id: str = "default"
    document_type: str = "default"
    identity: str = "default"


@dataclass(frozen=True)
class PreferenceDefinition:
    key: str
    scope: PreferenceScope
    default: Any = None
    value_type: str = "text"
    description: str = ""


class PreferenceBackend:
    def value(self, key: str, default: Any = None) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

    def set_value(self, key: str, value: Any) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def remove(self, key: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class DictPreferenceBackend(PreferenceBackend):
    """Small Qt-free backend used by tests and diagnostic tooling."""

    def __init__(self, initial: Mapping[str, Any] | None = None):
        self.data: MutableMapping[str, Any] = dict(initial or {})

    def value(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self.data[key] = value

    def remove(self, key: str) -> None:
        self.data.pop(key, None)


class QSettingsPreferenceBackend(PreferenceBackend):
    """QSettings backend loaded lazily to keep this module import-safe in CI."""

    ORG = "Alrajhi"
    APP = "Accounting"

    def __init__(self, settings: Any | None = None):
        if settings is None:
            from PyQt5.QtCore import QSettings  # pylint: disable=import-error,import-outside-toplevel
            settings = QSettings(self.ORG, self.APP)
        self.settings = settings

    def value(self, key: str, default: Any = None) -> Any:
        return self.settings.value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self.settings.setValue(key, value)
        try:
            self.settings.sync()
        except Exception:
            pass

    def remove(self, key: str) -> None:
        self.settings.remove(key)
        try:
            self.settings.sync()
        except Exception:
            pass


PREFERENCE_DEFINITIONS: Dict[str, PreferenceDefinition] = {
    # User runtime privacy/display choices.
    "dashboard/cash_balances_hidden": PreferenceDefinition(
        "dashboard/cash_balances_hidden", PreferenceScope.USER, False, "bool",
        "Hide or show dashboard cash balances for the current user.",
    ),
    "dashboard/cash_view_mode": PreferenceDefinition(
        "dashboard/cash_view_mode", PreferenceScope.USER, "today", "enum:today,general",
        "Dashboard cash movement scope selected by the current user.",
    ),
    "theme": PreferenceDefinition("theme", PreferenceScope.USER, "light", "enum:light,dark", "Selected UI theme."),
    "language": PreferenceDefinition("language", PreferenceScope.USER, "ar", "text", "Selected UI language."),

    # Company/system settings currently still persisted under legacy-compatible keys.
    "company/name": PreferenceDefinition("company/name", PreferenceScope.COMPANY, "", "text", "Company display name."),
    "company/address": PreferenceDefinition("company/address", PreferenceScope.COMPANY, "", "text", "Company address."),
    "company/phone": PreferenceDefinition("company/phone", PreferenceScope.COMPANY, "", "text", "Company phone."),
    "company/email": PreferenceDefinition("company/email", PreferenceScope.COMPANY, "", "text", "Company email."),
    "company/tax_number": PreferenceDefinition("company/tax_number", PreferenceScope.COMPANY, "", "text", "Company tax number."),
    "company/commercial_register": PreferenceDefinition("company/commercial_register", PreferenceScope.COMPANY, "", "text", "Company commercial register."),
    "company/website": PreferenceDefinition("company/website", PreferenceScope.COMPANY, "", "text", "Company website."),
    "company/logo_path": PreferenceDefinition("company/logo_path", PreferenceScope.WORKSTATION, "", "path", "Local company logo path."),
    "company/logo_data_uri": PreferenceDefinition("company/logo_data_uri", PreferenceScope.COMPANY, "", "text", "Embedded company logo data URI."),

    # Dynamic families; these are resolved by helper methods below.
    "transaction_grid/headerState": PreferenceDefinition("transaction_grid/headerState", PreferenceScope.DOCUMENT_TYPE, "", "bytes64", "Transaction grid header state."),
    "transaction_grid/visibleKeys": PreferenceDefinition("transaction_grid/visibleKeys", PreferenceScope.DOCUMENT_TYPE, "", "csv", "Transaction grid visible semantic columns."),
    "transaction_grid/activePreset": PreferenceDefinition("transaction_grid/activePreset", PreferenceScope.DOCUMENT_TYPE, "manager", "text", "Transaction grid active column preset."),
    "transaction_grid/autoResponsive": PreferenceDefinition("transaction_grid/autoResponsive", PreferenceScope.DOCUMENT_TYPE, True, "bool", "Transaction grid responsive column mode."),
    "pos/visible_columns": PreferenceDefinition("pos/visible_columns", PreferenceScope.POS_TERMINAL, "", "csv", "POS visible columns."),
    "pos/density": PreferenceDefinition("pos/density", PreferenceScope.POS_TERMINAL, "touch", "enum:compact,comfortable,touch", "POS density."),
    "pos/preset": PreferenceDefinition("pos/preset", PreferenceScope.POS_TERMINAL, "cashier", "text", "POS layout preset."),
}


def safe_segment(value: Any) -> str:
    text = str(value if value not in (None, "") else "default").strip() or "default"
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in text)


def runtime_context() -> PreferenceContext:
    """Build a best-effort context from UserSession/settings_service without hard dependency."""
    user_id = "anonymous"
    branch_id = "global"
    profile_id = "1"
    try:
        from auth.session import UserSession  # pylint: disable=import-outside-toplevel
        user_id = str(UserSession.get_current_user_id() or UserSession.get_current_username() or "anonymous")
        branch_id = str(UserSession.get_current_branch_id() or "global")
    except Exception:
        pass
    try:
        from core.services.settings_service import settings_service  # pylint: disable=import-outside-toplevel
        profile = settings_service.get_active_profile() or {}
        profile_id = str(profile.get("id") or "1")
    except Exception:
        pass
    return PreferenceContext(user_id=safe_segment(user_id), branch_id=safe_segment(branch_id), profile_id=safe_segment(profile_id))


class PreferencesRegistry:
    ROOT = "user_preferences"

    def __init__(self, backend: PreferenceBackend | None = None, definitions: Mapping[str, PreferenceDefinition] | None = None):
        self.backend = backend or DictPreferenceBackend()
        self.definitions: Dict[str, PreferenceDefinition] = dict(definitions or PREFERENCE_DEFINITIONS)

    def definition(self, key: str) -> PreferenceDefinition:
        if key in self.definitions:
            return self.definitions[key]
        return PreferenceDefinition(key=key, scope=PreferenceScope.USER, default=None, value_type="dynamic")

    def known_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self.definitions))

    def scoped_key(self, key: str, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> str:
        definition = self.definition(key)
        scope = scope or definition.scope
        context = context or runtime_context()
        raw_key = str(key).strip("/")

        # Legacy-compatible key families preserved intentionally during Phase419.
        if scope == PreferenceScope.COMPANY:
            return raw_key
        if scope == PreferenceScope.SYSTEM:
            return f"system/{raw_key}"
        if scope == PreferenceScope.USER:
            return f"{self.ROOT}/{safe_segment(context.user_id)}/{raw_key}"
        if scope == PreferenceScope.USER_BRANCH:
            return f"{self.ROOT}/{safe_segment(context.user_id)}/{safe_segment(context.branch_id)}/{raw_key}"
        if scope == PreferenceScope.BRANCH:
            return f"branches/{safe_segment(context.branch_id)}/{raw_key}"
        if scope == PreferenceScope.WORKSTATION:
            return f"workstations/{safe_segment(context.workstation_id)}/{raw_key}"
        if scope == PreferenceScope.TABLE_LAYOUT:
            return (
                f"tables/users/{safe_segment(context.user_id)}/branches/{safe_segment(context.branch_id)}"
                f"/profiles/{safe_segment(context.profile_id)}/{safe_segment(context.table_id)}/{raw_key}"
            )
        if scope == PreferenceScope.DOCUMENT_TYPE:
            return (
                f"transactions/users/{safe_segment(context.user_id)}/branches/{safe_segment(context.branch_id)}"
                f"/profiles/{safe_segment(context.profile_id)}/{safe_segment(context.document_type)}/{raw_key}"
            )
        if scope == PreferenceScope.POS_TERMINAL:
            return (
                f"pos/users/{safe_segment(context.user_id)}/branches/{safe_segment(context.branch_id)}"
                f"/profiles/{safe_segment(context.profile_id)}/{safe_segment(context.identity)}/{raw_key}"
            )
        return f"{self.ROOT}/{safe_segment(context.user_id)}/{raw_key}"

    def transaction_grid_key(self, document_type: str, name: str, *, context: PreferenceContext | None = None) -> str:
        ctx = context or runtime_context()
        ctx = PreferenceContext(
            user_id=ctx.user_id,
            branch_id=ctx.branch_id,
            profile_id=ctx.profile_id,
            workstation_id=ctx.workstation_id,
            company_id=ctx.company_id,
            table_id=ctx.table_id,
            document_type=document_type or ctx.document_type,
            identity=ctx.identity,
        )
        return self.scoped_key(str(name), context=ctx, scope=PreferenceScope.DOCUMENT_TYPE)

    def pos_key(self, identity: str, name: str, *, context: PreferenceContext | None = None) -> str:
        ctx = context or runtime_context()
        ctx = PreferenceContext(
            user_id=ctx.user_id,
            branch_id=ctx.branch_id,
            profile_id=ctx.profile_id,
            workstation_id=ctx.workstation_id,
            company_id=ctx.company_id,
            table_id=ctx.table_id,
            document_type=ctx.document_type,
            identity=identity or ctx.identity,
        )
        return self.scoped_key(str(name), context=ctx, scope=PreferenceScope.POS_TERMINAL)

    def get(self, key: str, default: Any = None, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> Any:
        definition = self.definition(key)
        effective_default = definition.default if default is None else default
        return self.backend.value(self.scoped_key(key, context=context, scope=scope), effective_default)

    def set(self, key: str, value: Any, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> None:
        self.backend.set_value(self.scoped_key(key, context=context, scope=scope), value)

    def remove(self, key: str, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> None:
        self.backend.remove(self.scoped_key(key, context=context, scope=scope))

    def get_bool(self, key: str, default: bool = False, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> bool:
        value = self.get(key, default, context=context, scope=scope)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def set_bool(self, key: str, value: bool, *, context: PreferenceContext | None = None, scope: PreferenceScope | None = None) -> None:
        self.set(key, "true" if bool(value) else "false", context=context, scope=scope)


preference_registry = PreferencesRegistry()


__all__ = [
    "DictPreferenceBackend",
    "PREFERENCE_DEFINITIONS",
    "PreferenceBackend",
    "PreferenceContext",
    "PreferenceDefinition",
    "PreferenceScope",
    "PreferencesRegistry",
    "QSettingsPreferenceBackend",
    "preference_registry",
    "runtime_context",
    "safe_segment",
]
