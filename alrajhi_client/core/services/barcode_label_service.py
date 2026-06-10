# -*- coding: utf-8 -*-
"""Barcode label rendering service.

Barcode-1 hardened generation and validation.  Barcode-2 centralizes label
rendering and print options so PDF/image/batch printing use one contract.
"""
from __future__ import annotations

import base64
import html
import io
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from barcode import Code128, EAN13
from barcode.writer import ImageWriter

from config import get_company_info
from core.services.barcode_service import barcode_service, BarcodeError


@dataclass(frozen=True)
class LabelOptions:
    label_size: str = "50x30"
    symbology: str = "AUTO"
    show_company: bool = True
    show_name: bool = True
    show_price: bool = True
    show_barcode_text: bool = True
    columns: int = 2


class BarcodeLabelService:
    SIZES = {
        "40x30": {"width_mm": 40, "height_mm": 30, "barcode_width_mm": 34, "font_pt": 8},
        "50x30": {"width_mm": 50, "height_mm": 30, "barcode_width_mm": 43, "font_pt": 9},
        "60x40": {"width_mm": 60, "height_mm": 40, "barcode_width_mm": 52, "font_pt": 10},
        "80mm": {"width_mm": 72, "height_mm": 45, "barcode_width_mm": 62, "font_pt": 11},
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
            show_name=bool(options.get('show_name', True)),
            show_price=bool(options.get('show_price', True)),
            show_barcode_text=bool(options.get('show_barcode_text', True)),
            columns=columns,
        )

    def resolve_symbology(self, barcode: str, requested: str = 'AUTO') -> str:
        requested = (requested or 'AUTO').upper()
        value = barcode_service.normalize(barcode)
        if not value:
            raise BarcodeError("الباركود مطلوب للطباعة")
        detected = barcode_service.detect_symbology(value)
        if detected in ('INVALID', 'INVALID_EAN13', 'EMPTY'):
            barcode_service.validate(value, allow_empty=False)
        if requested == 'AUTO':
            return 'EAN13' if detected == 'EAN13' else 'CODE128'
        if requested == 'EAN13' and not barcode_service.is_valid_ean13(value):
            raise BarcodeError("لا يمكن طباعة هذا الرمز كـ EAN-13 لأنه غير صالح")
        return requested

    def barcode_png_base64(self, barcode: str, symbology: str = 'AUTO') -> str:
        value = barcode_service.normalize(barcode)
        sym = self.resolve_symbology(value, symbology)
        writer = ImageWriter()
        if sym == 'EAN13':
            code = EAN13(value, writer=writer)
        else:
            code = Code128(value, writer=writer)
        buffer = io.BytesIO()
        code.write(buffer, options={
            'write_text': False,
            'module_height': 12.0,
            'quiet_zone': 2.0,
            'font_size': 8,
            'dpi': 200,
        })
        return base64.b64encode(buffer.getvalue()).decode('ascii')

    def label_html(self, item: Dict, options: Optional[Dict | LabelOptions] = None) -> str:
        opts = self.normalize_options(options)
        size = self.SIZES[opts.label_size]
        company = get_company_info().get('name', 'الراجحي للمحاسبة')
        barcode = str(item.get('barcode', '') or '').strip()
        name = str(item.get('name', '') or '').strip()
        price = str(item.get('price', '') or '').strip()
        img = self.barcode_png_base64(barcode, opts.symbology)
        parts = []
        if opts.show_company:
            parts.append(f"<div class='company'>{html.escape(company)}</div>")
        if opts.show_name:
            parts.append(f"<div class='item-name'>{html.escape(name)}</div>")
        parts.append(f"<img class='barcode-img' src='data:image/png;base64,{img}' />")
        if opts.show_barcode_text:
            parts.append(f"<div class='barcode-text'>{html.escape(barcode)}</div>")
        if opts.show_price and price:
            parts.append(f"<div class='price'>السعر: {html.escape(price)}</div>")
        return f"""
        <div class="barcode-label size-{opts.label_size}">
            {''.join(parts)}
        </div>
        """

    def labels_document_html(self, items: Iterable[Dict], options: Optional[Dict | LabelOptions] = None) -> str:
        opts = self.normalize_options(options)
        size = self.SIZES[opts.label_size]
        labels: List[str] = []
        for item in items:
            copies = int(item.get('copies', 1) or 1)
            for _ in range(max(1, copies)):
                labels.append(self.label_html(item, opts))
        gap = 3
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
    body {{ margin: 6mm; font-family: Arial, Tahoma, sans-serif; background: #fff; }}
    .labels-page {{ display: grid; grid-template-columns: repeat({opts.columns}, {size['width_mm']}mm); gap: {gap}mm; align-items: start; }}
    .barcode-label {{ width: {size['width_mm']}mm; min-height: {size['height_mm']}mm; box-sizing: border-box; border: 1px dashed #c8c8c8; padding: 2mm; text-align: center; page-break-inside: avoid; overflow: hidden; }}
    .company {{ font-size: {max(7, size['font_pt']-1)}pt; font-weight: bold; margin-bottom: 1mm; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .item-name {{ font-size: {size['font_pt']}pt; font-weight: bold; margin-bottom: 1mm; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .barcode-img {{ width: {size['barcode_width_mm']}mm; max-height: {max(12, size['height_mm']-16)}mm; object-fit: contain; margin: 1mm auto; display: block; }}
    .barcode-text {{ font-size: {max(7, size['font_pt']-1)}pt; font-family: monospace; direction: ltr; }}
    .price {{ font-size: {size['font_pt']}pt; font-weight: bold; margin-top: 1mm; }}
</style>
</head>
<body><div class="labels-page">{''.join(labels)}</div></body></html>"""


barcode_label_service = BarcodeLabelService()
