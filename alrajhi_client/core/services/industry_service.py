# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from gateways.industry_gateway import create_industry_gateway


class IndustryService:
    """Application service for vertical industry profile and UI mode."""

    def __init__(self):
        self.gateway = create_industry_gateway()

    def get_profile(self) -> dict[str, Any]:
        return self.gateway.get_profile()

    def set_profile(self, industry: str, ui_mode: str | None = None, enabled_modules: list[str] | None = None) -> dict[str, Any]:
        return self.gateway.set_profile(industry, ui_mode=ui_mode, enabled_modules=enabled_modules)

    def is_touch_enabled(self) -> bool:
        return bool(self.get_profile().get("touch_enabled"))

    def is_module_enabled(self, module: str) -> bool:
        module = str(module or "").strip().lower()
        profile = self.get_profile()
        return profile.get("industry") == module or module in set(profile.get("enabled_modules") or [])


industry_service = IndustryService()
