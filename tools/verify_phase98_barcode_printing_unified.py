# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(path):
    return (ROOT / path).read_text(encoding='utf-8')

required = {
    'alrajhi_client/printing/printing_service.py': [
        'def barcode_label_options',
        'def barcode_labels_html',
        'def barcode_labels_print',
        'def barcode_labels_pdf',
        'barcode_label_service.labels_document_html',
    ],
    'alrajhi_client/core/services/settings_service.py': [
        'barcode_default_printer', 'barcode_label_size', 'barcode_symbology',
        'barcode_copies', 'barcode_columns', 'barcode_show_company',
    ],
    'alrajhi_client/views/widgets/settings_widget.py': [
        'settings_barcode_print_title', 'barcode_default_printer',
        'barcode_label_size', 'barcode_symbology', 'barcode_copies', 'barcode_columns',
    ],
    'alrajhi_client/views/dialogs/batch_print_dialog.py': [
        'printing_service.barcode_labels_pdf',
        'printing_service.barcode_labels_print',
        'settings_service.get_printing_settings',
    ],
    'alrajhi_client/views/widgets/items_widget.py': [
        'BatchPrintDialog(self, selected_items=[item])',
    ],
    'alrajhi_client/i18n/translator.py': [
        'settings_barcode_print_title', 'settings_barcode_default_printer_label',
    ],
}

missing = []
for path, needles in required.items():
    content = text(path)
    for needle in needles:
        if needle not in content:
            missing.append(f'{path}: missing {needle}')

if 'PDFPrinter(self)' in text('alrajhi_client/views/widgets/items_widget.py'):
    missing.append('items_widget still uses PDFPrinter directly for single barcode printing')
if 'PDFPrinter(self)' in text('alrajhi_client/views/dialogs/batch_print_dialog.py'):
    missing.append('batch_print_dialog still uses PDFPrinter directly instead of unified printing_service')

if missing:
    raise SystemExit('\n'.join(missing))
print('OK phase98 unified barcode printing wiring')
