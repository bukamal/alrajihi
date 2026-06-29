# -*- coding: utf-8 -*-
"""Runtime display fitting for the main shell.

Phase 438 makes the main window screen-aware instead of relying on fixed
1200/1400 pixel assumptions.  This matters for X11/VNC, HiDPI, laptops, and
mobile remote-desktop sessions where a fixed desktop geometry can leave large
black bands or push parts of the shell off-screen.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from PyQt5.QtCore import QRect, QSize, QTimer
from PyQt5.QtWidgets import QApplication, QWidget


PHASE = 438


@dataclass(frozen=True)
class MainShellRuntimeFitProfile:
    """Computed geometry profile for a visible runtime screen."""

    screen_width: int
    screen_height: int
    minimum_width: int
    minimum_height: int
    initial_width: int
    initial_height: int
    start_maximized: bool
    policy: str = "screen_aware_maximized"

    def as_dict(self) -> Dict[str, object]:
        return {
            "phase": PHASE,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "minimum_width": self.minimum_width,
            "minimum_height": self.minimum_height,
            "initial_width": self.initial_width,
            "initial_height": self.initial_height,
            "start_maximized": self.start_maximized,
            "policy": self.policy,
        }


def _available_geometry(window: Optional[QWidget] = None) -> QRect:
    screen = None
    try:
        if window is not None and window.screen() is not None:
            screen = window.screen()
    except Exception:
        screen = None
    if screen is None:
        app = QApplication.instance()
        try:
            screen = app.primaryScreen() if app is not None else QApplication.primaryScreen()
        except Exception:
            screen = None
    if screen is not None:
        try:
            return screen.availableGeometry()
        except Exception:
            pass
    return QRect(0, 0, 1366, 768)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on", "y"}


def compute_main_shell_runtime_fit_profile(window: Optional[QWidget] = None) -> MainShellRuntimeFitProfile:
    """Compute a safe runtime profile that never exceeds available geometry."""
    available = _available_geometry(window)
    sw = max(640, int(available.width() or 1366))
    sh = max(480, int(available.height() or 768))

    # Keep a useful ERP baseline, but never force a minimum size larger than the
    # active screen. This avoids clipped shells in mobile VNC and small Windows
    # displays while preserving a desktop-grade layout on normal screens.
    usable_w = max(640, sw - max(24, min(96, int(sw * 0.04))))
    usable_h = max(480, sh - max(24, min(80, int(sh * 0.06))))
    min_w = min(1200, max(860, int(usable_w * 0.72))) if usable_w >= 1000 else max(640, usable_w)
    min_h = min(700, max(560, int(usable_h * 0.72))) if usable_h >= 720 else max(480, usable_h)
    initial_w = min(1400, usable_w)
    initial_h = min(900, usable_h)
    if initial_w < min_w:
        initial_w = min_w
    if initial_h < min_h:
        initial_h = min_h

    # ERP shells should start maximized by default.  Windowed mode remains
    # available for tests or special desktop workflows via an explicit flag.
    start_maximized = not _env_flag("ALRAJHI_WINDOWED_START", False)
    return MainShellRuntimeFitProfile(
        screen_width=sw,
        screen_height=sh,
        minimum_width=int(min_w),
        minimum_height=int(min_h),
        initial_width=int(initial_w),
        initial_height=int(initial_h),
        start_maximized=bool(start_maximized),
    )


def apply_main_shell_runtime_fit(window: QWidget) -> MainShellRuntimeFitProfile:
    """Apply minimum/initial sizing before the main window is shown."""
    profile = compute_main_shell_runtime_fit_profile(window)
    window.setProperty("mainShellRuntimeFitPhase", PHASE)
    window.setProperty("mainShellRuntimeFitPolicy", profile.policy)
    window.setProperty("mainShellStartsMaximized", profile.start_maximized)
    window.setMinimumSize(QSize(profile.minimum_width, profile.minimum_height))
    window.resize(profile.initial_width, profile.initial_height)
    return profile


def _clamp_to_available(window: QWidget) -> None:
    """Keep non-maximized shell geometry inside the active screen."""
    if window.isMaximized() or window.isFullScreen():
        return
    available = _available_geometry(window)
    geom = window.frameGeometry()
    width = min(max(window.minimumWidth(), geom.width()), max(window.minimumWidth(), available.width()))
    height = min(max(window.minimumHeight(), geom.height()), max(window.minimumHeight(), available.height()))
    x = min(max(available.left(), geom.left()), max(available.left(), available.right() - width + 1))
    y = min(max(available.top(), geom.top()), max(available.top(), available.bottom() - height + 1))
    window.resize(width, height)
    window.move(x, y)


def show_main_window_runtime_fitted(window: QWidget) -> MainShellRuntimeFitProfile:
    """Show the main shell using the runtime fit policy.

    The default is maximized so the dashboard uses the whole available desktop
    instead of appearing as a smaller fixed window surrounded by black remote
    desktop margins.  A delayed clamp protects explicit windowed runs.
    """
    profile = apply_main_shell_runtime_fit(window)
    if profile.start_maximized:
        window.showMaximized()
    else:
        window.show()
    QTimer.singleShot(0, lambda: _clamp_to_available(window))
    return profile
