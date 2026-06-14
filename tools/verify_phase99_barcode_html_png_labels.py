# -*- coding: utf-8 -*-
"""Static guard for Phase 99 barcode label rendering.
Ensures barcode labels use one HTML renderer and expose PNG/QR/logo settings.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def require(cond, msg):
    if not cond:
        raise SystemExit(msg)


def main():
    svc = read('alrajhi_client/core/services/barcode_label_service.py')
    printing = read('alrajhi_client/printing/printing_service.py')
    settings = read('alrajhi_client/core/services/settings_service.py')
    dialog = read('alrajhi_client/views/dialogs/batch_print_dialog.py')
    widget = read('alrajhi_client/views/widgets/settings_widget.py')
    tr = read('alrajhi_client/i18n/translator.py')

    require('qr_png_base64' in svc and 'show_qr' in svc, 'QR rendering support missing from barcode label service')
    require('_file_to_data_uri' in svc and 'show_logo' in svc, 'logo data-uri support missing from barcode label service')
    require('labels_document_html' in svc and 'lang=' in svc and 'dir=' in svc, 'language-aware label HTML missing')
    require('localized_item_name' in svc and "name_{lang}" in svc, 'localized item name fallback missing')
    require('save_html_png' in printing and 'barcode_labels_png' in printing, 'PNG export path missing from printing service')
    require('barcode_show_logo' in settings and 'barcode_show_qr' in settings, 'barcode logo/QR settings missing from settings service')
    require('barcode_show_logo' in widget and 'barcode_show_qr' in widget, 'barcode logo/QR controls missing from settings widget')
    require('barcode_labels_png' in dialog, 'batch print dialog does not use unified PNG rendering')
    require('ThermalPrinter' not in dialog and 'ImagePrinter' not in dialog, 'legacy raw/image barcode printer path still used in batch dialog')
    for key in ('settings_barcode_show_logo', 'settings_barcode_show_qr', 'barcode_required_for_print'):
        require(key in tr, f'translation key missing: {key}')
    print('✅ Phase 99 barcode HTML/PNG label rendering guard passed')


if __name__ == '__main__':
    main()
