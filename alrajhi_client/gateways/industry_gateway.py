# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IndustryGateway(ABC):
    @abstractmethod
    def get_profile(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def set_profile(self, industry: str, ui_mode: str | None = None, enabled_modules: list[str] | None = None) -> dict[str, Any]:
        raise NotImplementedError


def create_industry_gateway() -> IndustryGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.industry_gateway import RemoteIndustryGateway
        return RemoteIndustryGateway(db.get_rest_client())
    from gateways.local.industry_gateway import LocalIndustryGateway
    return LocalIndustryGateway()
