# -*- coding: utf-8 -*-
"""Universal table-column contract foundation.

Phase 334: column visibility, printing and export must not be hard-coded inside
individual screens.  This module is PyQt-free and describes the stable column
metadata consumed by tables, printing and settings.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ColumnDefinition:
    """One stable column definition shared by display, print and export paths."""

    key: str
    label_key: str
    visible_default: bool = True
    printable_default: bool = True
    exportable_default: bool = True
    width: int = 120
    alignment: str = "center"
    data_type: str = "text"
    editable: bool = False
    required: bool = False
    permission: str = ""
    settings_key: str = ""

    def scoped(self, table_settings_prefix: str) -> "ColumnDefinition":
        prefix = (table_settings_prefix or "").rstrip("/")
        if not prefix or self.settings_key:
            return self
        return replace(self, settings_key=f"{prefix}/{self.key}")


@dataclass(frozen=True)
class TableColumnContract:
    """Column contract for one concrete table in one workspace."""

    page_id: str
    table_id: str
    table_type: str
    settings_prefix: str
    columns: tuple[ColumnDefinition, ...]
    editable: bool = False
    printable: bool = True
    exportable: bool = True

    @property
    def contract_id(self) -> str:
        return f"{self.page_id}.{self.table_id}"

    def column(self, key: str) -> ColumnDefinition | None:
        key = str(key or "")
        for col in self.columns:
            if col.key == key:
                return col
        return None

    def required_keys(self) -> tuple[str, ...]:
        return tuple(col.key for col in self.columns if col.required)

    def default_visible_keys(self) -> tuple[str, ...]:
        return tuple(col.key for col in self.columns if col.visible_default or col.required)

    def default_printable_keys(self) -> tuple[str, ...]:
        if not self.printable:
            return tuple()
        return tuple(col.key for col in self.columns if col.printable_default)

    def default_exportable_keys(self) -> tuple[str, ...]:
        if not self.exportable:
            return tuple()
        return tuple(col.key for col in self.columns if col.exportable_default)


def contract_id(page_id: str, table_id: str) -> str:
    return f"{str(page_id or '').strip()}.{str(table_id or '').strip()}"


def scoped_columns(columns: Iterable[ColumnDefinition], table_settings_prefix: str) -> tuple[ColumnDefinition, ...]:
    return tuple(col.scoped(table_settings_prefix) for col in columns)


def column_keys(columns: Iterable[ColumnDefinition]) -> tuple[str, ...]:
    return tuple(col.key for col in columns)


def allowed_keys_for_purpose(contract: TableColumnContract | None, purpose: str) -> set[str]:
    if contract is None:
        return set()
    purpose = (purpose or "display").strip().lower()
    if purpose == "print":
        return set(contract.default_printable_keys())
    if purpose == "export":
        return set(contract.default_exportable_keys())
    return set(contract.default_visible_keys())


def validate_unique_keys(columns: Iterable[ColumnDefinition]) -> bool:
    keys = [col.key for col in columns]
    return len(keys) == len(set(keys))
