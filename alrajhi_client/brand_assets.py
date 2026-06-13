# -*- coding: utf-8 -*-
from pathlib import Path


def asset_path(name: str) -> str:
    return str(Path(__file__).resolve().parent / "assets" / "brand" / name)


def logo_png(size: int = 512) -> str:
    candidate = Path(asset_path(f"logo_{size}.png"))
    return str(candidate if candidate.exists() else Path(asset_path("logo.png")))


def app_icon() -> str:
    return asset_path("app.ico")


APP_DISPLAY_NAME_AR = "الراجحي ERP"
APP_DESCRIPTION_AR = "إدارة المخزون والمحاسبة والتصنيع"
APP_DISPLAY_NAME_EN = "AlRajhi ERP"
