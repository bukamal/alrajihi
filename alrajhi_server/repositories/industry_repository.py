from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db

ALLOWED_INDUSTRIES = {"general", "pharmacy", "restaurant", "apparel", "mixed"}
ALLOWED_UI_MODES = {"classic", "touch_pos", "compact"}


class IndustryRepository:
    """Repository for industry profile and touch-mode settings.

    The values are persisted in the existing settings table to avoid a disruptive
    schema dependency while still exposing domain-specific methods to API/service
    layers.
    """

    def _set_setting(self, key: str, value: Any, category: str = "industry") -> None:
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute(
            "INSERT OR REPLACE INTO settings (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
            (key, str(value), category, now),
        )
        db.commit()

    def _get_setting(self, key: str, default: Any = None) -> Any:
        row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def get_profile(self) -> dict[str, Any]:
        industry = str(self._get_setting("industry/profile", "general") or "general")
        if industry not in ALLOWED_INDUSTRIES:
            industry = "general"
        ui_mode = str(self._get_setting("ui/mode", "classic") or "classic")
        if ui_mode not in ALLOWED_UI_MODES:
            ui_mode = "classic"
        enabled = str(self._get_setting("industry/enabled_modules", industry) or industry)
        modules = [m.strip() for m in enabled.split(",") if m.strip()]
        return {
            "industry": industry,
            "ui_mode": ui_mode,
            "touch_enabled": ui_mode == "touch_pos",
            "enabled_modules": modules,
            "supported_industries": sorted(ALLOWED_INDUSTRIES),
            "supported_ui_modes": sorted(ALLOWED_UI_MODES),
        }

    def set_profile(self, industry: str, ui_mode: str | None = None, enabled_modules: list[str] | None = None) -> dict[str, Any]:
        industry = (industry or "general").strip().lower()
        if industry not in ALLOWED_INDUSTRIES:
            raise ValueError(f"Unsupported industry profile: {industry}")
        self._set_setting("industry/profile", industry)
        if ui_mode is not None:
            mode = (ui_mode or "classic").strip().lower()
            if mode not in ALLOWED_UI_MODES:
                raise ValueError(f"Unsupported UI mode: {mode}")
            self._set_setting("ui/mode", mode, category="ui")
        if enabled_modules is None:
            enabled_modules = [industry]
        clean = []
        for module in enabled_modules:
            module = str(module or "").strip().lower()
            if module and module in ALLOWED_INDUSTRIES and module not in clean:
                clean.append(module)
        self._set_setting("industry/enabled_modules", ",".join(clean or [industry]))
        return self.get_profile()


def get_industry_repository() -> IndustryRepository:
    return IndustryRepository()
