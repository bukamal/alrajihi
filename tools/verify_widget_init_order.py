# -*- coding: utf-8 -*-
"""Guard against QWidget methods before superclass initialization."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "alrajhi_client"

WIDGET_METHODS = {
    "setLayoutDirection",
    "setStyleSheet",
    "setWindowTitle",
    "setWindowIcon",
    "setObjectName",
    "setMinimumSize",
    "resize",
}


def _is_super_init(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "__init__":
        return False
    value = func.value
    if isinstance(value, ast.Call) and getattr(value.func, "id", None) == "super":
        return True
    if isinstance(value, ast.Name) and value.id in {"QWidget", "QDialog", "QMainWindow", "BaseWidget"}:
        return True
    return False


def main() -> int:
    violations = []
    for path in TARGET.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"]:
                super_line = None
                for stmt in fn.body:
                    for node in ast.walk(stmt):
                        if isinstance(node, ast.Call) and _is_super_init(node):
                            super_line = stmt.lineno
                            break
                    if super_line:
                        break
                if not super_line:
                    continue
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        if node.func.attr in WIDGET_METHODS and node.lineno < super_line:
                            violations.append(f"{path.relative_to(ROOT)}:{node.lineno} {cls.name}.{node.func.attr} before super().__init__")
    if violations:
        print("Widget init-order violations:")
        print("\n".join(violations))
        return 1
    print("widget init-order guard passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
