# -*- coding: utf-8 -*-
"""Professional, settings-driven RTL HTML print templates.

All printable documents in the client should pass through these templates so PDF,
preview and direct-print output share the same header, typography, table style,
footer, paper sizing and company metadata.
"""
from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Optional
import base64
from io import BytesIO
import datetime
import os

from config import get_company_info
from core.services.settings_service import settings_service


def _tr(key: str, **kwargs) -> str:
    try:
        from i18n.translator import translate
        return translate(key, **kwargs)
    except Exception:
        return key


def _s(value: Any) -> str:
    return escape("" if value is None else str(value))


def _value(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _img_src(path: str) -> str:
    """Return a URI usable by QTextDocument."""
    if not path:
        return ""
    if path.startswith(("data:", "file:", "http://", "https://")):
        return path
    try:
        if os.path.exists(path):
            return "file:///" + os.path.abspath(path).replace("\\", "/")
    except Exception:
        pass
    return path


def _qr_data_uri(payload: str) -> str:
    try:
        import qrcode
        img = qrcode.make(payload or "")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def _print_meta_line() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _settings() -> Dict[str, Any]:
    try:
        cfg = settings_service.get_printing_settings()
        return dict(cfg or {})
    except Exception:
        return {}


def _bool_setting(settings: Dict[str, Any], key: str, default: bool = True) -> bool:
    val = settings.get(key, default)
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("1", "true", "yes", "on", "نعم")


def _normalize_paper(paper: str = "default", settings: Optional[Dict[str, Any]] = None, doc_type: str = "invoice") -> str:
    settings = settings or _settings()
    if paper in (None, "", "default"):
        if doc_type == "report":
            paper = settings.get("report_template") or settings.get("default_paper") or "a4"
        elif doc_type == "voucher":
            paper = settings.get("voucher_template") or settings.get("invoice_template") or "a4"
        elif doc_type == "return":
            paper = settings.get("return_template") or settings.get("invoice_template") or "a4"
        else:
            paper = settings.get("invoice_template") or settings.get("default_paper") or "a4"
    return str(paper or "a4").lower()


def _paper_spec(paper: str, settings: Dict[str, Any]) -> Dict[str, str]:
    paper = (paper or "a4").lower()
    thermal_size = str(settings.get("thermal_size", "80mm")).lower()
    if paper in ("thermal", "receipt"):
        paper = "thermal58" if "58" in thermal_size else "thermal80"
    if paper == "thermal58":
        return {"class": "thermal58", "page": "58mm auto", "width": "58mm", "margin": "2.5mm", "font": "8.5pt"}
    if paper == "thermal80":
        return {"class": "thermal80", "page": "80mm auto", "width": "78mm", "margin": "3mm", "font": "9pt"}
    # QTextDocument handles A4 HTML most consistently when the sheet remains fluid.
    return {"class": "a4", "page": "A4", "width": "100%", "margin": "10mm", "font": str(settings.get("print_font_size", "10.5pt") or "10.5pt")}


def _accent(settings: Dict[str, Any]) -> str:
    value = str(settings.get("accent_color", "#1d4ed8") or "#1d4ed8")
    return value if value.startswith("#") and len(value) in (4, 7) else "#1d4ed8"


def _font_family(settings: Dict[str, Any]) -> str:
    family = settings.get("font_family") or "Tajawal, Arial, DejaVu Sans, sans-serif"
    return str(family)





def _document_language() -> str:
    try:
        from i18n.translator import normalize_language
        return normalize_language(settings_service.get_language())
    except Exception:
        return "ar"


def _document_direction() -> str:
    try:
        from i18n.translator import language_direction
        return language_direction(_document_language())
    except Exception:
        return "rtl"


_TITLE_MAP = {
    "invoices": _tr("invoices"),
    "invoice": _tr("invoices"),
    "sales_invoices": _tr("sales_invoices"),
    "sale_invoices": _tr("sales_invoices"),
    "purchase_invoices": _tr("purchase_invoices"),
    "purchases_invoices": _tr("purchase_invoices"),
    "items": _tr("items"),
    "products": _tr("items"),
    "customers": _tr("customers"),
    "suppliers": _tr("suppliers"),
    "categories": "التصنيفات",
    "users": "المستخدمون",
    "vouchers": _tr("vouchers"),
    "warehouses": _tr("warehouses"),
    "cashboxes": _tr("cashboxes"),
    "banks": _tr("banks"),
    "cash_bank": _tr("cashboxes"),
    "manufacturing": _tr("manufacturing"),
    "reports": _tr("reports"),
    "settings": _tr("settings"),
    "audit_log": _tr("audit_log"),
    "returns": _tr("returns"),
    "sales_returns": _tr("sales_returns"),
    "purchase_returns": _tr("purchase_returns"),
}

def _human_title(title: Any, fallback: str = _tr("print_report_default")) -> str:
    raw = str(title or "").strip()
    if not raw:
        return fallback
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _TITLE_MAP:
        return _TITLE_MAP[key]
    # Hide internal object names like table_items or view_invoices.
    for prefix in ("table_", "view_", "widget_", "page_", "tbl_"):
        if key.startswith(prefix) and key[len(prefix):] in _TITLE_MAP:
            return _TITLE_MAP[key[len(prefix):]]
    # If it is a technical ASCII identifier, do not print it above the date.
    if raw.replace("_", "").replace("-", "").isascii() and any(ch.isalpha() for ch in raw):
        return fallback
    return raw


def _company_data(settings: Dict[str, Any]) -> Dict[str, str]:
    info = get_company_info() or {}
    logo_path = _value(info.get("logo_path") or settings.get("logo_path"))
    try:
        from pathlib import Path as _Path
        if not logo_path or not _Path(logo_path).exists():
            from brand_assets import logo_png
            logo_path = logo_png(512)
    except Exception:
        logo_path = logo_path if logo_path else ""
    return {
        "name": _value(info.get("name") or settings.get("company_name"), _tr("app_title")),
        "address": _value(info.get("address") or settings.get("company_address")),
        "phone": _value(info.get("phone") or settings.get("company_phone")),
        "email": _value(info.get("email") or settings.get("company_email")),
        "tax_number": _value(info.get("tax_number") or settings.get("tax_number")),
        "logo_path": logo_path,
    }


def _company_header(settings: Dict[str, Any], title: str = "") -> str:
    title = _human_title(title, _tr("print_document"))
    data = _company_data(settings)
    logo_html = ""
    if data["logo_path"] and _bool_setting(settings, "show_logo", True):
        logo_html = f"<td class='brand-logo'><img src='{_s(_img_src(data['logo_path']))}' alt='logo'></td>"
    else:
        logo_html = "<td class='brand-logo placeholder'> </td>"

    tax_line = ""
    if data["tax_number"] and _bool_setting(settings, "show_tax_number", True):
        tax_line = f"<div class='muted'>الرقم الضريبي: {_s(data['tax_number'])}</div>"

    contacts = []
    if data["phone"]:
        contacts.append(_tr("print_phone") + ": " + _s(data["phone"]))
    if data["email"]:
        contacts.append(_tr("print_email") + ": " + _s(data["email"]))
    contact_line = " | ".join(contacts)

    return f"""
    <table class='brand-table'>
        <tr>
            {logo_html}
            <td class='brand-main'>
                <div class='company-name'>{_s(data['name'])}</div>
                <div class='muted'>{_s(data['address'])}</div>
                <div class='muted'>{contact_line}</div>
                {tax_line}
            </td>
            <td class='brand-meta'>
                <div class='document-badge'>{_s(title)}</div>
                <div class='muted'>تاريخ الطباعة</div>
                <div class='strong'>{_print_meta_line()}</div>
            </td>
        </tr>
    </table>
    """


def _meta_table(rows: List[List[tuple]]) -> str:
    out = []
    for row in rows:
        cells = []
        for label, value in row:
            cells.append(f"<td><span class='meta-label'>{_s(label)}</span><span class='meta-value'>{_s(value)}</span></td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return "<table class='meta-table'>" + "".join(out) + "</table>"


def _totals_table(rows: List[tuple]) -> str:
    body = []
    for label, value, klass in rows:
        cls = f" class='{_s(klass)}'" if klass else ""
        body.append(f"<tr{cls}><td>{_s(label)}</td><td>{_s(value)}</td></tr>")
    return "<table class='totals-table'>" + "".join(body) + "</table>"


def _line_value(line: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = line.get(key) if isinstance(line, dict) else None
        if value not in (None, ""):
            return value
    return default


def _table(headers: List[str], rows: List[List[Any]], empty_text: str = _tr("print_no_data"), reverse_columns: Optional[bool] = None) -> str:
    """Render a professional RTL-safe table.

    Qt QTextDocument sometimes mirrors RTL table visual order differently between
    preview and PDF. We therefore reverse columns in the generated HTML by
    default, so the final PDF appears in the intended Arabic order. This can be
    disabled from printing settings with reverse_print_table_columns = false.
    """
    settings = _settings()
    if reverse_columns is None:
        reverse_columns = _bool_setting(settings, "reverse_print_table_columns", False)

    safe_headers = list(headers or [])
    safe_rows = [list(row or []) for row in (rows or [])]
    if reverse_columns and len(safe_headers) > 1:
        safe_headers = list(reversed(safe_headers))
        safe_rows = [list(reversed(row)) for row in safe_rows]

    head = "".join(f"<th>{_s(h)}</th>" for h in safe_headers)
    body = []
    for row in safe_rows:
        # Keep row length aligned with header count for stable PDF rendering.
        if len(row) < len(safe_headers):
            row = row + [""] * (len(safe_headers) - len(row))
        elif len(row) > len(safe_headers) and safe_headers:
            row = row[:len(safe_headers)]
        body.append("<tr>" + "".join(f"<td>{_s(c)}</td>" for c in row) + "</tr>")
    if not body:
        body.append(f"<tr><td colspan='{max(1, len(safe_headers))}' class='empty-cell'>{_s(empty_text)}</td></tr>")
    table_dir = _document_direction()
    return f"<table class='data-table' dir='{table_dir}'><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _summary_cards(summary: Optional[Dict[str, Any]]) -> str:
    if not summary:
        return ""
    cells = []
    for key, value in summary.items():
        cells.append(f"<td class='summary-card'><div class='summary-label'>{_s(key)}</div><div class='summary-value'>{_s(value)}</div></td>")
    return "<table class='summary-table'><tr>" + "".join(cells) + "</tr></table>"


def _footer(settings: Dict[str, Any], default: str = "") -> str:
    text = settings.get("footer_text") or default or _tr("print_generated_by")
    return f"<div class='print-footer'>{_s(text)}</div>"


def base_document(title: str, body_html: str, paper: str = "a4", settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or _settings()
    spec = _paper_spec(paper, settings)
    lang = _document_language()
    doc_dir = _document_direction()
    text_align = 'right' if doc_dir == 'rtl' else 'left'
    opposite_align = 'left' if doc_dir == 'rtl' else 'right'
    accent = _accent(settings)
    font_family = _font_family(settings)
    compact = " compact" if _bool_setting(settings, "compact_tables", False) else ""
    zebra = " zebra" if _bool_setting(settings, "zebra_rows", True) else ""

    # Use table-based layout because Qt QTextDocument renders it more reliably than flex/grid in PDF.
    return f"""<!DOCTYPE html>
<html dir='{doc_dir}' lang='{lang}'>
<head>
<meta charset='utf-8'>
<title>{_s(title)}</title>
<style>
@page {{ size: {spec['page']}; margin: {spec['margin']}; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #ffffff; color: #111827; direction: {doc_dir}; }}
body {{ font-family: {font_family}; font-size: {spec['font']}; line-height: 1.45; }}
.sheet {{ width: {spec['width']}; margin: 0 auto; }}
.brand-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; border-bottom: 3px solid {accent}; }}
.brand-table td {{ vertical-align: middle; padding: 8px 6px; border: none; }}
.brand-logo {{ width: 90px; text-align: center; }}
.brand-logo img {{ max-width: 78px; max-height: 70px; }}
.brand-logo.placeholder {{ border: 1px dashed #d1d5db; border-radius: 8px; }}
.brand-main {{ text-align: {text_align}; }}
.company-name {{ font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
.brand-meta {{ width: 155px; text-align: center; border-right: 1px solid #e5e7eb !important; }}
.document-badge {{ display: inline-block; background: {accent}; color: #ffffff; padding: 7px 12px; border-radius: 999px; font-weight: 800; margin-bottom: 5px; }}
.muted {{ color: #64748b; font-size: 90%; }}
.strong {{ font-weight: 800; color: #111827; }}
.document-title {{ text-align: center; font-size: 18px; font-weight: 900; margin: 8px 0 10px; color: #0f172a; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px; }}
.meta-table td {{ border: 1px solid #dbe3ef; background: #f8fafc; padding: 7px 9px; width: 33.33%; }}
.meta-label {{ display: block; color: #64748b; font-size: 88%; margin-bottom: 2px; }}
.meta-value {{ display: block; font-weight: 800; color: #0f172a; }}
.data-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; direction: {doc_dir}; }}
.data-table th {{ background: {accent}; color: #ffffff; border: 1px solid {accent}; padding: 8px 5px; font-weight: 800; text-align: center; white-space: normal; }}
.data-table td {{ border: 1px solid #dbe3ef; padding: 7px 5px; text-align: center; vertical-align: middle; word-wrap: break-word; overflow-wrap: anywhere; }}
.data-table tbody tr:nth-child(even) td {{ background: #f8fafc; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ page-break-inside: avoid; }}
.data-table .text-cell {{ text-align: {text_align}; }}
.empty-cell {{ color: #64748b; padding: 20px !important; }}
.summary-table {{ width: 100%; border-collapse: separate; border-spacing: 6px; margin: 9px 0; }}
.summary-card {{ border: 1px solid #dbe3ef; background: #f8fafc; border-radius: 10px; padding: 8px; text-align: center; }}
.summary-label {{ color: #64748b; font-size: 88%; }}
.summary-value {{ color: #0f172a; font-size: 115%; font-weight: 900; margin-top: 2px; }}
.totals-table {{ width: 42%; min-width: 260px; margin-{opposite_align}: auto; margin-top: 10px; border-collapse: collapse; }}
.totals-table td {{ border: 1px solid #dbe3ef; padding: 7px 9px; }}
.totals-table td:first-child {{ background: #f8fafc; color: #334155; font-weight: 700; }}
.totals-table td:last-child {{ text-align: {text_align}; font-weight: 800; }}
.totals-table tr.final td {{ background: #eaf2ff; color: #0f172a; font-size: 110%; }}
.totals-table tr.due td:last-child {{ color: #dc2626; }}
.notes-box {{ margin-top: 10px; border: 1px dashed #cbd5e1; background: #fcfdff; padding: 8px; min-height: 34px; }}
.qr-table {{ width: 100%; margin-top: 10px; border-collapse: collapse; }}
.qr-table td {{ text-align: center; border: none; color: #64748b; }}
.qr-table img {{ width: 88px; height: 88px; }}
.signatures {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
.signatures td {{ width: 50%; text-align: center; padding-top: 22px; border-top: 1px solid #475569; color: #334155; }}
.signatures td:first-child {{ padding-right: 30px; }}
.signatures td:last-child {{ padding-left: 30px; }}
.print-footer {{ margin-top: 18px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: center; color: #64748b; font-size: 90%; }}
.compact .data-table th, .compact .data-table td, .compact .meta-table td, .compact .totals-table td {{ padding: 4px 3px; }}
.thermal80 .sheet, .thermal58 .sheet {{ width: {spec['width']}; }}
.thermal80 .brand-table, .thermal58 .brand-table {{ border-bottom-width: 1px; margin-bottom: 5px; }}
.thermal80 .brand-logo, .thermal58 .brand-logo {{ display: none; }}
.thermal80 .brand-meta, .thermal58 .brand-meta {{ display: none; }}
.thermal80 .company-name, .thermal58 .company-name {{ font-size: 12px; text-align: center; }}
.thermal80 .muted, .thermal58 .muted {{ font-size: 8px; text-align: center; }}
.thermal80 .document-title, .thermal58 .document-title {{ font-size: 12px; margin: 4px 0; }}
.thermal80 .data-table th, .thermal80 .data-table td, .thermal58 .data-table th, .thermal58 .data-table td {{ padding: 2px; font-size: 8px; }}
.thermal80 .meta-table td, .thermal58 .meta-table td {{ display: table-cell; padding: 2px; font-size: 8px; }}
.thermal80 .totals-table, .thermal58 .totals-table {{ width: 100%; min-width: 0; }}
.thermal80 .signatures, .thermal58 .signatures {{ display: none; }}
.thermal80 .hide-thermal, .thermal58 .hide-thermal {{ display: none; }}
</style>
</head>
<body class='{_s(spec['class'])}{compact}{zebra}'>
<div class='sheet'>
{body_html}
</div>
</body>
</html>"""


def invoice_html(invoice: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "invoice")
    inv_type = invoice.get("type") or invoice.get("inv_type") or "sale"
    title = {"sale": _tr("sales_invoice"), "purchase": _tr("purchase_invoice")}.get(inv_type, _tr("invoice"))
    ref = invoice.get("reference") or invoice.get("ref") or invoice.get("number") or invoice.get("id") or ""
    date = invoice.get("date") or invoice.get("created_at") or ""
    party_label = _tr("print_party_customer") if inv_type == "sale" else _tr("print_party_supplier")
    party = invoice.get("party_name") or invoice.get("entity_name") or invoice.get("customer_name") or invoice.get("supplier_name") or _tr("print_cash_party")
    warehouse = invoice.get("warehouse_name") or invoice.get("warehouse") or ""
    payment_method = invoice.get("payment_method") or invoice.get("payment") or ""
    user_name = invoice.get("user_name") or invoice.get("seller_name") or invoice.get("created_by") or ""

    raw_lines: Iterable[Any] = invoice.get("lines") or invoice.get("items") or []
    rows: List[List[Any]] = []
    for i, raw in enumerate(raw_lines, 1):
        line = raw if isinstance(raw, dict) else {}
        rows.append([
            i,
            _line_value(line, "barcode", "item_barcode", "code"),
            _line_value(line, "item_name", "name", "description"),
            _line_value(line, "unit", "unit_display", "unit_name"),
            _line_value(line, "quantity", "qty"),
            _line_value(line, "unit_price", "price"),
            _line_value(line, "discount_percent", "discount_pct", "discount", default="0"),
            _line_value(line, "tax_percent", "tax_pct", "tax", default="0"),
            _line_value(line, "line_total", "total"),
        ])

    qr_html = ""
    if _bool_setting(settings, "show_qr", True):
        qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
        qr_uri = _qr_data_uri(qr_payload)
        if qr_uri:
            qr_html = f"<table class='qr-table'><tr><td><img src='{qr_uri}'><div>رمز المستند</div></td></tr></table>"

    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_document_number"), ref), (_tr("print_document_date"), date), (party_label, party)],
        [(_tr("print_warehouse"), warehouse), (_tr("print_payment_method"), payment_method), (_tr("print_user"), user_name)],
    ])}
    {_table(["#", _tr("print_barcode"), _tr("print_item"), _tr("print_unit"), _tr("print_quantity"), _tr("print_price"), _tr("print_discount_percent"), _tr("print_tax_percent"), _tr("print_total")], rows, _tr("print_no_lines"))}
    {_totals_table([
        (_tr("print_subtotal"), invoice.get("total_before_discount", invoice.get("subtotal", "")), ""),
        (_tr("print_discount"), invoice.get("discount", invoice.get("discount_amount", 0)), ""),
        (_tr("print_tax"), invoice.get("tax_amount", invoice.get("tax", 0)), ""),
        (_tr("print_grand_total"), invoice.get("total", ""), "final"),
        (_tr("print_paid"), invoice.get("paid") or invoice.get("paid_amount", 0), ""),
        (_tr("print_remaining"), invoice.get("remaining", ""), "due"),
    ])}
    <div class='notes-box'><b>{_s(_tr("print_notes"))}:</b> {_s(invoice.get('notes', ''))}</div>
    {qr_html}
    <table class='signatures hide-thermal'><tr><td>توقيع المستلم</td><td>المحاسب</td></tr></table>
    {_footer(settings, _tr("print_thanks"))}
    """
    return base_document(f"{title} {ref}", body, paper, settings)


def voucher_html(voucher: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "voucher")
    vtype = voucher.get("type")
    title = {"receipt": _tr("receipt_voucher"), "payment": _tr("payment_voucher"), "expense": _tr("expense_voucher")}.get(vtype, _tr("voucher"))
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_number"), voucher.get("id") or voucher.get("reference")), (_tr("print_document_date"), voucher.get("date")), (_tr("amount"), voucher.get("amount"))],
        [(_tr("print_party"), voucher.get("party_name", "")), (_tr("print_account"), voucher.get("account_name", "")), (_tr("print_user"), voucher.get("user_name", ""))],
    ])}
    <div class='notes-box'><b>{_s(_tr("print_description"))}:</b> {_s(voucher.get('description', ''))}</div>
    <table class='signatures'><tr><td>المستلم</td><td>المحاسب</td></tr></table>
    {_footer(settings, title)}
    """
    return base_document(title, body, paper, settings)


def return_html(data: Dict[str, Any], paper: str = "default") -> str:
    payload = dict(data or {})
    rtype = payload.get("type") or payload.get("return_type") or "sale_return"
    payload["type"] = "sale" if rtype in ("sale_return", "sale") else "purchase"
    payload["reference"] = payload.get("reference") or payload.get("return_number") or payload.get("id") or ""
    title = _tr("sales_return") if payload["type"] == "sale" else _tr("purchase_return")
    html = invoice_html(payload, _normalize_paper(paper, _settings(), "return"))
    return html.replace(_tr("sales_invoice"), title).replace(_tr("purchase_invoice"), title)


def report_html(title: str, rows: List[List[Any]], headers: List[str], subtitle: str = "", summary: Optional[Dict[str, Any]] = None, paper: str = "default") -> str:
    settings = _settings()
    title = _human_title(title, _tr("print_report_default"))
    paper = _normalize_paper(paper, settings, "report")
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    <div class='muted' style='text-align:center;margin-bottom:8px;'>{_s(subtitle)}</div>
    {_summary_cards(summary)}
    {_table(headers, rows, _tr("print_no_data"))}
    {_footer(settings, _tr("print_report_generated_by"))}
    """
    return base_document(title, body, paper, settings)


def production_order_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Professional HTML for production order details.

    Data accepts: order, consumptions, outputs, reservations or flat keys.
    """
    settings = _settings()
    paper = _normalize_paper(paper, settings, "report")
    payload = dict(data or {})
    order = payload.get("order") or payload
    consumptions = payload.get("consumptions") or []
    outputs = payload.get("outputs") or []
    reservations = payload.get("reservations") or []
    status_map = {'planned': 'مخطط', 'in_progress': 'قيد التنفيذ', 'completed': 'مكتمل', 'cancelled': 'ملغي'}
    title = _tr("production_order")
    meta = _meta_table([
        [(_tr("order_number"), order.get("order_number") or order.get("id") or ""), (_tr("product"), order.get("product_name") or order.get("item_name") or ""), (_tr("status"), status_map.get(order.get("status"), order.get("status", "")))],
        [(_tr("planned_quantity"), order.get("planned_qty", "")), (_tr("produced_quantity"), order.get("produced_qty", "")), (_tr("start_date"), order.get("start_date", ""))],
        [(_tr("raw_warehouse"), order.get("raw_warehouse_name") or ""), (_tr("output_warehouse"), order.get("output_warehouse_name") or ""), (_tr("print_notes"), order.get("notes", ""))],
    ])
    cons_rows = []
    for i, c in enumerate(consumptions, 1):
        cons_rows.append([i, c.get('item_name') or c.get('name') or c.get('item') or c.get('item_id') or '', c.get('consumed_qty') or c.get('quantity') or '', c.get('unit_cost') or c.get('cost') or '', c.get('movement_date') or c.get('date') or ''])
    out_rows = []
    for i, o in enumerate(outputs, 1):
        out_rows.append([i, o.get('product_name') or o.get('item_name') or o.get('item') or o.get('product_id') or '', o.get('produced_qty') or o.get('quantity') or '', o.get('unit_cost') or o.get('cost') or '', o.get('output_date') or o.get('date') or ''])
    res_rows = []
    for i, r in enumerate(reservations, 1):
        reserved = r.get('reserved_qty') or r.get('reserved') or ''
        consumed = r.get('consumed_qty') or r.get('consumed') or ''
        remaining = r.get('remaining_qty') or r.get('remaining') or ''
        res_rows.append([i, r.get('item_name') or r.get('name') or r.get('item') or r.get('item_id') or '', reserved, consumed, remaining])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {meta}
    <h3>المواد المستهلكة</h3>
    {_table(['#','المادة','الكمية','تكلفة الوحدة','التاريخ'], cons_rows, 'لا توجد مواد مستهلكة')}
    <h3>المنتج النهائي</h3>
    {_table(['#','المنتج','الكمية','تكلفة الوحدة','التاريخ'], out_rows, 'لا توجد مخرجات إنتاج')}
    <h3>الحجوزات والمتبقي</h3>
    {_table(['#','المادة','المحجوز','المستهلك','المتبقي'], res_rows, 'لا توجد حجوزات')}
    <table class='signatures hide-thermal'><tr><td>مسؤول الإنتاج</td><td>المحاسبة</td></tr></table>
    {_footer(settings, 'تم إنشاء أمر الإنتاج بواسطة نظام الراجحي')}
    """
    return base_document(title, body, paper, settings)
