#!/usr/bin/env python3
"""Detect print QAction wiring that references missing local methods."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'alrajhi_client' / 'views'
PRINT_METHOD_PREFIXES = ('print_', 'open_', 'save_', 'export_', 'direct_')
PRINT_TOKENS = ('print', 'طباعة', 'pdf', 'html', 'browser')

class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.class_stack: list[ast.ClassDef] = []
        self.methods_by_class: dict[str, set[str]] = {}
        self.refs: list[tuple[str, int, str, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.methods_by_class[node.name] = {
            n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.class_stack.append(node)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'connect' and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name) and arg.value.id == 'self':
                target = arg.attr
                src = ast.unparse(node.func.value) if hasattr(ast, 'unparse') else ''
                is_print_src = any(tok in src.lower() for tok in PRINT_TOKENS)
                is_print_target = target.startswith(PRINT_METHOD_PREFIXES)
                if self.class_stack and (is_print_src or is_print_target):
                    self.refs.append((self.class_stack[-1].name, node.lineno, target, src))
        self.generic_visit(node)

def main() -> int:
    failures: list[str] = []
    for path in VIEWS.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        v = Visitor(path)
        v.visit(tree)
        for cls, line, meth, src in v.refs:
            if meth not in v.methods_by_class.get(cls, set()):
                failures.append(f'{path.relative_to(ROOT)}:{line}: {cls}.{src}.connect(self.{meth}) but method is missing')
    if failures:
        print('Print action guard failed:')
        for f in failures:
            print(' -', f)
        return 1
    print('Print action guard: PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
