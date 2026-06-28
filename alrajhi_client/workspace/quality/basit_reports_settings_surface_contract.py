# -*- coding: utf-8 -*-
from __future__ import annotations

BASIT_REPORTS_SETTINGS_SURFACE_CONTRACT = {
    "phase": 405,
    "name": "basit_reports_settings_surface",
    "surfaces": ["reports", "settings"],
    "requirements": [
        "Reports filter controls use a Basit-style operational toolbar.",
        "Reports tables use the shared basitTable surface and compact accounting profile.",
        "Reports summary bar uses the red Basit total surface for high-visibility totals.",
        "Settings grouped navigation, nested tabs and cards use the same blue/yellow Basit grammar.",
        "Settings save/action buttons inherit the shared Basit toolbar button profile.",
    ],
    "markers": {
        "reports_root": "basitReportsSurface",
        "reports_toolbar": "basitReportToolbar",
        "reports_table": "basitReportTable",
        "reports_summary": "basitReportSummary",
        "settings_root": "basitSettingsSurface",
        "settings_tabs": "basitSettingsTabs",
        "settings_card": "basitSettingsCard",
    },
}
