# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]

PREFERENCES_REGISTRY_CONSOLIDATION_CONTRACT: Dict[str, object] = {
    "phase": 419,
    "name": "preferences_registry_consolidation",
    "registry_module": "core.services.preferences_registry",
    "owners": [
        "user preferences",
        "dashboard privacy preferences",
        "theme preference",
        "transaction grid layout keys",
        "POS preference keys",
        "company/workstation preference catalog",
    ],
    "scopes": [
        "system",
        "company",
        "branch",
        "user",
        "user_branch",
        "workstation",
        "table_layout",
        "document_type",
        "pos_terminal",
    ],
    "requirements": [
        "All new UI preferences must declare a scope in PREFERENCE_DEFINITIONS.",
        "UserPreferencesService must resolve keys through PreferencesRegistry.",
        "TransactionGridPreferences must resolve document layout keys through PreferencesRegistry.",
        "POSPreferences must resolve POS keys through PreferencesRegistry.",
        "Theme persistence must use UserPreferencesService rather than raw QSettings.",
        "Direct QSettings usages that remain must be visible in the Phase419 audit matrix.",
    ],
}


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def preferences_registry_consolidation_summary(root: Path | None = None) -> Dict[str, object]:
    base = root or ROOT
    required = [
        "PHASE419_PREFERENCES_REGISTRY_CONSOLIDATION.md",
        "alrajhi_client/core/services/preferences_registry.py",
        "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py",
        "tools/phase419_preferences_registry_consolidation_guard.py",
        "tests/test_phase419_preferences_registry_consolidation.py",
    ]
    missing: List[str] = [rel for rel in required if not _exists(base, rel)]
    return {
        "phase": 419,
        "name": "preferences_registry_consolidation",
        "required_files": len(required),
        "missing": missing,
        "ready": not missing,
    }


__all__ = [
    "PREFERENCES_REGISTRY_CONSOLIDATION_CONTRACT",
    "preferences_registry_consolidation_summary",
]
