# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from gateways.industry_gateway import IndustryGateway
from gateways.settings_gateway import create_settings_gateway

ALLOWED_INDUSTRIES = {"general", "pharmacy", "restaurant", "apparel", "mixed"}
ALLOWED_UI_MODES = {"classic", "touch_pos", "compact"}


class LocalIndustryGateway(IndustryGateway):
    def __init__(self):
        self.settings = create_settings_gateway()

    def get_profile(self) -> dict[str, Any]:
        industry = str(self.settings.get("industry/profile", "general") or "general")
        if industry not in ALLOWED_INDUSTRIES:
            industry = "general"
        ui_mode = str(self.settings.get("ui/mode", "classic") or "classic")
        if ui_mode not in ALLOWED_UI_MODES:
            ui_mode = "classic"
        modules = [m.strip() for m in str(self.settings.get("industry/enabled_modules", industry) or industry).split(",") if m.strip()]
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
        self.settings.set("industry/profile", industry)
        if ui_mode is not None:
            mode = (ui_mode or "classic").strip().lower()
            if mode not in ALLOWED_UI_MODES:
                raise ValueError(f"Unsupported UI mode: {mode}")
            self.settings.set("ui/mode", mode)
        if enabled_modules is None:
            enabled_modules = [industry]
        clean = []
        for module in enabled_modules:
            module = str(module or "").strip().lower()
            if module in ALLOWED_INDUSTRIES and module not in clean:
                clean.append(module)
        self.settings.set("industry/enabled_modules", ",".join(clean or [industry]))
        return self.get_profile()
