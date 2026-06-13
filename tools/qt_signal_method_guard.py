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
        self.refs: list[tuple[str, int, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        methods = {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.methods_by_class[node.name] = methods
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
        for cls, line, meth in v.refs:
            methods = v.methods_by_class.get(cls, set())
            if meth not in methods:
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
