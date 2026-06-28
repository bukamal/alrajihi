#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    ("contract", "alrajhi_client/workspace/quality/basit_management_surface_contract.py", "BASIT_MANAGEMENT_SURFACE_CONTRACT"),
    ("base_widget_workspace", "alrajhi_client/views/widgets/base_widget.py", "basitManagementWorkspace"),
    ("base_widget_toolbar", "alrajhi_client/views/widgets/base_widget.py", "basitListToolbar"),
    ("base_widget_table", "alrajhi_client/views/widgets/base_widget.py", "basitManagementTable"),
    ("toolbar_property", "alrajhi_client/views/widgets/components/table_toolbar.py", "self.setProperty('basitListToolbar', True)"),
    ("toolbar_buttons", "alrajhi_client/views/widgets/components/table_toolbar.py", "basitToolbarButton"),
    ("toolbar_search", "alrajhi_client/views/widgets/components/table_toolbar.py", "basitListSearch"),
    ("responsive_master_detail", "alrajhi_client/ui/components/responsive_master_detail.py", "basitMasterDetail"),
    ("detail_placeholder", "alrajhi_client/ui/components/responsive_master_detail.py", "basitDetailPlaceholder"),
    ("inline_workspace", "alrajhi_client/views/widgets/unified_inline_workspace.py", "basitManagementWorkspace"),
    ("inline_back", "alrajhi_client/views/widgets/unified_inline_workspace.py", "basitToolbarButton"),
    ("modern_surface_helper", "alrajhi_client/views/widgets/modern_ui.py", "def _apply_basit_list_surface"),
    ("modern_surface_call", "alrajhi_client/views/widgets/modern_ui.py", "_apply_basit_list_surface(widget)"),
    ("qss_phase", "alrajhi_client/theme/qss.py", "Phase404: Basit-inspired management/list workspaces"),
    ("qss_workspace", "alrajhi_client/theme/qss.py", "QWidget[basitManagementWorkspace=\"true\"]"),
    ("qss_toolbar", "alrajhi_client/theme/qss.py", "QWidget[basitListToolbar=\"true\"]"),
    ("qss_splitter", "alrajhi_client/theme/qss.py", "QSplitter#ResponsiveMasterDetailSplitter[basitMasterDetailSplitter=\"true\"]"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    issues: list[str] = []
    for name, rel, needle in CHECKS:
        if needle not in read(rel):
            issues.append(f"{name}: missing {needle!r} in {rel}")
    if issues:
        print("phase404_basit_management_surface_guard failed")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"phase404_basit_management_surface_guard passed ({len(CHECKS)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
