# -*- coding: utf-8 -*-
"""Persistent per-user UI preferences (Phase 413).

This service stores lightweight runtime UI choices that must survive closing and
re-opening the desktop client.  It intentionally uses QSettings instead of the
business settings table because these values are user/workstation preferences,
not tenant accounting configuration.
"""
from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QSettings

try:  # Imported lazily in tests/headless tooling as well as runtime.
    from auth.session import UserSession
except Exception:  # pragma: no cover - defensive import fallback
    UserSession = None  # type: ignore


class UserPreferencesService:
    ORG = "Alrajhi"
    APP = "Accounting"
    ROOT = "user_preferences"
    # Phase413: dashboard visibility preferences are persisted under these stable keys.
    DASHBOARD_CASH_HIDDEN = "dashboard/cash_balances_hidden"
    DASHBOARD_CASH_VIEW_MODE = "dashboard/cash_view_mode"

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings(self.ORG, self.APP)

    def _current_user_key(self) -> str:
        uid = None
        try:
            if UserSession is not None:
                uid = UserSession.get_current_user_id() or UserSession.get_current_username()
        except Exception:
            uid = None
        text = str(uid or "anonymous").strip() or "anonymous"
        return self._safe_segment(text)

    def _current_branch_key(self) -> str:
        branch_id = None
        try:
            if UserSession is not None:
                branch_id = UserSession.get_current_branch_id()
        except Exception:
            branch_id = None
        text = str(branch_id if branch_id not in (None, "") else "global")
        return self._safe_segment(text)

    @staticmethod
    def _safe_segment(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in value)

    def key(self, preference_key: str, *, branch_scoped: bool = False) -> str:
        parts = [self.ROOT, self._current_user_key()]
        if branch_scoped:
            parts.append(self._current_branch_key())
        parts.append(str(preference_key).strip("/"))
        return "/".join(parts)

    def get(self, preference_key: str, default: Any = None, *, branch_scoped: bool = False) -> Any:
        return self._settings.value(self.key(preference_key, branch_scoped=branch_scoped), default)

    def set(self, preference_key: str, value: Any, *, branch_scoped: bool = False) -> None:
        self._settings.setValue(self.key(preference_key, branch_scoped=branch_scoped), value)
        self._settings.sync()

    def get_bool(self, preference_key: str, default: bool = False, *, branch_scoped: bool = False) -> bool:
        value = self.get(preference_key, default, branch_scoped=branch_scoped)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def set_bool(self, preference_key: str, value: bool, *, branch_scoped: bool = False) -> None:
        self.set(preference_key, "true" if bool(value) else "false", branch_scoped=branch_scoped)

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
