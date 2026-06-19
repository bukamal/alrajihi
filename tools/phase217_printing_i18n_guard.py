# -*- coding: utf-8 -*-
"""Phase 217 guard: printing surface must use i18n keys, not Arabic literals.

This is intentionally narrow: legacy designer/thermal tools may still carry UI
literals. The unified printable document surface is printing_service.py and
print_templates.py.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "alrajhi_client" / "printing" / "printing_service.py"
TEMPLATES = ROOT / "alrajhi_client" / "printing" / "print_templates.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"

ARABIC_LITERAL = re.compile(r"(?P<quote>['\"])(?P<value>[^'\"\n]*[\u0600-\u06FF][^'\"\n]*)(?P=quote)")
ALLOWED_TEMPLATE_SNIPPETS = {
    '"نعم"',  # boolean parser accepts legacy Arabic true value; not a UI string.
}

REQUIRED_TRANSLATION_KEYS = [
    "print_commercial_register",
    "print_preview_title",
    "print_dialog_title",
    "print_no_content",
    "print_no_preview_content",
    "print_no_save_content",
    "barcode_preview_title",
    "invoice_preview_title",
    "restaurant_kitchen_ticket_print_title",
    "manufacturing_pick_ticket_print_title",
    "inventory_transfer_print_title",
    "report_preview_title",
]


def _arabic_literals(path: Path):
    hits = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for match in ARABIC_LITERAL.finditer(line):
            literal = match.group(0)
            if path == TEMPLATES and literal in ALLOWED_TEMPLATE_SNIPPETS:
                continue
            hits.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    return hits


def main() -> int:
    problems = []
    for path in (SERVICE, TEMPLATES):
        problems.extend(_arabic_literals(path))

    service_text = SERVICE.read_text(encoding="utf-8")
    template_text = TEMPLATES.read_text(encoding="utf-8")
    translator_text = TRANSLATOR.read_text(encoding="utf-8")

    if "def _tr(" not in service_text:
        problems.append("printing_service.py must use the local _tr helper")
    if "_tr(\"print_no_content\")" not in service_text:
        problems.append("printing_service.py must use translated empty-content warnings")
    if "_tr('print_commercial_register')" not in template_text:
        problems.append("print_templates.py must translate commercial register label")
    if "_tr(\"print_date_label\")" not in template_text:
        problems.append("print_templates.py must translate print date label")
    if "_tr(\"print_receiver_signature\")" not in template_text:
        problems.append("print_templates.py must translate receiver signature")
    if '"categories": _tr("categories")' not in template_text:
        problems.append("_TITLE_MAP must translate categories via _tr")
    if '"users": _tr("users")' not in template_text:
        problems.append("_TITLE_MAP must translate users via _tr")

    for key in REQUIRED_TRANSLATION_KEYS:
        if key not in translator_text:
            problems.append(f"Missing print translation key: {key}")

    if problems:
        raise AssertionError("\n".join(problems))
    print("phase217_printing_i18n_guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
