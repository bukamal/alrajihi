from __future__ import annotations

from dataclasses import dataclass

from .transaction_column_schema import TransactionColumn
from ..i18n import tr


@dataclass(frozen=True)
class TransactionColumnPreset:
    """Named line-grid preset shared by invoices, returns, POS, and restaurant docs."""

    name: str
    title_key: str
    keys: tuple[str, ...]

    @property
    def title(self) -> str:
        return tr(self.title_key)


# Presets use stable column keys.  Missing keys are ignored by the grid, so the
# same preset name can be applied to sales and purchase schemas safely.
_PRESETS: tuple[TransactionColumnPreset, ...] = (
    TransactionColumnPreset(
        "compact",
        "transaction_preset_compact",
        ("row", "item", "unit", "qty", "price", "cost", "total"),
    ),
    TransactionColumnPreset(
        "cashier",
        "transaction_preset_cashier",
        ("row", "barcode", "item", "qty", "price", "total"),
    ),
    TransactionColumnPreset(
        "accountant",
        "transaction_preset_accountant",
        ("row", "original_invoice", "barcode", "item", "unit", "qty", "price", "cost", "discount", "tax", "total", "notes"),
    ),
    TransactionColumnPreset(
        "warehouse",
        "transaction_preset_warehouse",
        ("row", "barcode", "item", "unit", "qty", "available", "original_qty", "previous_qty", "returnable_qty", "batch", "expiry", "total"),
    ),
    TransactionColumnPreset(
        "manager",
        "transaction_preset_manager",
        ("row", "original_invoice", "barcode", "item", "unit", "qty", "available", "original_qty", "previous_qty", "returnable_qty", "price", "cost", "discount", "tax", "reason", "restock", "batch", "expiry", "total", "notes"),
    ),
)

PRESET_BY_NAME = {preset.name: preset for preset in _PRESETS}
DEFAULT_PRESET = "manager"
RESPONSIVE_COMPACT_PRESET = "compact"


def preset_names() -> list[str]:
    return [preset.name for preset in _PRESETS]


def preset_title(name: str) -> str:
    return PRESET_BY_NAME.get(name, PRESET_BY_NAME[DEFAULT_PRESET]).title


def presets() -> list[TransactionColumnPreset]:
    return list(_PRESETS)


def visible_keys_for_preset(name: str, columns: list[TransactionColumn]) -> set[str]:
    preset = PRESET_BY_NAME.get(name) or PRESET_BY_NAME[DEFAULT_PRESET]
    schema_keys = {column.key for column in columns}
    required = {column.key for column in columns if column.required}
    return (set(preset.keys) & schema_keys) | required
