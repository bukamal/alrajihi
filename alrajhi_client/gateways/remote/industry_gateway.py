# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from gateways.industry_gateway import IndustryGateway


class RemoteIndustryGateway(IndustryGateway):
    def __init__(self, client):
        self.client = client

    def get_profile(self) -> dict[str, Any]:
        return self.client._request("GET", "/api/industry/profile") or {}

    def set_profile(self, industry: str, ui_mode: str | None = None, enabled_modules: list[str] | None = None) -> dict[str, Any]:
        return self.client._request("PUT", "/api/industry/profile", {
            "industry": industry,
            "ui_mode": ui_mode,
            "enabled_modules": enabled_modules,
        }) or {}
