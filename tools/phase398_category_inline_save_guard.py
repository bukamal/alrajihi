# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "category_inline_save_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/category_inline_save_contract.py", "CATEGORY_INLINE_SAVE_CONTRACT"),
    ("inline_bar_created", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_action_bar = QWidget(self)"),
    ("inline_bar_named", "alrajhi_client/features/categories/category_editor_tab.py", "CategoryInlineActionBar"),
    ("inline_save_button_created", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_save_btn = QPushButton(translate('save')"),
    ("inline_save_wired", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_save_btn.clicked.connect(self.workspace_save)"),
    ("inline_bar_added_after_properties", "alrajhi_client/features/categories/category_editor_tab.py", "root.addWidget(self.properties)\n        root.addWidget(self.inline_action_bar)"),
    ("inline_bar_hidden_by_default", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_action_bar.setVisible(False)"),
    ("layout_profile_override", "alrajhi_client/features/categories/category_editor_tab.py", "def apply_document_layout_profile"),
    ("inline_mode_shows_bar", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_action_bar.setVisible(inline_mode)"),
    ("permission_applies", "alrajhi_client/features/categories/category_editor_tab.py", "self.inline_save_btn.setEnabled(self._can_edit)"),
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
        print("Phase398 category inline save guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase398 category inline save guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
