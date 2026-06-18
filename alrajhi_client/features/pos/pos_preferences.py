# -*- coding: utf-8 -*-
from __future__ import annotations

"""POS UI preference persistence scoped through the project settings layer.

The POS screen is cashier-facing and often runs on shared terminals, but layout
state still must not be saved through raw QSettings.  This helper mirrors the
transaction/material grid preference contract: user + branch + active settings
profile + POS identity.
"""

from auth.session import UserSession
from core.services.settings_service import settings_service


class POSPreferences:
    def __init__(self, identity: str = "pos.lines"):
        self.identity = identity or "pos.lines"
        self.scope = self._scope_key()

    def _scope_key(self) -> str:
        user_id = UserSession.get_current_user_id() or UserSession.get_current_username() or "anonymous"
        branch_id = UserSession.get_current_branch_id() or "global"
        try:
            profile = settings_service.get_active_profile() or {}
            profile_id = profile.get("id") or 1
        except Exception:
            profile_id = 1
        return f"users/{user_id}/branches/{branch_id}/profiles/{profile_id}"

    def key(self, name: str) -> str:
        return f"pos/{self.scope}/{self.identity}/{name}"

    def get(self, name: str, default=None):
        return settings_service.get(self.key(name), default)

    def set(self, name: str, value) -> None:
        settings_service.set(self.key(name), value)

    def visible_columns(self, default_keys: list[str]) -> list[str]:
        raw = self.get("visible_columns", ",".join(default_keys))
        if isinstance(raw, (list, tuple)):
            values = [str(v) for v in raw]
        else:
            values = [v.strip() for v in str(raw or "").split(",") if v.strip()]
        allowed = set(default_keys)
        selected = [value for value in values if value in allowed]
        return selected or list(default_keys)

    def save_visible_columns(self, keys: list[str]) -> None:
        self.set("visible_columns", ",".join(keys or []))

    def density(self, default: str = "touch") -> str:
        value = str(self.get("density", default) or default).lower()
        return value if value in ("compact", "comfortable", "touch") else default

    def save_density(self, density: str) -> None:
        value = str(density or "touch").lower()
        if value not in ("compact", "comfortable", "touch"):
            value = "touch"
        self.set("density", value)
    def preset(self, default: str = "cashier") -> str:
        value = str(self.get("preset", default) or default).lower()
        return value if value in ("compact", "cashier", "accountant", "warehouse", "manager") else default

    def save_preset(self, preset: str) -> None:
        value = str(preset or "cashier").lower()
        if value not in ("compact", "cashier", "accountant", "warehouse", "manager"):
            value = "cashier"
        self.set("preset", value)

