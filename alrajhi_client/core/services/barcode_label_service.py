# -*- coding: utf-8 -*-
"""Barcode label rendering service.

Phase 99: labels are rendered as HTML first, with optional PNG export.  This keeps
Arabic, German, English, logo, QR and barcode output visually consistent across
PDF, image export and Qt printers instead of relying on raw thermal text output.
"""
from __future__ import annotations

import base64
import html
import io
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

try:
    from barcode import Code128, EAN13
    from barcode.writer import ImageWriter
except Exception:  # optional dependency used only for barcode image rendering
    Code128 = EAN13 = ImageWriter = None

try:
    import qrcode
except Exception:  # optional, dependency exists in requirements
    qrcode = None

from core.services.barcode_service import barcode_service, BarcodeError


def _language_context() -> tuple[str, str]:
    try:
        from i18n import get_language, language_direction
        lang = get_language()
        return lang, language_direction(lang)
    except Exception:
        return "ar", "rtl"


def _tr(key: str, **kwargs) -> str:
    try:
        from i18n import translate
        return translate(key, **kwargs)
    except Exception:
        return kwargs.get("default", key)


def _company_info() -> Dict:
    try:
        from core.services.settings_service import settings_service
        return settings_service.company_info() or {}
    except Exception:
        try:
            from config import get_company_info
            return get_company_info() or {}
        except Exception:
            return {}


