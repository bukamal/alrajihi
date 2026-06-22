# -*- coding: utf-8 -*-
"""Runtime helpers for unified column settings.

Phase 342 wires the column contracts from the hidden registry into both the
settings UI and runtime table column customizers.  The helpers stay PyQt-free
so guards and services can validate/apply preferences without importing widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

from workspace.tables.column_contract import ColumnDefinition, TableColumnContract
from workspace.tables.column_output import column_setting_key, default_enabled
from workspace.tables.table_column_registry import table_column_contract_by_id

COLUMN_PURPOSES: tuple[str, ...] = ("display", "print", "export")


@dataclass(frozen=True)
class ColumnPreferenceState:
    column_key: str
    label_key: str
    required: bool
    display: bool
    print: bool
    export: bool
    settings: Mapping[str, str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "column_key": self.column_key,
            "label_key": self.label_key,
            "required": self.required,
            "display": self.display,
            "print": self.print,
            "export": self.export,
            "settings": dict(self.settings),
        }


def _settings_bool(key: str, default: bool) -> bool:
    if not key:
        return bool(default)
    try:
        from core.services.settings_service import settings_service
        return bool(settings_service.get_bool(key, bool(default)))
    except Exception:
        return bool(default)


def _settings_set(key: str, value: bool) -> None:
    if not key:
        return
    from core.services.settings_service import settings_service
    settings_service.set(key, "true" if value else "false")


def resolve_contract(contract_or_id: TableColumnContract | str | None) -> TableColumnContract | None:
    if isinstance(contract_or_id, TableColumnContract):
        return contract_or_id
    if contract_or_id:
        return table_column_contract_by_id(str(contract_or_id))
    return None


def column_state(column: ColumnDefinition) -> ColumnPreferenceState:
    settings = {purpose: column_setting_key(column, purpose) for purpose in COLUMN_PURPOSES}
    return ColumnPreferenceState(
        column_key=column.key,
        label_key=column.label_key,
        required=bool(column.required),
        display=True if column.required else _settings_bool(settings["display"], default_enabled(column, "display")),
        print=_settings_bool(settings["print"], default_enabled(column, "print")),
        export=_settings_bool(settings["export"], default_enabled(column, "export")),
        settings=settings,
    )


def contract_column_states(contract_or_id: TableColumnContract | str | None) -> tuple[ColumnPreferenceState, ...]:
    contract = resolve_contract(contract_or_id)
    if contract is None:
        return tuple()
    return tuple(column_state(col) for col in contract.columns)


def set_column_preference(column: ColumnDefinition, purpose: str, enabled: bool) -> None:
    purpose = str(purpose or "display").strip().lower()
    if purpose in {"visible", "screen"}:
        purpose = "display"
    if purpose in {"printing"}:
        purpose = "print"
    if purpose in {"excel", "csv", "xlsx"}:
        purpose = "export"
    if purpose not in COLUMN_PURPOSES:
        raise ValueError(f"Unsupported column purpose: {purpose}")
    if purpose == "display" and column.required:
        enabled = True
    _settings_set(column_setting_key(column, purpose), bool(enabled))


def save_contract_column_preferences(contract_or_id: TableColumnContract | str | None, values: Mapping[str, Mapping[str, bool]]) -> None:
    """Persist visible/printable/exportable preferences for one contract.

    ``values`` maps column_key -> {display: bool, print: bool, export: bool}.
    Required display columns are forced visible even if the caller sends false.
    """
    contract = resolve_contract(contract_or_id)
    if contract is None:
        raise ValueError("Unknown column contract")
    by_key = {col.key: col for col in contract.columns}
    for column_key, prefs in (values or {}).items():
        column = by_key.get(str(column_key))
        if column is None:
            continue
        for purpose in COLUMN_PURPOSES:
            if purpose in prefs:
                set_column_preference(column, purpose, bool(prefs[purpose]))
    try:
        from core.services.settings_service import settings_service
        settings_service.clear_cache()
    except Exception:
        pass


def reset_contract_column_preferences(contract_or_id: TableColumnContract | str | None) -> None:
    contract = resolve_contract(contract_or_id)
    if contract is None:
        raise ValueError("Unknown column contract")
    for column in contract.columns:
        set_column_preference(column, "display", default_enabled(column, "display"))
        set_column_preference(column, "print", default_enabled(column, "print"))
        set_column_preference(column, "export", default_enabled(column, "export"))
    try:
        from core.services.settings_service import settings_service
        settings_service.clear_cache()
    except Exception:
        pass


def reset_all_column_preferences(contracts: Iterable[TableColumnContract]) -> None:
    for contract in contracts:
        reset_contract_column_preferences(contract)


def display_keys_for_contract(contract_or_id: TableColumnContract | str | None) -> tuple[str, ...]:
    return tuple(state.column_key for state in contract_column_states(contract_or_id) if state.display)


def validate_column_preference_runtime() -> Dict[str, list[str]]:
    """Validate that every registered column has runtime preference keys."""
    from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS
    issues: Dict[str, list[str]] = {}
    for contract_id, contract in sorted(TABLE_COLUMN_CONTRACTS.items()):
        if not contract.settings_prefix.startswith("ui/columns/"):
            issues.setdefault("contract_prefix", []).append(contract_id)
        for column in contract.columns:
            state = column_state(column)
            missing = [purpose for purpose, key in state.settings.items() if not key]
            if missing:
                issues.setdefault("missing_keys", []).append(f"{contract_id}.{column.key}:{','.join(missing)}")
            if column.required and not state.display:
                issues.setdefault("required_hidden", []).append(f"{contract_id}.{column.key}")
    return issues


__all__ = [
    "COLUMN_PURPOSES",
    "ColumnPreferenceState",
    "column_state",
    "contract_column_states",
    "display_keys_for_contract",
    "reset_all_column_preferences",
    "reset_contract_column_preferences",
    "resolve_contract",
    "save_contract_column_preferences",
    "set_column_preference",
    "validate_column_preference_runtime",
]
