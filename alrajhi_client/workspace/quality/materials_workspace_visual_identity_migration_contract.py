# -*- coding: utf-8 -*-
"""Phase445 materials workspace visual identity migration contract.

The contract is intentionally static/Qt-free. It verifies that materials list and
material editor surfaces opt into the centralized visual identity instead of
local, hard-coded styling.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "materials_visual_phase",
    "materials_filter_card_bg",
    "materials_filter_chip_bg",
    "materials_table_header_bg",
    "materials_editor_card_radius",
    "materials_editor_primary_action_bg",
]

REQUIRED_QSS_MARKERS = [
    'QFrame#MaterialsFilterCard',
    'visualRole="materials_filter"',
    'visualRole="materials_table"',
    'visualRole="material_form_card"',
    'QFrame#MaterialEditorActionBar',
]

REQUIRED_LIST_MARKERS = [
    "MaterialsFilterCard",
    "materialsFilterSurface",
    "_apply_materials_workspace_identity",
    "visualRole', 'materials_toolbar'",
    "visualRole', 'materials_table'",
]

REQUIRED_EDITOR_MARKERS = [
    "MaterialBasicCard",
    "MaterialPricingCard",
    "MaterialBarcodeCard",
    "MaterialUnitsCard",
    "MaterialEditorActionBar",
    "visualRole', 'material_form_card'",
    "visualRole', 'material_editor'",
    "centralized material visual identity",
]

FORBIDDEN_EDITOR_LOCAL_QSS = [
    "QFrame#DocumentHeaderCard",
    "QGroupBox#FormCard",
    "QFrame#BottomActionBar",
    "QHeaderView::section { font-weight: 800; padding: 7px; }",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase445_materials_workspace_visual_identity_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"Missing material brand token: {token}")
    checks += 1
    if not any(marker in brand for marker in ("'project_visual_identity_phase': 445", "'project_visual_identity_phase': 446", "'project_visual_identity_phase': 447", "'project_visual_identity_phase': 450", "'project_visual_identity_phase': 451")):
        details.append("Project visual identity phase must be 445 or later.")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"Missing material QSS selector/marker: {marker}")

    list_src = _read(root, "alrajhi_client/views/widgets/items_widget.py")
    for marker in REQUIRED_LIST_MARKERS:
        checks += 1
        if marker not in list_src:
            details.append(f"Materials list missing visual marker: {marker}")
    checks += 1
    if "insertLayout(1, filter_layout)" in list_src:
        details.append("Materials filters must be inside MaterialsFilterCard, not a raw inserted layout.")

    editor_src = _read(root, "alrajhi_client/features/items/item_editor_tab.py")
    for marker in REQUIRED_EDITOR_MARKERS:
        checks += 1
        if marker not in editor_src:
            details.append(f"Material editor missing visual marker: {marker}")
    for marker in FORBIDDEN_EDITOR_LOCAL_QSS:
        checks += 1
        if marker in editor_src:
            details.append(f"Material editor still contains legacy local QSS marker: {marker}")

    runtime = _read(root, "alrajhi_client/ui/runtime_visual_polish.py")
    checks += 1
    if 'if not child.property("visualRole")' not in runtime:
        details.append("Runtime visual polish must preserve explicit material visualRole properties.")
    checks += 1
    if 'if not table.property("visualRole")' not in runtime:
        details.append("Runtime table polish must preserve materials_table visualRole.")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 445,
    }
