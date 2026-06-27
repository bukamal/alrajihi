# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_category_inline_editor_has_save_button_outside_hidden_header_card():
    src = read("alrajhi_client/features/categories/category_editor_tab.py")
    assert "self.header = CategoryHeaderPanel" in src
    assert "self.inline_action_bar = QWidget(self)" in src
    assert "CategoryInlineActionBar" in src
    assert "root.addWidget(self.header)" in src
    assert "root.addWidget(self.properties)\n        root.addWidget(self.inline_action_bar)" in src


def test_inline_save_uses_same_save_command_and_permission_state():
    src = read("alrajhi_client/features/categories/category_editor_tab.py")
    assert "self.header.saveRequested.connect(self.workspace_save)" in src
    assert "self.inline_save_btn.clicked.connect(self.workspace_save)" in src
    assert "self.inline_save_btn.setEnabled(self._can_edit)" in src


def test_inline_layout_profile_shows_save_action_when_header_is_hidden():
    src = read("alrajhi_client/features/categories/category_editor_tab.py")
    block = src.split("def apply_document_layout_profile", 1)[1].split("def reload_parent_categories", 1)[0]
    assert "super().apply_document_layout_profile" in block
    assert "inline_mode" in block
    assert "self.inline_action_bar.setVisible(inline_mode)" in block


def test_quality_contract_documents_category_inline_save():
    contract = read("alrajhi_client/workspace/quality/category_inline_save_contract.py")
    assert "CATEGORY_INLINE_SAVE_CONTRACT" in contract
    assert "inline_save_outside_hidden_document_header" in contract
    assert "permission_state_applies_to_inline_save" in contract