def _file_to_data_uri(path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return ""
    if path.startswith('data:'):
        return path
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().lstrip('.') or 'png'
    if ext == 'jpg':
        ext = 'jpeg'
    try:
        with open(path, 'rb') as fh:
            data = base64.b64encode(fh.read()).decode('ascii')
        return f"data:image/{ext};base64,{data}"
    except Exception:
        return ""


@dataclass(frozen=True)
class LabelOptions:
    label_size: str = "50x30"
    symbology: str = "AUTO"
    show_company: bool = True
    show_logo: bool = True
    show_qr: bool = True
    show_name: bool = True
    show_price: bool = True
    show_barcode_text: bool = True
    columns: int = 2


class BarcodeLabelService:
    SIZES = {
        "40x30": {"width_mm": 40, "height_mm": 30, "barcode_width_mm": 34, "font_pt": 8, "qr_mm": 9, "logo_mm": 7},
        "50x30": {"width_mm": 50, "height_mm": 30, "barcode_width_mm": 38, "font_pt": 9, "qr_mm": 10, "logo_mm": 8},
        "60x40": {"width_mm": 60, "height_mm": 40, "barcode_width_mm": 48, "font_pt": 10, "qr_mm": 12, "logo_mm": 10},
        "80mm": {"width_mm": 72, "height_mm": 45, "barcode_width_mm": 60, "font_pt": 11, "qr_mm": 14, "logo_mm": 12},
    }

    def normalize_options(self, options: Optional[Dict | LabelOptions] = None) -> LabelOptions:
        if isinstance(options, LabelOptions):
            return options
        options = options or {}
        size = options.get('label_size', '50x30')
        if size not in self.SIZES:
            size = '50x30'
        symbology = (options.get('symbology') or 'AUTO').upper()
        if symbology not in ('AUTO', 'EAN13', 'CODE128'):
            symbology = 'AUTO'
        columns = int(options.get('columns', 2) or 2)
        columns = min(max(columns, 1), 4)
        return LabelOptions(
            label_size=size,
            symbology=symbology,
            show_company=bool(options.get('show_company', True)),
            show_logo=bool(options.get('show_logo', True)),
            show_qr=bool(options.get('show_qr', True)),
            show_name=bool(options.get('show_name', True)),
            show_price=bool(options.get('show_price', True)),
            show_barcode_text=bool(options.get('show_barcode_text', True)),
            columns=columns,
        )

    def resolve_symbology(self, barcode: str, requested: str = 'AUTO') -> str:
        requested = (requested or 'AUTO').upper()
        value = barcode_service.normalize(barcode)
        if not value:
            raise BarcodeError(_tr('barcode_required_for_print', default='Barcode is required for printing'))
        detected = barcode_service.detect_symbology(value)
        if detected in ('INVALID', 'INVALID_EAN13', 'EMPTY'):
            barcode_service.validate(value, allow_empty=False)
        if requested == 'AUTO':
            return 'EAN13' if detected == 'EAN13' else 'CODE128'
        if requested == 'EAN13' and not barcode_service.is_valid_ean13(value):
            raise BarcodeError(_tr('barcode_invalid_ean13_print', default='This code cannot be printed as EAN-13'))
        return requested

    def barcode_png_base64(self, barcode: str, symbology: str = 'AUTO') -> str:
        if Code128 is None or EAN13 is None or ImageWriter is None:
            raise RuntimeError(_tr('barcode_python_packages_required', default='python-barcode and Pillow are required'))
        value = barcode_service.normalize(barcode)
        sym = self.resolve_symbology(value, symbology)
        writer = ImageWriter()
        code = EAN13(value, writer=writer) if sym == 'EAN13' else Code128(value, writer=writer)
        buffer = io.BytesIO()
        code.write(buffer, options={
            'write_text': False,
            'module_height': 12.0,
            'quiet_zone': 2.0,
            'font_size': 8,
            'dpi': 220,
        })
        return base64.b64encode(buffer.getvalue()).decode('ascii')

    def qr_png_base64(self, value: str) -> str:
        if not value or qrcode is None:
            return ""
        img = qrcode.make(str(value))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('ascii')

    def localized_item_name(self, item: Dict) -> str:
        lang, _ = _language_context()
        # Future-proof: if multilingual item names are later added to the DB, use them automatically.
        for key in (f'name_{lang}', f'item_name_{lang}', 'localized_name', 'name'):
            value = str(item.get(key, '') or '').strip()
            if value:
                return value
        return ''

    def label_html(self, item: Dict, options: Optional[Dict | LabelOptions] = None) -> str:
        opts = self.normalize_options(options)
        size = self.SIZES[opts.label_size]
        lang, direction = _language_context()
        company_info = _company_info()
        company = str(company_info.get('name') or _tr('app_name_short', default='Al Rajhi Accounting')).strip()
        logo_value = company_info.get('logo_data_uri') or company_info.get('logo_path') or company_info.get('logo')
        logo_src = _file_to_data_uri(logo_value) if opts.show_logo else ''
        barcode = str(item.get('barcode', '') or '').strip()
        name = self.localized_item_name(item)
        price = str(item.get('price', '') or item.get('selling_price', '') or '').strip()
        img = self.barcode_png_base64(barcode, opts.symbology)
        qr_img = self.qr_png_base64(barcode) if opts.show_qr else ''
        price_label = _tr('price', default='Price')
        parts = []
        if logo_src or (opts.show_company and company):
            logo = f"<img class='label-logo' src='{logo_src}' alt='logo' />" if logo_src else ""
            comp = f"<div class='company'>{html.escape(company)}</div>" if opts.show_company and company else ""
            parts.append(f"<div class='label-top'>{logo}{comp}</div>")
        if opts.show_name and name:
            parts.append(f"<div class='item-name'>{html.escape(name)}</div>")
        parts.append("<div class='code-row'>")
        parts.append(f"<img class='barcode-img' src='data:image/png;base64,{img}' alt='barcode' />")
        if qr_img:
            parts.append(f"<img class='qr-img' src='data:image/png;base64,{qr_img}' alt='qr' />")
        parts.append("</div>")
        if opts.show_barcode_text:
            parts.append(f"<div class='barcode-text'>{html.escape(barcode)}</div>")
        if opts.show_price and price:
            parts.append(f"<div class='price'><span>{html.escape(price_label)}</span>: {html.escape(price)}</div>")
        return f"""
        <div class="barcode-label size-{opts.label_size}" dir="{direction}" lang="{html.escape(lang)}">
            {''.join(parts)}
        </div>
        """

    def labels_document_html(self, items: Iterable[Dict], options: Optional[Dict | LabelOptions] = None) -> str:
        opts = self.normalize_options(options)
        size = self.SIZES[opts.label_size]
        lang, direction = _language_context()
        labels: List[str] = []
        for item in items:
            copies = int(item.get('copies', 1) or 1)
            for _ in range(max(1, copies)):
                labels.append(self.label_html(item, opts))
        gap = 3
        text_align = 'right' if direction == 'rtl' else 'left'
        return f"""<!DOCTYPE html>
<html dir="{direction}" lang="{html.escape(lang)}">
<head>
<meta charset="UTF-8">
<style>
    @page {{ margin: 4mm; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 6mm; font-family: 'Tajawal','Noto Sans Arabic','Arial','Tahoma',sans-serif; background: #fff; color: #111827; direction: {direction}; }}
    .labels-page {{ display: grid; grid-template-columns: repeat({opts.columns}, {size['width_mm']}mm); gap: {gap}mm; align-items: start; justify-content: start; }}
    .barcode-label {{ width: {size['width_mm']}mm; min-height: {size['height_mm']}mm; box-sizing: border-box; border: 1px dashed #c8c8c8; border-radius: 2mm; padding: 2mm; text-align: center; page-break-inside: avoid; overflow: hidden; background: #fff; }}
    .label-top {{ display: flex; align-items: center; justify-content: center; gap: 1.5mm; margin-bottom: 1mm; direction: {direction}; }}
    .label-logo {{ width: {size['logo_mm']}mm; height: {size['logo_mm']}mm; object-fit: contain; flex: 0 0 auto; }}
    .company {{ font-size: {max(7, size['font_pt']-1)}pt; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: {max(22, size['width_mm']-12)}mm; }}
    .item-name {{ font-size: {size['font_pt']}pt; font-weight: 700; margin-bottom: 1mm; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; direction: {direction}; text-align: center; }}
    .code-row {{ display: flex; align-items: center; justify-content: center; gap: 1.5mm; direction: ltr; }}
    .barcode-img {{ width: {size['barcode_width_mm']}mm; max-height: {max(12, size['height_mm']-17)}mm; object-fit: contain; display: block; }}
    .qr-img {{ width: {size['qr_mm']}mm; height: {size['qr_mm']}mm; object-fit: contain; display: block; }}
    .barcode-text {{ font-size: {max(7, size['font_pt']-1)}pt; font-family: 'Consolas','Courier New',monospace; direction: ltr; unicode-bidi: embed; margin-top: .6mm; }}
    .price {{ font-size: {size['font_pt']}pt; font-weight: 700; margin-top: .6mm; direction: {direction}; text-align: center; }}
    .price span {{ font-weight: 700; }}
    @media print {{ body {{ padding: 0; }} .barcode-label {{ border-color: #d4d4d4; }} }}
</style>
</head>
<body><div class="labels-page">{''.join(labels)}</div></body></html>"""


barcode_label_service = BarcodeLabelService()
