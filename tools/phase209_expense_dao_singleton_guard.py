#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 209 guard: legacy DAO singleton compatibility for dashboard expenses."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def module_assigns_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return True
    return False


def class_has_methods(tree: ast.AST, class_name: str, methods: set[str]) -> bool:
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            found = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
            return methods.issubset(found)
    return False


def main() -> None:
    expense_path = 'alrajhi_client/database/dao/expense_dao.py'
    expense_tree = ast.parse(read(expense_path), filename=expense_path)
    require(module_assigns_name(expense_tree, 'expense_dao'), 'expense_dao.py must expose expense_dao singleton')
    require(class_has_methods(expense_tree, 'ExpenseDAO', {'get_all', 'add', 'delete'}), 'ExpenseDAO must expose get_all/add/delete')

    reporting_path = 'alrajhi_client/database/dao/reporting_dao.py'
    reporting_tree = ast.parse(read(reporting_path), filename=reporting_path)
    require(module_assigns_name(reporting_tree, 'reporting_dao'), 'reporting_dao.py must expose reporting_dao singleton because lazy exports reference it')

    dao_init = read('alrajhi_client/database/dao/__init__.py')
    require("'expense_dao': ('database.dao.expense_dao', 'expense_dao')" in dao_init, 'database.dao lazy map must point expense_dao to singleton attr')
    require("'reporting_dao': ('database.dao.reporting_dao', 'reporting_dao')" in dao_init, 'database.dao lazy map must point reporting_dao to singleton attr')

    gateway = read('alrajhi_client/gateways/local/expense_gateway.py')
    require('from database import expense_dao' in gateway, 'LocalExpenseGateway should keep importing compatibility expense_dao singleton')
    require('expense_dao.get_all' in gateway, 'LocalExpenseGateway list() must call expense_dao.get_all')

    print('phase209_expense_dao_singleton_guard: OK')


if __name__ == '__main__':
    main()
