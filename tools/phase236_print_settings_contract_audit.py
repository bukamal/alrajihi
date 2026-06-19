# -*- coding: utf-8 -*-
"""Phase 236 audit: visible print buttons must honor project printing settings.

The audit focuses on UI-facing print triggers. Backend compatibility helpers may
still expose preview/browser/pdf names, but visible buttons in views/features must
route to the single print path. Barcode printing must use project settings rather
than a per-dialog printer/PDF/image selector.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'tools' / 'audit_outputs'
OUT_JSON = OUT_DIR / 'phase236_print_settings_contract_audit.json'
OUT_MD = OUT_DIR / 'PHASE236_PRINT_SETTINGS_CONTRACT_AUDIT.md'

UI_ROOTS = [
    ROOT / 'alrajhi_client' / 'views',
    ROOT / 'alrajhi_client' / 'features',
]

ALLOW_PREVIEW_NAME_FILES = {
    'alrajhi_client/features/manufacturing/manufacturing_printing_bridge.py',
    'alrajhi_client/features/inventory/inventory_printing_bridge.py',
    'alrajhi_client/features/restaurant/restaurant_printing_bridge.py',
    'alrajhi_client/features/transactions/components/transaction_printing_bridge.py',
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace('\\', '/')


def iter_files():
    for base in UI_ROOTS:
        if base.exists():
            for path in base.rglob('*.py'):
                if '__pycache__' not in path.parts:
                    yield path


def add(findings, severity, path, line, message):
    findings.append({'severity': severity, 'path': path, 'line': line, 'message': message})


def line_no(text: str, pos: int) -> int:
    return text[:pos].count('\n') + 1


def main() -> int:
    findings = []
    for path in iter_files():
        r = rel(path)
        text = path.read_text(encoding='utf-8')
        # Visible print buttons must not install per-button mode menus.
        if r not in ALLOW_PREVIEW_NAME_FILES:
            for pat, msg in [
                (r'print_menu\s*=\s*QMenu', 'print button still builds a per-screen print menu'),
                (r'print_btn\.setMenu\((?!None\))', 'print button still attaches a menu'),
                (r'addAction\([^\n]*(preview|browser|direct|pdf)', 'print menu still exposes preview/browser/direct/pdf action'),
            ]:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    add(findings, 'high', r, line_no(text, m.start()), msg)

        # UI code outside bridge compatibility must not call preview/browser/pdf printing_service variants.
        if r not in ALLOW_PREVIEW_NAME_FILES:
            for m in re.finditer(r'printing_service\.[A-Za-z0-9_]*(preview|browser|pdf)\s*\(', text):
                add(findings, 'high', r, line_no(text, m.start()), 'UI print path bypasses single settings-driven print button')

        # Barcode dialogs must not select PDF/image printers or call raw barcode print directly.
        if r.endswith('batch_print_dialog.py'):
            for forbidden in ('PrinterManager', 'printer_combo', 'barcode_labels_print(', 'barcode_labels_pdf', 'barcode_labels_png', "'pdf'", '"pdf"', "'image'", '"image"'):
                if forbidden in text:
                    add(findings, 'high', r, 1, f'batch barcode print still exposes non-settings path: {forbidden}')
            if 'barcode_labels_print_settings(' not in text:
                add(findings, 'high', r, 1, 'batch barcode print does not use barcode_labels_print_settings')

    # Settings defaults and visible settings must not default to PDF pseudo-printers.
    settings_service = (ROOT / 'alrajhi_client/core/services/settings_service.py').read_text(encoding='utf-8')
    if "'barcode_default_printer': self.get('printing/barcode/default_printer', '')" not in settings_service:
        add(findings, 'high', 'alrajhi_client/core/services/settings_service.py', 1, 'barcode_default_printer default is not an empty/system printer setting')
    if 'print_button_mode' not in settings_service:
        add(findings, 'medium', 'alrajhi_client/core/services/settings_service.py', 1, 'printing settings do not expose print_button_mode')

    printing_service = (ROOT / 'alrajhi_client/printing/printing_service.py').read_text(encoding='utf-8')
    required = ['print_button_mode', '_print_button_render', 'settings_service.get_printing_settings', 'barcode_labels_print_settings']
    for token in required:
        if token not in printing_service:
            add(findings, 'high', 'alrajhi_client/printing/printing_service.py', 1, f'printing service missing settings contract token: {token}')
    if "return 'browser'" not in printing_service or "pdf" not in printing_service:
        add(findings, 'medium', 'alrajhi_client/printing/printing_service.py', 1, 'printing service does not sanitize legacy PDF/print modes to browser HTML')

    summary = {}
    for f in findings:
        summary[f['severity']] = summary.get(f['severity'], 0) + 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({'summary': summary, 'findings': findings}, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = ['# Phase 236 Print Settings Contract Audit', '', f'Summary: `{summary}`', '']
    for f in findings[:200]:
        rows.append(f"- **{f['severity']}** `{f['path']}:{f['line']}` — {f['message']}")
    OUT_MD.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print(json.dumps({'summary': summary, 'findings': len(findings)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
