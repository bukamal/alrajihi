# -*- coding: utf-8 -*-
"""Informational UI language audit.

This audit does not fail CI. It lists likely visible literals that should be
migrated to translate()/tr() over time.  It intentionally ignores logs, SQL,
CSS, object names, and model constants.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [ROOT / 'alrajhi_client' / 'views', ROOT / 'alrajhi_client' / 'features']
OUT_DIR = ROOT / 'tools' / 'audit_outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
VISIBLE_CALLS = {'QLabel', 'QPushButton', 'QAction', 'QCheckBox', 'QRadioButton', 'QGroupBox', 'setWindowTitle', 'setText', 'setToolTip', 'addTab', 'addItem'}
AR_RE = re.compile(r'[\u0600-\u06FF]')
EN_WORD_RE = re.compile(r'\b(?:Save|Print|Export|Close|Refresh|Search|Total|Amount|Date|Status|Name|Customer|Supplier|Invoice|Voucher|Expense|Cashbox|Bank|Dashboard|Settings)\b')


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ''


def _is_translated_arg(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        return name in {'translate', 'tr', '_tr', 'self.tr'}
    if isinstance(node, ast.BinOp):
        return _is_translated_arg(node.left) or _is_translated_arg(node.right)
    if isinstance(node, ast.JoinedStr):
        return False
    return False


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        chunks = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                chunks.append(part.value)
        return ''.join(chunks)
    return None


def _interesting(text: str) -> bool:
    t = text.strip()
    if not t or len(t) <= 1:
        return False
    if t.startswith(('#', '.', 'Q', 'rgba', 'font-', 'background', 'border')):
        return False
    if '{' in t and '}' in t and ';' in t:
        return False
    return bool(AR_RE.search(t) or EN_WORD_RE.search(t))


def audit_file(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except Exception:
        return []
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name not in VISIBLE_CALLS:
            continue
        for arg in list(node.args)[:2]:
            if _is_translated_arg(arg):
                continue
            text = _literal_text(arg)
            if text and _interesting(text):
                findings.append({'file': str(path.relative_to(ROOT)), 'line': getattr(node, 'lineno', 0), 'call': name, 'text': text.strip()[:120]})
    return findings


def run() -> dict:
    findings = []
    for root in SCAN_ROOTS:
        for path in root.rglob('*.py'):
            if '__pycache__' in path.parts:
                continue
            findings.extend(audit_file(path))
    by_file = {}
    for f in findings:
        by_file.setdefault(f['file'], 0)
        by_file[f['file']] += 1
    top_files = sorted(by_file.items(), key=lambda kv: kv[1], reverse=True)[:20]
    report = {
        'phase': 232,
        'title': 'Project UI language audit',
        'total_findings': len(findings),
        'top_files': [{'file': f, 'count': c} for f, c in top_files],
        'sample_findings': findings[:100],
        'note': 'Informational only. Some findings are valid domain values; migrate user-visible literals gradually to translate()/tr().',
    }
    (OUT_DIR / 'phase232_project_language_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    md = ['# Phase 232 Project UI Language Audit', '', f"Total likely visible literals: `{len(findings)}`", '', 'Top files:']
    for f, c in top_files:
        md.append(f'- `{f}`: {c}')
    md.append('')
    md.append('This is informational, not a CI blocker. It identifies screens that still need gradual i18n cleanup.')
    (OUT_DIR / 'PHASE232_PROJECT_LANGUAGE_AUDIT.md').write_text('\n'.join(md), encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False))
