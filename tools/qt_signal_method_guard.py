#!/usr/bin/env python3
"""Detect QAction/Qt signal connections that reference missing self methods."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'alrajhi_client' / 'views'

class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.class_stack: list[ast.ClassDef] = []
        self.methods_by_class: dict[str, set[str]] = {}
        self.bases_by_class: dict[str, list[str]] = {}
        self.refs: list[tuple[str, int, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        methods = {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.methods_by_class[node.name] = methods
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
        self.bases_by_class[node.name] = bases
        self.class_stack.append(node)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_Call(self, node: ast.Call):
        # Match something.connect(self.method)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'connect' and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name) and arg.value.id == 'self':
                if self.class_stack:
                    self.refs.append((self.class_stack[-1].name, node.lineno, arg.attr))
        self.generic_visit(node)

def main() -> int:
    failures: list[str] = []
    for path in VIEWS.rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError as exc:
            failures.append(f'{path}: syntax error: {exc}')
            continue
        v = Visitor(path)
        v.visit(tree)
        inherited_qt_methods = {'accept', 'reject', 'showMinimized', 'showNormal', 'showMaximized', 'close'}
        inherited_mixin_methods = {'_on_add_shortcut', '_on_edit_shortcut', '_on_delete_shortcut', '_on_refresh_shortcut', '_on_print_shortcut', '_on_export_shortcut', '_on_double_click', '_on_selection_changed'}
        def has_method(class_name: str, method: str, seen: set[str] | None = None) -> bool:
            seen = seen or set()
            if class_name in seen:
                return False
            seen.add(class_name)
            if method in v.methods_by_class.get(class_name, set()):
                return True
            if method in inherited_qt_methods:
                return True
            if method in inherited_mixin_methods:
                return True
            for base in v.bases_by_class.get(class_name, []):
                if has_method(base, method, seen):
                    return True
            return False
        for cls, line, meth in v.refs:
            if not has_method(cls, meth):
                failures.append(f'{path.relative_to(ROOT)}:{line}: {cls}.connect(self.{meth}) but method is missing')
    if failures:
        print('Qt signal method guard failed:')
        for f in failures:
            print(' -', f)
        return 1
    print('Qt signal method guard: PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
