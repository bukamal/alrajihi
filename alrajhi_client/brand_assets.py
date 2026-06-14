# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


def _base_dirs() -> list[Path]:
    """Return possible locations of bundled brand assets in source and PyInstaller builds."""
    here = Path(__file__).resolve().parent
    dirs: list[Path] = []

    # Source tree: alrajhi_client/assets/brand
    dirs.append(here / "assets" / "brand")

    # PyInstaller one-dir/one-file runtime: sys._MEIPASS/assets/brand
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(Path(meipass) / "assets" / "brand")
        dirs.append(Path(meipass) / "alrajhi_client" / "assets" / "brand")

    # Executable folder fallbacks.
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        dirs.append(exe_dir / "assets" / "brand")
        dirs.append(exe_dir / "_internal" / "assets" / "brand")
        dirs.append(exe_dir / "_internal" / "alrajhi_client" / "assets" / "brand")

    # Development fallback when imported through a different module layout.
    dirs.append(Path.cwd() / "alrajhi_client" / "assets" / "brand")
    dirs.append(Path.cwd() / "assets" / "brand")

    seen: set[str] = set()
    out: list[Path] = []
    for d in dirs:
        key = str(d)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def asset_path(name: str) -> str:
    for base in _base_dirs():
        candidate = base / name
        if candidate.exists():
            return str(candidate)
    # Return the canonical source path even if missing; callers can test QPixmap/isNull.
    return str(_base_dirs()[0] / name)


def logo_png(size: int = 512) -> str:
    for name in (f"logo_{size}.png", "logo.png"):
        path = asset_path(name)
        if Path(path).exists():
            return path
    return asset_path("logo.png")


def app_icon() -> str:
    return asset_path("app.ico")


APP_DISPLAY_NAME_AR = "الراجحي للمحاسبة والمستودعات"
APP_DESCRIPTION_AR = "نظام الراجحي للمحاسبة والمستودعات"
APP_DISPLAY_NAME_EN = "AlRajhi Accounting & Warehouses"
