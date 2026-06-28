# -*- coding: utf-8 -*-
"""Persistent per-user UI preferences.

Phase 419 routes user-facing UI preferences through the central preferences
registry.  The key shapes remain compatible with Phase 413 so existing saved
choices are not lost, while new surfaces can declare their scope explicitly.
"""
from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QSettings

from core.services.preferences_registry import (
    PreferenceContext,
    PreferenceScope,
    PreferencesRegistry,
    QSettingsPreferenceBackend,
    safe_segment,
)

try:  # Imported lazily in tests/headless tooling as well as runtime.
    from auth.session import UserSession
except Exception:  # pragma: no cover - defensive import fallback
    UserSession = None  # type: ignore


class UserPreferencesService:
    ORG = "Alrajhi"
    APP = "Accounting"
    ROOT = "user_preferences"
    DASHBOARD_CASH_HIDDEN = "dashboard/cash_balances_hidden"
    DASHBOARD_CASH_VIEW_MODE = "dashboard/cash_view_mode"

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings(self.ORG, self.APP)
        self._registry = PreferencesRegistry(QSettingsPreferenceBackend(self._settings))

    def _current_user_key(self) -> str:
        uid = None
        try:
            if UserSession is not None:
                uid = UserSession.get_current_user_id() or UserSession.get_current_username()
        except Exception:
            uid = None
        return self._safe_segment(str(uid or "anonymous"))

    def _current_branch_key(self) -> str:
        branch_id = None
        try:
            if UserSession is not None:
                branch_id = UserSession.get_current_branch_id()
        except Exception:
            branch_id = None
        return self._safe_segment(str(branch_id if branch_id not in (None, "") else "global"))

    @staticmethod
    def _safe_segment(value: str) -> str:
        return safe_segment(value)

    def _context(self) -> PreferenceContext:
        return PreferenceContext(user_id=self._current_user_key(), branch_id=self._current_branch_key())

    def key(self, preference_key: str, *, branch_scoped: bool = False) -> str:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        return self._registry.scoped_key(preference_key, context=self._context(), scope=scope)

    def get(self, preference_key: str, default: Any = None, *, branch_scoped: bool = False) -> Any:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        return self._registry.get(preference_key, default, context=self._context(), scope=scope)

    def set(self, preference_key: str, value: Any, *, branch_scoped: bool = False) -> None:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        self._registry.set(preference_key, value, context=self._context(), scope=scope)
        # Keep Phase413 immediate-sync contract visible and explicit.
        self._settings.sync()

    def remove(self, preference_key: str, *, branch_scoped: bool = False) -> None:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        self._registry.remove(preference_key, context=self._context(), scope=scope)

    def get_bool(self, preference_key: str, default: bool = False, *, branch_scoped: bool = False) -> bool:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        return self._registry.get_bool(preference_key, default, context=self._context(), scope=scope)

    def set_bool(self, preference_key: str, value: bool, *, branch_scoped: bool = False) -> None:
        scope = PreferenceScope.USER_BRANCH if branch_scoped else PreferenceScope.USER
        self._registry.set_bool(preference_key, value, context=self._context(), scope=scope)

    def get_text(self, preference_key: str, default: str = "", *, branch_scoped: bool = False) -> str:
        value = self.get(preference_key, default, branch_scoped=branch_scoped)
        return str(value if value is not None else default)

    def set_text(self, preference_key: str, value: str, *, branch_scoped: bool = False) -> None:
        self.set(preference_key, str(value or ""), branch_scoped=branch_scoped)

    def dashboard_cash_balances_hidden(self) -> bool:
        return self.get_bool(self.DASHBOARD_CASH_HIDDEN, False)

    def set_dashboard_cash_balances_hidden(self, hidden: bool) -> None:
        self.set_bool(self.DASHBOARD_CASH_HIDDEN, bool(hidden))

    def dashboard_cash_view_mode(self) -> str:
        mode = self.get_text(self.DASHBOARD_CASH_VIEW_MODE, "today")
        return mode if mode in {"today", "general"} else "today"

    def set_dashboard_cash_view_mode(self, mode: str) -> None:
        self.set_text(self.DASHBOARD_CASH_VIEW_MODE, mode if mode in {"today", "general"} else "today")


user_preferences_service = UserPreferencesService()
