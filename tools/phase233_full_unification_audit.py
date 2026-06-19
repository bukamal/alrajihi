# -*- coding: utf-8 -*-
"""Phase 233 full unification audit.

Blocks regressions in the three project-wide UX contracts:
1) UI money conversion must not hard-code USD; use currency.storage_currency(),
   currency.to_display(), currency.from_display(), or currency.format_base_amount().
2) Qt printing primitives must remain inside alrajhi_client/printing only.
3) Visible UI text must pass through translate()/tr() across the client.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VISIBLE_CALLS = {
    "QLabel", "QPushButton", "QAction", "QCheckBox", "QRadioButton", "QGroupBox",
    "setWindowTitle", "setText", "setToolTip", "addTab", "addItem", "addAction", "addMenu",
}
AR_RE = re.compile(r"[\u0600-\u06FF]")
EN_WORD_RE = re.compile(
    r"\b(?:Save|Print|Export|Close|Refresh|Search|Total|Amount|Date|Status|Name|"
    r"Customer|Supplier|Invoice|Voucher|Expense|Cashbox|Bank|Dashboard|Settings|"
    r"View|Compact|Comfortable|Touch|Row density)\b"
)
PRINT_PATTERNS = ("QPrinter(", "QPrintDialog", "QPrintPreviewDialog", "QTextDocument")
MONEY_FIELDS = ("amount", "balance", "total", "price", "cost", "paid", "remaining", "value")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_translated(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node.func) in {"translate", "tr", "_tr", "self.tr"}


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str))
    return None


def _interesting_visible(text: str) -> bool:
    t = text.strip()
    if not t or len(t) <= 1:
        return False
    if t.startswith(("Q", ".", "#", "rgba", "background", "border", "font-")):
        return False
    if "{" in t and "}" in t and ";" in t:
        return False
    return bool(AR_RE.search(t) or EN_WORD_RE.search(t))


def _ast_findings(path: Path) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [{"severity": "high", "area": "parse", "file": rel(path), "line": 0, "message": str(exc)}]
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name == "convert":
            # Attribute call: currency.convert(...).  Any literal USD here is a UI/base-currency leak.
            if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "currency":
                for arg in node.args[1:3]:
                    if isinstance(arg, ast.Constant) and arg.value == "USD":
                        findings.append({
                            "severity": "high", "area": "currency", "file": rel(path), "line": getattr(node, "lineno", 0),
                            "message": "currency.convert uses hard-coded USD in UI/client code.",
                        })
        if name in VISIBLE_CALLS:
            for arg in list(node.args)[:2]:
                if _is_translated(arg):
                    continue
                text = _literal_text(arg)
                if text and _interesting_visible(text):
                    findings.append({
                        "severity": "high", "area": "i18n", "file": rel(path), "line": getattr(node, "lineno", 0),
                        "message": "Visible UI text is not routed through translate()/tr().", "text": text[:120],
                    })
    return findings


def audit() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for path in CLIENT.rglob("*.py"):
        if "__pycache__" in path.parts or path.as_posix().endswith("i18n/translator.py"):
            continue
        findings.extend(_ast_findings(path))
        text = path.read_text(encoding="utf-8", errors="ignore")
        file_rel = rel(path)
        # Currency lists/settings/storage/migration code may define currency codes.
        # UI-facing modules must not hard-code USD around monetary display or input.
        ui_currency_scope = (
            file_rel.startswith("alrajhi_client/views/")
            or file_rel.startswith("alrajhi_client/features/")
            or file_rel.startswith("alrajhi_client/ui/")
        )
        if ui_currency_scope and ("'USD'" in text or '"USD"' in text) and "views/widgets/settings_widget.py" not in file_rel:
            money_hint = any(field in text.lower() for field in MONEY_FIELDS)
            if money_hint and "currency.storage_currency()" not in text and "currency.to_display" not in text and "currency.from_display" not in text:
                findings.append({"severity": "medium", "area": "currency", "file": file_rel, "line": 0, "message": "Currency code literal remains near money-related UI code."})
        if any(pat in text for pat in PRINT_PATTERNS):
            if not file_rel.startswith("alrajhi_client/printing/"):
                findings.append({"severity": "high", "area": "printing", "file": file_rel, "line": 0, "message": "Qt printing primitive outside the centralized printing package."})
    printing_service = (CLIENT / "printing" / "printing_service.py").read_text(encoding="utf-8")
    if "def render_html(" not in printing_service:
        findings.append({"severity": "high", "area": "printing", "file": "alrajhi_client/printing/printing_service.py", "line": 0, "message": "printing_service.render_html is required for HTML print unification."})
    summary: dict[str, int] = {}
    for f in findings:
        summary[f["severity"]] = summary.get(f["severity"], 0) + 1
    report = {
        "phase": 233,
        "title": "Full UI currency/printing/i18n unification audit",
        "summary": summary,
        "findings": findings,
    }
    (OUT_DIR / "phase233_full_unification_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Phase 233 Full Unification Audit", "", "## Summary"]
    for key in ("high", "medium", "low"):
        lines.append(f"- {key}: {summary.get(key, 0)}")
    lines += ["", "## Findings"]
    for f in findings[:160]:
        lines.append(f"- [{f['severity']}] {f['area']} — {f['message']} (`{f.get('file')}`:{f.get('line')})")
    (OUT_DIR / "PHASE233_FULL_UNIFICATION_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = audit()
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
