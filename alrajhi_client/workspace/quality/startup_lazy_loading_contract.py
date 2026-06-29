# -*- coding: utf-8 -*-
"""Phase 436 contract: startup lazy-loading optimization."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

REQUIRED_MAIN_WINDOW_MARKERS = [
    "PAGE_FACTORY_SPECS",
    "load_page_factory_class",
    "_lazy_page_factory_specs",
    "_lazy_page_keys_pending",
    "_ensure_page_loaded",
    "available_page_ids",
    "_schedule_post_startup_warmup",
    "_restore_workspace_session_after_first_paint",
    "QTimer.singleShot(250",
    "QTimer.singleShot(900",
    "self._show_fixed_dashboard(refresh=False)",
]

REQUIRED_LAZY_FACTORY_KEYS = [
    "'dashboard'",
    "'items'",
    "'sales_invoices'",
    "'purchase_invoices'",
    "'pos'",
    "'manufacturing'",
    "'customers'",
    "'suppliers'",
    "'vouchers'",
    "'returns'",
    "'purchase_returns'",
    "'reports'",
    "'settings'",
    "'users'",
    "'categories'",
    "'warehouses'",
    "'branches'",
    "'cashboxes'",
    "'audit_log'",
    "'offline_queue'",
    "'monitoring'",
    "'restaurant'",
    "'cafe'",
    "'apparel'",
]

FORBIDDEN_EAGER_IMPORTS = [
    "from views.widgets.items_widget import",
    "from views.widgets.invoices_widget import",
    "from alrajhi_client.views.widgets.pos_widget import",
    "from views.widgets.manufacturing_widget import",
    "from views.widgets.customers_widget import",
    "from views.widgets.suppliers_widget import",
    "from views.widgets.vouchers_widget import",
    "from views.widgets.reports_widget import",
    "from views.widgets.settings_widget import",
    "from views.widgets.users_widget import",
    "from views.widgets.categories_widget import",
    "from views.widgets.warehouses_widget import",
    "from views.widgets.branches_widget import",
    "from views.widgets.cashboxes_widget import",
    "from views.widgets.returns_widget import",
    "from views.widgets.audit_log_widget import",
    "from views.widgets.offline_queue_widget import",
    "from views.widgets.monitoring_widget import",
    "from alrajhi_client.views.restaurant.restaurant_simple_pos_widget import",
    "from views.cafe import CafeWorkspaceWidget",
    "from views.apparel import ApparelWorkspaceWidget",
]

FORBIDDEN_EAGER_CONSTRUCTION_PATTERNS = [
    "for key, factory in page_factories:",
    "self.switch_page('dashboard')\n        self.restore_workspace_session()",
    "factory_by_key = {\n            'dashboard': DashboardWidget,",
]

REQUIRED_DOC_MARKERS = [
    "Phase 436",
    "Startup Lazy Loading Optimization",
    "MainWindow",
    "dashboard only",
    "lazy-loaded",
    "QTimer",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _row(key: str, status: bool, detail: str) -> Dict[str, object]:
    return {"key": key, "status": "pass" if status else "fail", "detail": detail}


def startup_lazy_loading_matrix(root: str | Path) -> List[Dict[str, object]]:
    root = Path(root)
    main_window = _read(root, "alrajhi_client/views/main_window.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")
    doc = _read(root, "PHASE436_STARTUP_LAZY_LOADING_OPTIMIZATION.md")
    rows: List[Dict[str, object]] = []

    for marker in REQUIRED_MAIN_WINDOW_MARKERS:
        rows.append(_row(f"main_window:{marker}", marker in main_window, "main_window.py contains lazy-startup marker"))
    for key in REQUIRED_LAZY_FACTORY_KEYS:
        rows.append(_row(f"factory_key:{key}", key in main_window, "lazy page factory key exists"))
    for pattern in FORBIDDEN_EAGER_IMPORTS:
        rows.append(_row(f"forbidden_import:{pattern}", pattern not in main_window, "heavy page import is not eager at shell startup"))
    for pattern in FORBIDDEN_EAGER_CONSTRUCTION_PATTERNS:
        rows.append(_row(f"forbidden_construct:{pattern[:40]}", pattern not in main_window, "old eager construction path removed"))
    rows.append(_row("brand:phase436", ("'brand_phase': 436" in brand or "'brand_phase': 437" in brand), "brand phase advanced to 436"))
    for marker in REQUIRED_DOC_MARKERS:
        rows.append(_row(f"doc:{marker}", marker in doc, "phase document contains required marker"))
    return rows


def startup_lazy_loading_summary(root: str | Path) -> Dict[str, object]:
    rows = startup_lazy_loading_matrix(root)
    issues = [r for r in rows if r["status"] != "pass"]
    return {
        "phase": 436,
        "checks": len(rows),
        "issues": len(issues),
        "ready": not issues,
    }
