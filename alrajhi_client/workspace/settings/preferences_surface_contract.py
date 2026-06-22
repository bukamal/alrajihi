# -*- coding: utf-8 -*-
"""Unified settings surface contract for UI, columns and barcode profiles.

Phase 341 makes the contracts created in Phases 331-340 visible to the settings
layer instead of leaving them as hidden Python registries.  The module is
PyQt-free so release guards can validate the settings surface without importing
widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from workspace.registry import BARCODE_PRINT_PROFILES
from workspace.tables.column_contract import TableColumnContract
from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS
from workspace.settings.column_preferences import validate_column_preference_runtime

BARCODE_PROFILE_SETTING_FIELDS: tuple[str, ...] = (
    "template_id",
    "label_size",
    "symbology",
    "copies",
    "columns",
    "show_company",
    "show_logo",
    "show_qr",
    "show_name",
    "show_price",
    "show_barcode_text",
    "show_variant_color_size",
    "show_variant_code",
    "show_section",
    "show_table_zone",
    "show_modifier_group",
    "show_size",
)

COLUMN_SETTING_SUFFIXES: tuple[str, ...] = ("visible", "printable", "exportable")


@dataclass(frozen=True)
class SettingsSurfaceRow:
    surface_type: str
    id: str
    title: str
    settings_prefix: str
    setting_keys: tuple[str, ...]

    def as_dict(self) -> Dict[str, object]:
        return {
            "surface_type": self.surface_type,
            "id": self.id,
            "title": self.title,
            "settings_prefix": self.settings_prefix,
            "settings_count": len(self.setting_keys),
            "setting_keys": ";".join(self.setting_keys),
        }


def _column_setting_keys(contract: TableColumnContract) -> tuple[str, ...]:
    keys: list[str] = []
    for column in contract.columns:
        base = str(column.settings_key or "").rstrip("/")
        if not base:
            continue
        for suffix in COLUMN_SETTING_SUFFIXES:
            keys.append(f"{base}/{suffix}")
    return tuple(keys)


def _barcode_setting_keys(profile_id: str) -> tuple[str, ...]:
    profile = BARCODE_PRINT_PROFILES[profile_id]
    prefix = str(profile.settings_prefix or "").rstrip("/")
    return tuple(f"{prefix}/{field}" for field in BARCODE_PROFILE_SETTING_FIELDS)


def settings_surface_rows() -> tuple[SettingsSurfaceRow, ...]:
    rows: list[SettingsSurfaceRow] = []
    for contract_id, contract in sorted(TABLE_COLUMN_CONTRACTS.items()):
        rows.append(SettingsSurfaceRow(
            surface_type="columns",
            id=contract_id,
            title=f"{contract.page_id}.{contract.table_id}",
            settings_prefix=contract.settings_prefix,
            setting_keys=_column_setting_keys(contract),
        ))
    for profile_id, profile in sorted(BARCODE_PRINT_PROFILES.items()):
        rows.append(SettingsSurfaceRow(
            surface_type="barcode_profile",
            id=profile_id,
            title=profile.title_key,
            settings_prefix=profile.settings_prefix,
            setting_keys=_barcode_setting_keys(profile_id),
        ))
    return tuple(rows)


def settings_surface_matrix() -> List[Dict[str, object]]:
    return [row.as_dict() for row in settings_surface_rows()]


def validate_settings_surface() -> Dict[str, list[str]]:
    issues: Dict[str, list[str]] = {}
    for contract_id, contract in sorted(TABLE_COLUMN_CONTRACTS.items()):
        if not contract.settings_prefix.startswith("ui/columns/"):
            issues.setdefault("column_prefix", []).append(contract_id)
        missing = [col.key for col in contract.columns if not col.settings_key]
        if missing:
            issues.setdefault("column_setting_keys", []).append(f"{contract_id}: {','.join(missing)}")
        if not contract.columns:
            issues.setdefault("column_empty", []).append(contract_id)
    runtime_issues = validate_column_preference_runtime()
    for group, items in runtime_issues.items():
        for item in items:
            issues.setdefault(f"column_runtime_{group}", []).append(item)
    for profile_id, profile in sorted(BARCODE_PRINT_PROFILES.items()):
        if not profile.settings_prefix.startswith("printing/barcode/"):
            issues.setdefault("barcode_prefix", []).append(profile_id)
        keys = _barcode_setting_keys(profile_id)
        if not keys:
            issues.setdefault("barcode_settings", []).append(profile_id)
        if not profile.browser_html_only:
            issues.setdefault("barcode_browser_html", []).append(profile_id)
        if not profile.supports_multi_print:
            issues.setdefault("barcode_multi_print", []).append(profile_id)
    return issues


__all__ = [
    "BARCODE_PROFILE_SETTING_FIELDS",
    "COLUMN_SETTING_SUFFIXES",
    "SettingsSurfaceRow",
    "settings_surface_rows",
    "settings_surface_matrix",
    "validate_settings_surface",
]
