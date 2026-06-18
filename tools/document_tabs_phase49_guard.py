#!/usr/bin/env python3
"""Guard for Phase 49 return document-tab refactor.

Returns must no longer use the generic DialogDocumentTab bridge.  They must
expose a feature-level document tab with componentized header/lines/settlement
and explicit workspace save/print/export commands while preserving unit-aware
return payloads.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'alrajhi_client/features/returns/return_editor_tabs.py',
    'alrajhi_client/features/returns/components/return_header.py',
    'alrajhi_client/features/returns/components/return_lines.py',
    'alrajhi_client/features/returns/components/return_settlement.py',
    'alrajhi_client/features/returns/components/return_actions.py',
]


def fail(messages: list[str]) -> int:
    print('Phase 49 return document-tabs guard failed:')
    for message in messages:
        print(f' - {message}')
    return 1


def main() -> int:
    failures: list[str] = []
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.exists():
            failures.append(f'missing {rel}')
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            failures.append(f'syntax error in {rel}:{exc.lineno}: {exc.msg}')

    editor = (ROOT / 'alrajhi_client/features/returns/return_editor_tabs.py').read_text(encoding='utf-8')
    forbidden = ['DialogDocumentTab', "from features.dialog_documents", 'dialog_cls']
    for token in forbidden:
        if token in editor:
            failures.append(f'return editor still uses generic dialog bridge token: {token}')

    required_tokens = [
        'class _ReturnDocumentMixin',
        'ReturnHeaderComponent',
        'ReturnLinesComponent',
        'ReturnSettlementComponent',
        'workspace_save',
        'workspace_print',
        'workspace_export',
        'document_payload',
        'dirtyChanged',
        'saved.emit',
    ]
    for token in required_tokens:
        if token not in editor:
            failures.append(f'return editor missing token: {token}')

    lines = (ROOT / 'alrajhi_client/features/returns/components/return_lines.py').read_text(encoding='utf-8')
    for token in ('_ret_unit_price_usd_for_factor', '_ret_returnable_base', 'quantity_in_base', 'conversion_factor'):
        if token not in lines:
            failures.append(f'return lines component missing unit-aware token: {token}')

    main_window = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    if 'features.returns' not in main_window or 'open_return_document' not in main_window:
        failures.append('main window no longer routes returns through feature tabs')

    return fail(failures) if failures else (print('Phase 49 return document-tabs guard passed.') or 0)


if __name__ == '__main__':
    raise SystemExit(main())
