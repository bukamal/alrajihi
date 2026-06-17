#!/usr/bin/env python3
"""Architecture boundary guard for the Alrajhi client and server API.

Phase 22 rule:
- UI/views, core/services, currency.py, and main.py must not import database package, database.dao or database.repositories directly.
- Direct DatabaseConnection access is forbidden in protected layers and must remain behind gateways/services.
- Direct SQL execution is forbidden in protected layers.
- UI/main must not import core.server_control directly; use SystemService.

Run from the repository root:
    python tools/architecture_guard.py
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_DIRS = [
    ROOT / "alrajhi_client" / "views",
    ROOT / "alrajhi_client" / "core" / "services",
    ROOT / "alrajhi_server" / "api",
    ROOT / "alrajhi_server" / "services" / "http_routes",
]
CHECK_FILES = [
    ROOT / "alrajhi_client" / "currency.py",
    ROOT / "alrajhi_client" / "main.py",
]

# DAO access must be behind gateways/local/* only.
FORBIDDEN_DAO_PREFIXES = (
    "database.dao",
    "alrajhi_client.database.dao",
)

FORBIDDEN_REPOSITORY_PREFIXES = (
    "database.repositories",
    "alrajhi_client.database.repositories",
)

# Existing technical-debt exceptions.  These are not ideal; they are tracked so
# new direct DB access cannot silently enter views/services.
LEGACY_DB_ALLOWLIST = set()

LEGACY_SQL_ALLOWLIST = set()

DATABASE_CONNECTION_MODULES = {
    "database.connection",
    "alrajhi_client.database.connection",
    "database.connection_rest",
    "alrajhi_client.database.connection_rest",
    "alrajhi_server.database.connection",
}

SQL_METHOD_NAMES = {"execute", "executemany", "executescript", "query"}
FORBIDDEN_SERVER_CONTROL_MODULES = {
    "core.server_control",
    "alrajhi_client.core.server_control",
}

FORBIDDEN_DATABASE_ROOT_MODULES = {
    "database",
    "alrajhi_client.database",
}

FORBIDDEN_SERVER_API_REPOSITORY_MODULES = {
    "alrajhi_server.repositories.legacy_sql_repository",
}

ALLOWED_DATABASE_ROOT_NAMES = set()

# Views should not instantiate repositories through database/__init__.py.
# Repository access belongs behind core services and gateways.
FORBIDDEN_VIEW_DATABASE_IMPORTS = {
    "UserRepository",
    "AuditRepository",
    "CustomerRepository",
    "SupplierRepository",
    "ItemRepository",
    "CategoryRepository",
    "InvoiceRepository",
    "VoucherRepository",
    "ExpenseRepository",
}

@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    import_text: str
    reason: str

    def format(self) -> str:
        rel = self.path.relative_to(ROOT).as_posix()
        return f"{rel}:{self.line}: {self.reason}: {self.import_text}"


def module_matches(module: str | None, prefixes: tuple[str, ...]) -> bool:
    if not module:
        return False
    return any(module == p or module.startswith(p + ".") for p in prefixes)


def import_name(node: ast.AST) -> str:
    if isinstance(node, ast.Import):
        return ", ".join(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        names = ", ".join(alias.name for alias in node.names)
        dots = "." * node.level
        return f"from {dots}{node.module or ''} import {names}"
    return "<unknown import>"


def scan_file(path: Path) -> list[Violation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [Violation(path, exc.lineno or 0, "<parse>", f"syntax error: {exc.msg}")]

    violations: list[Violation] = []
    rel = path.relative_to(ROOT).as_posix()

    SQL_KEYWORDS = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "PRAGMA")

    for node in ast.walk(tree):
        if (rel.startswith("alrajhi_server/api/") or rel.startswith("alrajhi_server/services/http_routes/")) and isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = " ".join(node.value.upper().split())
            if any(text.startswith(keyword + " ") for keyword in SQL_KEYWORDS):
                violations.append(Violation(path, getattr(node, "lineno", 0), "<sql literal>", "SQL literals are forbidden in server API/service HTTP wrappers; move data access behind service/repository layers"))

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in SQL_METHOD_NAMES:
                if rel not in LEGACY_SQL_ALLOWLIST:
                    violations.append(Violation(path, getattr(node, "lineno", 0), f".{func.attr}(...)" , "direct SQL execution is forbidden outside gateways/database layers"))

        if isinstance(node, ast.Import):
            for alias in node.names:
                if module_matches(alias.name, FORBIDDEN_DAO_PREFIXES):
                    violations.append(Violation(path, node.lineno, import_name(node), "direct DAO import is forbidden outside gateways"))
                if module_matches(alias.name, FORBIDDEN_REPOSITORY_PREFIXES):
                    violations.append(Violation(path, node.lineno, import_name(node), "direct repository import is forbidden outside gateways"))
                if alias.name in DATABASE_CONNECTION_MODULES and rel not in LEGACY_DB_ALLOWLIST:
                    violations.append(Violation(path, node.lineno, import_name(node), "direct DatabaseConnection import requires explicit allow-list"))
                if alias.name in FORBIDDEN_SERVER_CONTROL_MODULES:
                    violations.append(Violation(path, node.lineno, import_name(node), "direct server_control import is forbidden in UI/application entrypoints; use SystemService"))
                if alias.name in FORBIDDEN_SERVER_API_REPOSITORY_MODULES and (rel.startswith("alrajhi_server/api/") or rel.startswith("alrajhi_server/services/http_routes/")):
                    violations.append(Violation(path, node.lineno, import_name(node), "server API must not depend on LegacySqlRepository; use a domain repository"))
                if alias.name in FORBIDDEN_DATABASE_ROOT_MODULES:
                    violations.append(Violation(path, node.lineno, import_name(node), "direct database package import is forbidden in protected layers; use Service/Gateway"))

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module_matches(module, FORBIDDEN_DAO_PREFIXES):
                violations.append(Violation(path, node.lineno, import_name(node), "direct DAO import is forbidden outside gateways"))
            if module_matches(module, FORBIDDEN_REPOSITORY_PREFIXES):
                violations.append(Violation(path, node.lineno, import_name(node), "direct repository import is forbidden outside gateways"))
            if module in DATABASE_CONNECTION_MODULES and rel not in LEGACY_DB_ALLOWLIST:
                violations.append(Violation(path, node.lineno, import_name(node), "direct DatabaseConnection import requires explicit allow-list"))
            if module in FORBIDDEN_SERVER_CONTROL_MODULES:
                violations.append(Violation(path, node.lineno, import_name(node), "direct server_control import is forbidden in UI/application entrypoints; use SystemService"))
            if module in FORBIDDEN_SERVER_API_REPOSITORY_MODULES and (rel.startswith("alrajhi_server/api/") or rel.startswith("alrajhi_server/services/http_routes/")):
                violations.append(Violation(path, node.lineno, import_name(node), "server API must not depend on LegacySqlRepository; use a domain repository"))
            if module in FORBIDDEN_DATABASE_ROOT_MODULES:
                imported = {alias.name for alias in node.names}
                if imported - ALLOWED_DATABASE_ROOT_NAMES:
                    violations.append(Violation(path, node.lineno, import_name(node), "direct database package import is forbidden in protected layers; use Service/Gateway"))
            if rel.startswith("alrajhi_client/views/") and module in {"database", "alrajhi_client.database"}:
                imported = {alias.name for alias in node.names}
                forbidden = imported & FORBIDDEN_VIEW_DATABASE_IMPORTS
                if forbidden:
                    violations.append(Violation(path, node.lineno, import_name(node), "direct repository import in views is forbidden"))

    return violations


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in CHECK_DIRS:
        if directory.exists():
            files.extend(sorted(directory.rglob("*.py")))
    files.extend(path for path in CHECK_FILES if path.exists())
    return files


def main() -> int:
    violations: list[Violation] = []
    for path in iter_python_files():
        violations.extend(scan_file(path))

    if violations:
        print("Architecture guard failed.\n")
        for violation in violations:
            print(violation.format())
        print("\nMove data access behind Service/Gateway, or document a temporary legacy exception explicitly.")
        return 1

    print("Architecture guard passed: no forbidden DAO/repository/SQL access in protected client/server layers.")
    print(f"Tracked legacy DatabaseConnection exceptions: {len(LEGACY_DB_ALLOWLIST)} files.")
    print(f"Tracked legacy SQL execution exceptions: {len(LEGACY_SQL_ALLOWLIST)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
