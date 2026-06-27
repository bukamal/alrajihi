# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "feature_activation_gate_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/feature_activation_gate_contract.py", "FEATURE_ACTIVATION_GATE_CONTRACT"),
    ("app_paths_feature_license", "alrajhi_client/core/app_paths.py", "def feature_license_file(feature: str)"),
    ("auth_generic_activate", "alrajhi_client/auth/activation.py", "def activate_feature(feature: str, license_key: str)"),
    ("auth_generic_check", "alrajhi_client/auth/activation.py", "def check_feature_activation(feature: str)"),
    ("network_uses_generic", "alrajhi_client/auth/activation.py", "return activate_feature('network', license_key)"),
    ("dialog_exists", "alrajhi_client/views/dialogs/module_activation_dialog.py", "class ModuleActivationDialog"),
    ("dialog_uses_generic", "alrajhi_client/views/dialogs/module_activation_dialog.py", "activate_feature(self.feature, key)"),
    ("main_page_gate", "alrajhi_client/views/main_window.py", "PAID_FEATURE_PAGES"),
    ("manufacturing_page_protected", "alrajhi_client/views/main_window.py", "'manufacturing': 'manufacturing'"),
    ("restaurant_page_protected", "alrajhi_client/views/main_window.py", "'restaurant': 'restaurant'"),
    ("cafe_page_protected", "alrajhi_client/views/main_window.py", "'cafe': 'cafe'"),
    ("apparel_page_protected", "alrajhi_client/views/main_window.py", "'apparel': 'apparel'"),
    ("switch_page_checks_gate", "alrajhi_client/views/main_window.py", "not self._ensure_page_feature_activation(pid)"),
    ("bom_document_protected", "alrajhi_client/views/main_window.py", "open_bom_document(self, bom_id=None):\n        if not self._ensure_feature_activation('manufacturing'"),
    ("production_order_protected", "alrajhi_client/views/main_window.py", "open_production_order_document(self):\n        if not self._ensure_feature_activation('manufacturing'"),
    ("network_settings_unified", "alrajhi_client/views/widgets/settings_widget.py", "ModuleActivationDialog.ensure_feature"),
    ("i18n_activation_title", "alrajhi_client/i18n/translator.py", "module_activation_title"),
    ("i18n_french_feature_label", "alrajhi_client/i18n/translator.py", "feature_activation_apparel"),
]


def main() -> int:
    rows = []
    issues = []
    for name, rel, needle in CHECKS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        ok = needle in text
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            issues.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase397 feature activation gate guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase397 feature activation gate guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
