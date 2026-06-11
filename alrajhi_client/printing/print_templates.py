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
from i18n.translator import t, translate_text, get_language, direction as lang_direction, html_lang as current_html_lang


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



def _reverse_header_layout(settings: Optional[Dict[str, Any]] = None) -> bool:
    settings = settings or _settings()
    return _bool_setting(settings, "reverse_print_header_layout", True)


def _reverse_meta_layout(settings: Optional[Dict[str, Any]] = None) -> bool:
    settings = settings or _settings()
    return _bool_setting(settings, "reverse_print_meta_columns", True)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return _s(f"{value:.6f}".rstrip('0').rstrip('.'))
    return _s(value)

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




_TITLE_KEY_MAP = {
    "invoices": "invoice", "invoice": "invoice",
    "sales_invoices": "sales_invoices", "sale_invoices": "sales_invoices",
    "purchase_invoices": "purchase_invoices", "purchases_invoices": "purchase_invoices",
    "items": "items", "products": "items", "customers": "customers", "suppliers": "suppliers",
    "categories": "categories", "users": "users", "vouchers": "voucher", "warehouses": "warehouses",
    "cashboxes": "cashboxes_banks", "banks": "cashboxes_banks", "cash_bank": "cashboxes_banks",
    "manufacturing": "manufacturing", "reports": "reports", "settings": "settings", "audit_log": "audit_log",
    "returns": "return_doc", "sales_returns": "sales_returns", "purchase_returns": "purchase_returns",
}

def _human_title(title: Any, fallback: str = "report") -> str:
    raw = str(title or "").strip()
    if not raw:
        return t(fallback, fallback)
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _TITLE_KEY_MAP:
        return t(_TITLE_KEY_MAP[key])
    for prefix in ("table_", "view_", "widget_", "page_", "tbl_"):
        stripped = key[len(prefix):] if key.startswith(prefix) else key
        if stripped in _TITLE_KEY_MAP:
            return t(_TITLE_KEY_MAP[stripped])
    if raw.replace("_", "").replace("-", "").isascii() and any(ch.isalpha() for ch in raw):
        return t(fallback, fallback)
    return raw


def _company_data(settings: Dict[str, Any]) -> Dict[str, str]:
    info = get_company_info() or {}
    return {
        "name": _value(info.get("name") or settings.get("company_name"), "نظام الراجحي"),
        "address": _value(info.get("address") or settings.get("company_address")),
        "phone": _value(info.get("phone") or settings.get("company_phone")),
        "email": _value(info.get("email") or settings.get("company_email")),
        "tax_number": _value(info.get("tax_number") or settings.get("tax_number")),
        "logo_path": _value(info.get("logo_path") or settings.get("logo_path")),
    }


def _company_header(settings: Dict[str, Any], title: str = "") -> str:
    title = _human_title(title, "مستند")
    data = _company_data(settings)
    logo_html = ""
    if data["logo_path"] and _bool_setting(settings, "show_logo", True):
        logo_html = f"<td class='brand-logo'><img src='{_s(_img_src(data['logo_path']))}' alt='logo'></td>"
    else:
        logo_html = "<td class='brand-logo placeholder'> </td>"

    tax_line = ""
    if data["tax_number"] and _bool_setting(settings, "show_tax_number", True):
        tax_line = f"<div class='muted'>{_s(t('tax_number'))}: {_s(data['tax_number'])}</div>"

    contacts = []
    if data["phone"]:
        contacts.append(_s(t("phone")) + ": " + _s(data["phone"]))
    if data["email"]:
        contacts.append(_s(t("email")) + ": " + _s(data["email"]))
    contact_line = " | ".join(contacts)

    main_html = f"""<td class='brand-main'>
                <div class='company-name'>{_s(data['name'])}</div>
                <div class='muted'>{_s(data['address'])}</div>
                <div class='muted'>{contact_line}</div>
                {tax_line}
            </td>"""
    meta_html = f"""<td class='brand-meta'>
                <div class='document-badge'>{_s(title)}</div>
                <div class='muted'>{_s(t('print_date'))}</div>
                <div class='strong'>{_print_meta_line()}</div>
            </td>"""
    cells = [logo_html, main_html, meta_html]
    if _reverse_header_layout(settings):
        cells = list(reversed(cells))
    return f"""
    <table class='brand-table' dir='{lang_direction()}'>
        <tr>{''.join(cells)}</tr>
    </table>
    """


