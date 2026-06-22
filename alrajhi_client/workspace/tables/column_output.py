# -*- coding: utf-8 -*-
"""Column output mapping for printing and export.

Phase 336: screen visibility, print visibility and export visibility are
separate concerns.  This module resolves the universal column contract through
settings and exposes PyQt-free helpers used by tables and print templates.
"""
from __future__ import annotations

from typing import Iterable

from .column_contract import ColumnDefinition, TableColumnContract
from .table_column_registry import table_column_contract_by_id

_PURPOSE_SUFFIX = {
    "display": "visible",
    "visible": "visible",
    "print": "printable",
    "printing": "printable",
    "export": "exportable",
    "excel": "exportable",
}


def normalize_purpose(purpose: str = "display") -> str:
    raw = str(purpose or "display").strip().lower()
    if raw in {"print", "printing"}:
        return "print"
    if raw in {"export", "excel", "xlsx", "csv"}:
        return "export"
    return "display"


def purpose_suffix(purpose: str = "display") -> str:
    return _PURPOSE_SUFFIX.get(str(purpose or "display").strip().lower(), "visible")


def default_enabled(column: ColumnDefinition, purpose: str = "display") -> bool:
    purpose = normalize_purpose(purpose)
    if purpose == "print":
        return bool(column.printable_default)
    if purpose == "export":
        return bool(column.exportable_default)
    return bool(column.visible_default or column.required)


def _settings_bool(key: str, default: bool) -> bool:
    if not key:
        return bool(default)
    try:
        from core.services.settings_service import settings_service
        return bool(settings_service.get_bool(key, bool(default)))
    except Exception:
        return bool(default)


def column_setting_key(column: ColumnDefinition, purpose: str = "display") -> str:
    suffix = purpose_suffix(purpose)
    base = str(column.settings_key or "").rstrip("/")
    return f"{base}/{suffix}" if base else ""


def column_enabled(column: ColumnDefinition, purpose: str = "display") -> bool:
    return _settings_bool(column_setting_key(column, purpose), default_enabled(column, purpose))


def columns_for_output(contract_or_id: TableColumnContract | str | None, purpose: str = "display") -> tuple[ColumnDefinition, ...]:
    """Return columns enabled for the requested output purpose.

    ``purpose='display'`` resolves visible columns. ``print`` and ``export`` use
    their dedicated contract flags and settings keys instead of the current table
    hidden state.  Required display columns stay visible by default.
    """
    contract = contract_or_id
    if isinstance(contract_or_id, str):
        contract = table_column_contract_by_id(contract_or_id)
    if contract is None:
        return tuple()
    return tuple(col for col in contract.columns if column_enabled(col, purpose))


def keys_for_output(contract_or_id: TableColumnContract | str | None, purpose: str = "display") -> tuple[str, ...]:
    return tuple(col.key for col in columns_for_output(contract_or_id, purpose))


def filter_dict_for_output(row: dict, contract_or_id: TableColumnContract | str | None, purpose: str = "display") -> dict:
    keys = keys_for_output(contract_or_id, purpose)
    return {key: row.get(key) for key in keys}


def ensure_known_keys(contract_or_id: TableColumnContract | str | None, keys: Iterable[str]) -> bool:
    contract = table_column_contract_by_id(contract_or_id) if isinstance(contract_or_id, str) else contract_or_id
    if contract is None:
        return False
    known = {col.key for col in contract.columns}
    return set(keys).issubset(known)
