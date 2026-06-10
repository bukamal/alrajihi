# -*- coding: utf-8 -*-
"""Reusable RTL HTML print templates for invoices, vouchers and reports."""
from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Optional
import base64
from io import BytesIO
import datetime

from config import get_company_info
from core.services.settings_service import settings_service


def _s(value: Any) -> str:
    return escape("" if value is None else str(value))


def _company_header(settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or settings_service.get_printing_settings()
    info = get_company_info()
    logo_html = ""
    logo_path = info.get('logo_path') or ''
    if logo_path and settings.get('show_logo', True):
        logo_html = f"<img class='logo' src='{_s(logo_path)}' alt='logo'/>"
    tax = info.get('tax_number') or ''
    return f"""
    <div class="company-header">
        {logo_html}
        <div class="company-name">{_s(info.get('name', ''))}</div>
        <div class="company-line">{_s(info.get('address', ''))}</div>
        <div class="company-line">هاتف: {_s(info.get('phone', ''))} &nbsp; | &nbsp; بريد: {_s(info.get('email', ''))}</div>
        <div class="company-line tax">{('الرقم الضريبي: ' + _s(tax)) if tax and settings.get('show_tax_number', True) else ''}</div>
    </div>
    """


def _qr_data_uri(payload: str) -> str:
    try:
        import qrcode
        img = qrcode.make(payload or '')
        buf = BytesIO()
        img.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return ''

def _print_meta_line() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def base_document(title: str, body_html: str, paper: str = 'a4') -> str:
    width = '78mm' if paper == 'thermal80' else '210mm'
    margin = '4mm' if paper == 'thermal80' else '12mm'
    font_size = '10px' if paper == 'thermal80' else '13px'
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{_s(title)}</title>
<style>
    @page {{ size: {'80mm auto' if paper == 'thermal80' else 'A4'}; margin: {margin}; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Tajawal','Arial',sans-serif; direction: rtl; color: #111827; font-size: {font_size}; margin: 0; }}
    .sheet {{ width: {width}; margin: 0 auto; }}
    .company-header {{ text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-bottom: 14px; }}
    .logo {{ max-height: 60px; max-width: 120px; display: block; margin: 0 auto 6px; }}
    .company-name {{ font-size: 20px; font-weight: 700; }}
    .company-line {{ margin-top: 3px; color: #374151; }}
    .doc-title {{ text-align: center; font-size: 18px; font-weight: 700; margin: 10px 0; }}
    .meta {{ width: 100%; border-collapse: collapse; margin: 10px 0 14px; }}
    .meta td {{ border: 1px solid #d1d5db; padding: 7px; }}
    table.items {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    table.items th, table.items td {{ border: 1px solid #d1d5db; padding: 7px; text-align: center; }}
    table.items th {{ background: #2563eb; color: white; font-weight: 700; }}
    .totals {{ width: 330px; margin-right: auto; margin-top: 14px; border-collapse: collapse; }}
    .totals td {{ border: 1px solid #d1d5db; padding: 7px; }}
    .total-final td {{ font-weight: 700; background: #eff6ff; }}
    .notes {{ margin-top: 12px; border: 1px dashed #d1d5db; padding: 8px; min-height: 34px; }}
    .signatures {{ display: flex; justify-content: space-between; gap: 20px; margin-top: 36px; }}
    .signature {{ width: 45%; text-align: center; border-top: 1px solid #374151; padding-top: 6px; }}
    .footer {{ margin-top: 28px; text-align: center; color: #6b7280; font-size: 11px; }}
    .qr-box {{ text-align: center; margin-top: 14px; }}
    .qr-box img {{ width: 95px; height: 95px; }}
    .summary-cards {{ display: flex; gap: 8px; margin: 12px 0; flex-wrap: wrap; }}
    .summary-card {{ flex: 1; min-width: 130px; border: 1px solid #d1d5db; border-radius: 8px; padding: 9px; background: #f9fafb; }}
    .summary-card b {{ display: block; color: #374151; font-size: 12px; margin-bottom: 5px; }}
    .summary-card span {{ font-weight: 700; color: #111827; }}
    .thermal .company-name {{ font-size: 14px; }}
    .thermal .doc-title {{ font-size: 13px; }}
    .thermal table.items th, .thermal table.items td, .thermal .meta td, .thermal .totals td {{ padding: 3px; }}
    .thermal .totals {{ width: 100%; }}
</style>
</head>
<body class="{_s(paper)}">
<div class="sheet">
{body_html}
</div>
</body>
</html>"""


def invoice_html(invoice: Dict[str, Any], paper: str = 'a4') -> str:
    inv_type = invoice.get('type') or invoice.get('inv_type') or 'sale'
    title = 'فاتورة بيع' if inv_type == 'sale' else 'فاتورة شراء'
    ref = invoice.get('reference') or invoice.get('ref') or ''
    date = invoice.get('date') or ''
    party_label = 'العميل' if inv_type == 'sale' else 'المورد'
    party = invoice.get('party_name') or invoice.get('entity_name') or invoice.get('customer_name') or invoice.get('supplier_name') or 'نقدي'
    print_settings = settings_service.get_printing_settings()
    if paper == 'default':
        paper = print_settings.get('invoice_template', 'a4')
    lines: Iterable[Dict[str, Any]] = invoice.get('lines') or []
    rows = []
    for i, line in enumerate(lines, 1):
        rows.append(
            f"<tr><td>{i}</td><td>{_s(line.get('item_name') or line.get('name'))}</td>"
            f"<td>{_s(line.get('unit', ''))}</td><td>{_s(line.get('quantity') or line.get('qty'))}</td>"
            f"<td>{_s(line.get('unit_price') or line.get('price'))}</td><td>{_s(line.get('total'))}</td></tr>"
        )
    qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
    qr_uri = _qr_data_uri(qr_payload) if print_settings.get('show_qr', True) else ''
    qr_html = f"<div class='qr-box'><img src='{qr_uri}'/><div>رمز الفاتورة</div></div>" if qr_uri else ''
    footer_text = print_settings.get('footer_text') or 'شكراً لتعاملكم معنا'
    body = f"""
    {_company_header(print_settings)}
    <div class="doc-title">{title}</div>
    <table class="meta">
        <tr><td><b>الرقم:</b> {_s(ref)}</td><td><b>التاريخ:</b> {_s(date)}</td></tr>
        <tr><td colspan="2"><b>{party_label}:</b> {_s(party)}</td></tr>
    </table>
    <table class="items">
        <thead><tr><th>#</th><th>المادة</th><th>الوحدة</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr></thead>
        <tbody>{''.join(rows) or '<tr><td colspan="6">لا توجد بنود</td></tr>'}</tbody>
    </table>
    <table class="totals">
        <tr><td>الإجمالي قبل الخصم</td><td>{_s(invoice.get('total_before_discount', invoice.get('subtotal', '')))}</td></tr>
        <tr><td>الخصم</td><td>{_s(invoice.get('discount', invoice.get('discount_amount', 0)))}</td></tr>
        <tr class="total-final"><td>الإجمالي</td><td>{_s(invoice.get('total'))}</td></tr>
        <tr><td>المدفوع</td><td>{_s(invoice.get('paid') or invoice.get('paid_amount', 0))}</td></tr>
        <tr><td>المتبقي</td><td>{_s(invoice.get('remaining', ''))}</td></tr>
    </table>
    <div class="notes"><b>ملاحظات:</b> {_s(invoice.get('notes', ''))}</div>
    {qr_html}
    <div class="signatures"><div class="signature">توقيع المستلم</div><div class="signature">المحاسب</div></div>
    <div class="footer">{_s(footer_text)}<br/>تاريخ الطباعة: {_print_meta_line()}</div>
    """
    return base_document(f"{title} {ref}", body, paper)


def voucher_html(voucher: Dict[str, Any], paper: str = 'a4') -> str:
    vtype = voucher.get('type')
    label = {'receipt': 'سند قبض', 'payment': 'سند دفع', 'expense': 'سند مصروف'}.get(vtype, 'سند')
    qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
    qr_uri = _qr_data_uri(qr_payload) if print_settings.get('show_qr', True) else ''
    qr_html = f"<div class='qr-box'><img src='{qr_uri}'/><div>رمز الفاتورة</div></div>" if qr_uri else ''
    footer_text = print_settings.get('footer_text') or 'شكراً لتعاملكم معنا'
    body = f"""
    {_company_header(print_settings)}
    <div class="doc-title">{label}</div>
    <table class="meta">
        <tr><td><b>الرقم:</b> {_s(voucher.get('id') or voucher.get('reference'))}</td><td><b>التاريخ:</b> {_s(voucher.get('date'))}</td></tr>
        <tr><td><b>المبلغ:</b> {_s(voucher.get('amount'))}</td><td><b>الطرف:</b> {_s(voucher.get('party_name', ''))}</td></tr>
        <tr><td colspan="2"><b>البيان:</b> {_s(voucher.get('description', ''))}</td></tr>
    </table>
    <div class="signatures"><div class="signature">المستلم</div><div class="signature">المحاسب</div></div>
    <div class="footer">{_s(label)}</div>
    """
    return base_document(label, body, paper)


def report_html(title: str, rows: List[List[Any]], headers: List[str], subtitle: str = '', summary: Optional[Dict[str, Any]] = None) -> str:
    head = ''.join(f"<th>{_s(h)}</th>" for h in headers)
    body_rows = ''.join('<tr>' + ''.join(f"<td>{_s(c)}</td>" for c in row) + '</tr>' for row in rows)
    qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
    qr_uri = _qr_data_uri(qr_payload) if print_settings.get('show_qr', True) else ''
    qr_html = f"<div class='qr-box'><img src='{qr_uri}'/><div>رمز الفاتورة</div></div>" if qr_uri else ''
    footer_text = print_settings.get('footer_text') or 'شكراً لتعاملكم معنا'
    body = f"""
    {_company_header(print_settings)}
    <div class="doc-title">{_s(title)}</div>
    <div style="text-align:center;margin-bottom:12px;">{_s(subtitle)}</div>
    <div style="text-align:center;color:#6b7280;margin-bottom:8px;">تاريخ الطباعة: {_print_meta_line()}</div>
    {summary_html}
    <table class="items"><thead><tr>{head}</tr></thead><tbody>{body_rows}</tbody></table>
    <div class="footer">{_s(print_settings.get('footer_text') or 'تم إنشاء التقرير بواسطة نظام الراجحي')}</div>
    """
    return base_document(title, body, 'a4')