def _meta_table(rows: List[List[tuple]]) -> str:
    out = []
    reverse = _reverse_meta_layout()
    for row in rows:
        row_items = list(row or [])
        if reverse:
            row_items = list(reversed(row_items))
        cells = []
        for label, value in row_items:
            cells.append(f"<td><span class='meta-label'>{_s(translate_text(label))}</span><span class='meta-value'>{_fmt(value)}</span></td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table class='meta-table' dir='{lang_direction()}'>" + "".join(out) + "</table>"


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


def _table(headers: List[str], rows: List[List[Any]], empty_text: str = t("no_data", "No data"), reverse_columns: Optional[bool] = None) -> str:
    """Render a professional RTL-safe table.

    Qt QTextDocument sometimes mirrors RTL table visual order differently between
    preview and PDF. We therefore reverse columns in the generated HTML by
    default, so the final PDF appears in the intended Arabic order. This can be
    disabled from printing settings with reverse_print_table_columns = false.
    """
    settings = _settings()
    if reverse_columns is None:
        reverse_columns = _bool_setting(settings, "reverse_print_table_columns", True)

    safe_headers = list(headers or [])
    safe_rows = [list(row or []) for row in (rows or [])]
    if reverse_columns and len(safe_headers) > 1:
        safe_headers = list(reversed(safe_headers))
        safe_rows = [list(reversed(row)) for row in safe_rows]

    head = "".join(f"<th>{_s(translate_text(h))}</th>" for h in safe_headers)
    body = []
    for row in safe_rows:
        # Keep row length aligned with header count for stable PDF rendering.
        if len(row) < len(safe_headers):
            row = row + [""] * (len(safe_headers) - len(row))
        elif len(row) > len(safe_headers) and safe_headers:
            row = row[:len(safe_headers)]
        
        cells = []
        for c in row:
            txt = str(c) if c is not None else ""
            if "<br>" in txt or "<span" in txt:
                cells.append(f"<td>{txt}</td>")
            else:
                cells.append(f"<td>{_fmt(c)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    if not body:
        body.append(f"<tr><td colspan='{max(1, len(safe_headers))}' class='empty-cell'>{_s(empty_text)}</td></tr>")
    return f"<table class='data-table' dir='{lang_direction()}'><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _summary_cards(summary: Optional[Dict[str, Any]]) -> str:
    if not summary:
        return ""
    cells = []
    for key, value in summary.items():
        cells.append(f"<td class='summary-card'><div class='summary-label'>{_s(translate_text(key))}</div><div class='summary-value'>{_s(value)}</div></td>")
    return "<table class='summary-table'><tr>" + "".join(cells) + "</tr></table>"


def _footer(settings: Dict[str, Any], default: str = "") -> str:
    text = settings.get("footer_text") or default or t("footer_thanks")
    return f"<div class='print-footer'>{_s(translate_text(text))}</div>"


def base_document(title: str, body_html: str, paper: str = "a4", settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or _settings()
    spec = _paper_spec(paper, settings)
    accent = _accent(settings)
    font_family = _font_family(settings)
    compact = " compact" if _bool_setting(settings, "compact_tables", False) else ""
    zebra = " zebra" if _bool_setting(settings, "zebra_rows", True) else ""

    # Use table-based layout because Qt QTextDocument renders it more reliably than flex/grid in PDF.
    return f"""<!DOCTYPE html>
<html dir='{lang_direction()}' lang='{current_html_lang()}'>
<head>
<meta charset='utf-8'>
<title>{_s(title)}</title>
<style>
@page {{ size: {spec['page']}; margin: {spec['margin']}; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #ffffff; color: #111827; direction: {lang_direction()}; }}
body {{ font-family: {font_family}; font-size: {spec['font']}; line-height: 1.45; }}
.sheet {{ width: {spec['width']}; margin: 0 auto; }}
.brand-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; border-bottom: 3px solid {accent}; background: #f8fafc; }}
.brand-table td {{ vertical-align: middle; padding: 8px 6px; border: none; }}
.brand-logo {{ width: 90px; text-align: center; }}
.brand-logo img {{ max-width: 78px; max-height: 70px; }}
.brand-logo.placeholder {{ border: 1px dashed #d1d5db; border-radius: 8px; }}
.brand-main {{ text-align: start; }}
.company-name {{ font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
.brand-meta {{ width: 165px; text-align: center; border-left: 1px solid #e5e7eb !important; border-right: 1px solid #e5e7eb !important; }}
.document-badge {{ display: inline-block; background: {accent}; color: #ffffff; padding: 7px 12px; border-radius: 999px; font-weight: 800; margin-bottom: 5px; }}
.muted {{ color: #64748b; font-size: 90%; }}
.strong {{ font-weight: 800; color: #111827; }}
.document-title {{ text-align: center; font-size: 18px; font-weight: 900; margin: 8px 0 10px; color: #0f172a; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px; direction: {lang_direction()}; }}
.meta-table td {{ border: 1px solid #dbe3ef; background: #f8fafc; padding: 7px 9px; width: 33.33%; }}
.meta-label {{ display: block; color: #64748b; font-size: 88%; margin-bottom: 2px; }}
.meta-value {{ display: block; font-weight: 800; color: #0f172a; }}
.data-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; direction: {lang_direction()}; border: 1px solid #cbd5e1; }}
.data-table th {{ background: {accent}; color: #ffffff; border: 1px solid {accent}; padding: 8px 5px; font-weight: 800; text-align: center; white-space: normal; }}
.data-table td {{ border: 1px solid #dbe3ef; padding: 7px 5px; text-align: center; vertical-align: middle; word-wrap: break-word; overflow-wrap: anywhere; }}
.data-table tbody tr:nth-child(even) td {{ background: #f8fafc; }}
.data-table tbody tr:nth-child(odd) td {{ background: #ffffff; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ page-break-inside: avoid; }}
.data-table .text-cell {{ text-align: start; }}
.empty-cell {{ color: #64748b; padding: 20px !important; }}
.summary-table {{ width: 100%; border-collapse: separate; border-spacing: 6px; margin: 9px 0; }}
.summary-card {{ border: 1px solid #dbe3ef; background: #f8fafc; border-radius: 10px; padding: 8px; text-align: center; }}
.summary-label {{ color: #64748b; font-size: 88%; }}
.summary-value {{ color: #0f172a; font-size: 115%; font-weight: 900; margin-top: 2px; }}
.totals-table {{ width: 42%; min-width: 260px; margin-right: auto; margin-top: 10px; border-collapse: collapse; }}
.totals-table td {{ border: 1px solid #dbe3ef; padding: 7px 9px; }}
.totals-table td:first-child {{ background: #f8fafc; color: #334155; font-weight: 700; }}
.totals-table td:last-child {{ text-align: left; font-weight: 800; }}
.totals-table tr.final td {{ background: #eaf2ff; color: #0f172a; font-size: 110%; }}
.totals-table tr.due td:last-child {{ color: #dc2626; }}
.notes-box {{ margin-top: 10px; border: 1px dashed #cbd5e1; background: #fcfdff; padding: 8px; min-height: 34px; }}
.qr-table {{ width: 100%; margin-top: 10px; border-collapse: collapse; }}
.qr-table td {{ text-align: center; border: none; color: #64748b; }}
.qr-table img {{ width: 88px; height: 88px; }}
.signatures {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
.signatures td {{ width: 50%; text-align: center; padding-top: 22px; border-top: 1px solid #475569; color: #334155; }}
.signatures td:first-child {{ padding-left: 30px; }}
.signatures td:last-child {{ padding-right: 30px; }}
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
    title = {"sale": t("sales_invoices"), "purchase": t("purchase_invoices")}.get(inv_type, t("invoice"))
    ref = invoice.get("reference") or invoice.get("ref") or invoice.get("number") or invoice.get("id") or ""
    date = invoice.get("date") or invoice.get("created_at") or ""
    party_label = t("customers") if inv_type == "sale" else t("suppliers")
    party = invoice.get("party_name") or invoice.get("entity_name") or invoice.get("customer_name") or invoice.get("supplier_name") or t("cash", "Cash")
    warehouse = invoice.get("warehouse_name") or invoice.get("warehouse") or ""
    payment_method = invoice.get("payment_method") or invoice.get("payment") or ""
    user_name = invoice.get("user_name") or invoice.get("seller_name") or invoice.get("created_by") or ""

    raw_lines: Iterable[Any] = invoice.get("lines") or invoice.get("items") or []
    rows: List[List[Any]] = []
    for i, raw in enumerate(raw_lines, 1):
        line = raw if isinstance(raw, dict) else {}
        unit_text = _line_value(line, "unit", "unit_display", "unit_name")
        factor = _line_value(line, "conversion_factor", default="")
        base_qty = _line_value(line, "quantity_in_base", "base_qty", default="")
        unit_details = unit_text
        if factor not in ("", "1", 1, "1.0") or base_qty not in ("", None):
            unit_details = f"{unit_text}<br><span class='muted'>{_s(t('conversion_factor'))}: {factor or '1'} | {_s(t('base_quantity'))}: {base_qty}</span>"
        rows.append([
            i,
            _line_value(line, "barcode", "item_barcode", "code"),
            _line_value(line, "item_name", "name", "description"),
            unit_details,
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
            qr_html = f"<table class='qr-table'><tr><td><img src='{qr_uri}'><div>{_s(t('document'))}</div></td></tr></table>"

    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(t("document", "رقم المستند"), ref), (t("date", "التاريخ"), date), (party_label, party)],
        [(t("warehouses", "المستودع"), warehouse), (t("payment_method", "طريقة الدفع"), payment_method), (t("user", "المستخدم"), user_name)],
    ])}
    {_table(["#", t("barcode"), t("item"), t("unit"), t("quantity"), t("unit_price"), t("discount") + " %", t("tax") + " %", t("total")], rows, t("no_items", "No items"))}
    {_totals_table([
        (t("subtotal", "الإجمالي قبل الخصم"), invoice.get("total_before_discount", invoice.get("subtotal", "")), ""),
        (t("discount", "الخصم"), invoice.get("discount", invoice.get("discount_amount", 0)), ""),
        (t("tax", "الضريبة"), invoice.get("tax_amount", invoice.get("tax", 0)), ""),
        (t("total", "الإجمالي النهائي"), invoice.get("total", ""), "final"),
        (t("paid", "المدفوع"), invoice.get("paid") or invoice.get("paid_amount", 0), ""),
        (t("remaining", "المتبقي"), invoice.get("remaining", ""), "due"),
    ])}
    <div class='notes-box'><b>{_s(t('notes'))}:</b> {_s(invoice.get('notes', ''))}</div>
    {qr_html}
    <table class='signatures hide-thermal'><tr><td>{_s(t('receiver_signature', 'Receiver signature'))}</td><td>{_s(t('accountant', 'Accountant'))}</td></tr></table>
    {_footer(settings, t("footer_thanks"))}
    """
    return base_document(f"{title} {ref}", body, paper, settings)


def voucher_html(voucher: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "voucher")
    vtype = voucher.get("type")
    title = {"receipt": t("receipt_vouchers"), "payment": t("payment_vouchers"), "expense": t("expense_voucher", "Expense voucher")}.get(vtype, t("voucher"))
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(t("number", "الرقم"), voucher.get("id") or voucher.get("reference")), (t("date", "التاريخ"), voucher.get("date")), (t("amount", "المبلغ"), voucher.get("amount"))],
        [(t("party", "الطرف"), voucher.get("party_name", "")), (t("account", "الحساب"), voucher.get("account_name", "")), (t("user", "المستخدم"), voucher.get("user_name", ""))],
    ])}
    <div class='notes-box'><b>{_s(t('description', 'البيان'))}:</b> {_s(voucher.get('description', ''))}</div>
    <table class='signatures'><tr><td>{_s(t('receiver', 'المستلم'))}</td><td>{_s(t('accountant', 'Accountant'))}</td></tr></table>
    {_footer(settings, title)}
    """
    return base_document(title, body, paper, settings)


def return_html(data: Dict[str, Any], paper: str = "default") -> str:
    payload = dict(data or {})
    rtype = payload.get("type") or payload.get("return_type") or "sale_return"
    payload["type"] = "sale" if rtype in ("sale_return", "sale") else "purchase"
    payload["reference"] = payload.get("reference") or payload.get("return_number") or payload.get("id") or ""
    title = t("sales_returns") if payload["type"] == "sale" else t("purchase_returns")
    html = invoice_html(payload, _normalize_paper(paper, _settings(), "return"))
    return html.replace(t("sales_invoices"), title).replace(t("purchase_invoices"), title).replace("فاتورة بيع", title).replace("فاتورة شراء", title).replace("Sales invoice", title).replace("Purchase invoice", title).replace("Verkaufsrechnung", title).replace("Einkaufsrechnung", title)


def report_html(title: str, rows: List[List[Any]], headers: List[str], subtitle: str = "", summary: Optional[Dict[str, Any]] = None, paper: str = "default") -> str:
    settings = _settings()
    title = _human_title(title, "report")
    paper = _normalize_paper(paper, settings, "report")
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    <div class='muted' style='text-align:center;margin-bottom:8px;'>{_s(subtitle)}</div>
    {_summary_cards(summary)}
    {_table(headers, rows, t("no_data", "No data"))}
    {_footer(settings, t("report_generated", "Generated by Alrajhi Accounting"))}
    """
    return base_document(title, body, paper, settings)
