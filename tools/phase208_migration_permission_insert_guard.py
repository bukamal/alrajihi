#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 208 guard: permission INSERT statements must match permissions(key,module,action,description).

The startup failure fixed in Phase 208 came from a malformed migration row that
inserted many permission keys into an INSERT that declared only four columns.
This guard statically validates permission INSERT statements in client/server
migrations and verifies finance permissions are inserted as separate rows.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = [
    ROOT / "alrajhi_client" / "database" / "migrations.py",
    ROOT / "alrajhi_server" / "database" / "migrations.py",
]

SINGLE_INSERT_RE = re.compile(
    r"INSERT\s+OR\s+IGNORE\s+INTO\s+permissions\(key,module,action,description\)\s+VALUES\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)

# Multi-row VALUES are legal when each tuple has exactly four string literals.
MULTI_VALUES_RE = re.compile(
    r"INSERT\s+OR\s+IGNORE\s+INTO\s+permissions\(key,module,action,description\)\s+VALUES\s*(.*?);",
    re.IGNORECASE | re.DOTALL,
)
TUPLE_RE = re.compile(r"\(([^()]+)\)")
STRING_RE = re.compile(r"'([^']*)'")

REQUIRED_FINANCE_PERMISSION_ROWS = {
    "finance.use": ("finance", "use"),
    "finance.cashbox.create": ("finance", "cashbox_create"),
    "finance.cashbox.edit": ("finance", "cashbox_edit"),
    "finance.cashbox.archive": ("finance", "cashbox_archive"),
    "finance.bank.create": ("finance", "bank_create"),
    "finance.bank.edit": ("finance", "bank_edit"),
    "finance.bank.archive": ("finance", "bank_archive"),
    "finance.movements.view": ("finance", "movements_view"),
    "finance.shifts.view": ("finance", "shifts_view"),
    "finance.voucher.view": ("finance", "voucher_view"),
    "finance.voucher.create": ("finance", "voucher_create"),
    "finance.voucher.edit": ("finance", "voucher_edit"),
    "finance.voucher.delete": ("finance", "voucher_delete"),
    "finance.voucher.print": ("finance", "voucher_print"),
}

REQUIRED_INVENTORY_PRINT_ROW = "INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.print','inventory','print','Print inventory and warehouse documents');"


def _validate_permission_inserts(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []

    for match in MULTI_VALUES_RE.finditer(text):
        values_blob = match.group(1)
        tuples = TUPLE_RE.findall(values_blob)
        if not tuples:
            failures.append(f"{path}: permission INSERT without value tuple at offset {match.start()}")
            continue
        for tup in tuples:
            strings = STRING_RE.findall(tup)
            if len(strings) != 4:
                failures.append(
                    f"{path}: permissions insert tuple has {len(strings)} values, expected 4: ({tup[:160]})"
                )

    if "'inventory.print', 'finance.use'" in text or "'inventory.print','finance.use'" in text:
        failures.append(f"{path}: finance permission keys are still merged into inventory.print INSERT")

    if REQUIRED_INVENTORY_PRINT_ROW not in text:
        failures.append(f"{path}: missing normalized inventory.print permission row")

    for key, (module, action) in REQUIRED_FINANCE_PERMISSION_ROWS.items():
        expected_prefix = f"INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('{key}','{module}','{action}',"
        if expected_prefix not in text:
            failures.append(f"{path}: missing separate permission row for {key}")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    for path in MIGRATIONS:
        _validate_permission_inserts(path)
    print("phase208_migration_permission_insert_guard passed")


if __name__ == "__main__":
    main()
