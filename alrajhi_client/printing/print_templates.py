# -*- coding: utf-8 -*-
"""Professional, settings-driven RTL HTML print templates.

All printable documents in the client should pass through these templates so PDF,
preview and direct-print output share the same header, typography, table style,
footer, paper sizing and company metadata.
"""
from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Optional
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import base64
from io import BytesIO
import datetime
import os



def _tr(key: str, **kwargs) -> str:
    """Translate template text using the configured print language.

    The UI language and the print/report language may differ per settings.
    Template generation must therefore avoid relying on the translator's global
    current UI language.
    """
    key = str(key)
    try:
        from i18n import translator as _translator
        try:
            from core.services.settings_service import settings_service
            lang = _translator.normalize_language(settings_service.print_language())
        except Exception:
            lang = _translator.DEFAULT_LANGUAGE
        table = getattr(_translator, '_translations', {})
        text = table.get(lang, {}).get(key) or table.get(_translator.DEFAULT_LANGUAGE, {}).get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
    except Exception:
        return key


def _settings_service():
    try:
        from core.services.settings_service import settings_service
        return settings_service
    except Exception:
        return None


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


def _image_data_uri(path: str) -> str:
    """Return an inline image URI suitable for browser HTML printing.

    Storing/printing the logo as a data URI is required in client-server mode:
    a filesystem path selected on one workstation is not guaranteed to exist on
    another workstation.  Existing data/file/http URIs remain supported.
    """
    value = str(path or '').strip()
    if not value:
        return ""
    if value.startswith('data:'):
        return value
    if value.startswith(('http://', 'https://', 'file:')):
        return value
    try:
        import mimetypes
        if os.path.exists(value):
            mime = mimetypes.guess_type(value)[0] or 'image/png'
            with open(value, 'rb') as fh:
                encoded = base64.b64encode(fh.read()).decode('ascii')
            return f'data:{mime};base64,{encoded}'
    except Exception:
        return ""
    return ""


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
        svc = _settings_service()
        if svc is None:
            return {}
        cfg = dict(svc.get_printing_settings() or {})
        # Printing must respect the same display-currency contract as the UI.
        # Values are formatting metadata only; templates never convert invoice
        # amounts because transaction documents already send display amounts.
        cfg.setdefault('display_currency', svc.get('display_currency', 'SYP') or 'SYP')
        cfg.setdefault('base_currency', svc.get('base_currency', 'SYP') or 'SYP')
        cfg.setdefault('currency_decimals', svc.get('currency_decimals', '2') or '2')
        cfg.setdefault('number_format', svc.get('number_format', 'western') or 'western')
        cfg.setdefault('currency_symbol', _CURRENCY_SYMBOLS.get(str(cfg.get('display_currency') or '').upper(), svc.get('currency_symbol', '')))
        return cfg
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
        elif doc_type == "pos_receipt":
            receipt_paper = settings.get("pos_receipt_paper") or settings.get("receipt_paper") or settings.get("thermal_size") or "80mm"
            paper = "thermal58" if "58" in str(receipt_paper).lower() else "thermal80"
        elif doc_type in ("restaurant_receipt", "restaurant_kitchen"):
            paper = settings.get("restaurant_receipt_template") or settings.get("restaurant_template") or settings.get("receipt_template") or settings.get("invoice_template") or "thermal"
        elif doc_type in ("inventory", "inventory_transfer", "inventory_balances", "inventory_movements", "inventory_ledger"):
            paper = settings.get("inventory_print_template") or settings.get("report_template") or settings.get("default_paper") or "a4"
        elif doc_type in ("manufacturing", "manufacturing_bom", "manufacturing_pick_ticket", "manufacturing_cost_report"):
            paper = settings.get("manufacturing_print_template") or settings.get("production_order_template") or settings.get("report_template") or settings.get("default_paper") or "a4"
        else:
            paper = settings.get("invoice_template") or settings.get("default_paper") or "a4"
    return str(paper or "a4").lower()


def _paper_spec(paper: str, settings: Dict[str, Any]) -> Dict[str, str]:
    paper = (paper or "a4").lower()
    thermal_size = str(settings.get("thermal_size", "80mm")).lower()
    if paper in ("80mm", "80", "thermal_80", "thermal-80"):
        paper = "thermal80"
    elif paper in ("58mm", "58", "thermal_58", "thermal-58"):
        paper = "thermal58"
    elif paper in ("thermal", "receipt"):
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







_CURRENCY_SYMBOLS = {
    'USD': '$',
    'SAR': '﷼',
    'SYP': 'ل.س',
    'EUR': '€',
    'GBP': '£',
    'AED': 'د.إ',
    'QAR': 'ر.ق',
    'KWD': 'د.ك',
    'OMR': 'ر.ع.',
}

_ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
_EASTERN_DIGITS = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')


def _clamp_int(value: Any, default: int = 2, minimum: int = 0, maximum: int = 6) -> int:
    try:
        num = int(str(value))
    except Exception:
        num = default
    return max(minimum, min(maximum, num))


def _currency_code(value: Any = None, settings: Optional[Dict[str, Any]] = None) -> str:
    raw = str(value or '').strip()
    if raw:
        aliases = {'ل.س': 'SYP', 'ليرة': 'SYP', 'ليرة سورية': 'SYP', '$': 'USD', '€': 'EUR', '﷼': 'SAR'}
        return aliases.get(raw, raw.upper() if raw.isascii() else raw)
    settings = settings or _settings()
    try:
        svc = _settings_service()
        if svc is not None:
            return str(svc.get('display_currency', settings.get('display_currency', 'SYP')) or 'SYP')
    except Exception:
        pass
    return str(settings.get('display_currency') or settings.get('currency') or settings.get('base_currency') or 'SYP')


def _document_currency(payload: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    payload = payload or {}
    explicit = payload.get('display_currency') or payload.get('currency') or payload.get('currency_code')
    return _currency_code(explicit, settings)


def _currency_symbol(currency_code: str, settings: Optional[Dict[str, Any]] = None) -> str:
    code = _currency_code(currency_code, settings)
    if code in _CURRENCY_SYMBOLS:
        return _CURRENCY_SYMBOLS[code]
    settings = settings or _settings()
    configured = str(settings.get('currency_symbol') or '').strip()
    return configured or code


def _currency_decimals(settings: Optional[Dict[str, Any]] = None) -> int:
    settings = settings or _settings()
    try:
        svc = _settings_service()
        if svc is not None:
            return _clamp_int(svc.get('currency_decimals', settings.get('currency_decimals', 2)), 2, 0, 6)
    except Exception:
        pass
    return _clamp_int(settings.get('currency_decimals', 2), 2, 0, 6)


def _quantity_decimals(settings: Optional[Dict[str, Any]] = None) -> int:
    settings = settings or _settings()
    try:
        svc = _settings_service()
        if svc is not None and hasattr(svc, 'quantity_decimals'):
            return _clamp_int(svc.quantity_decimals(), 3, 0, 6)
    except Exception:
        pass
    return _clamp_int(settings.get('quantity_decimals', 3), 3, 0, 6)


def _number_format(settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or _settings()
    try:
        svc = _settings_service()
        if svc is not None:
            return str(svc.get('number_format', settings.get('number_format', 'western')) or 'western')
    except Exception:
        pass
    return str(settings.get('number_format', 'western') or 'western')


def _decimal_or_none(value: Any) -> Optional[Decimal]:
    if value in (None, ''):
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().translate(_ARABIC_DIGITS)
    if not text:
        return None
    # Some legacy payloads may carry tiny negative values as 1E-22- after str()
    # or UI mirroring; normalize them before Decimal parsing.
    negative = False
    if text.endswith('-'):
        negative = True
        text = text[:-1]
    if text.startswith('-'):
        negative = True
        text = text[1:]
    for token in list(_CURRENCY_SYMBOLS.keys()) + list(_CURRENCY_SYMBOLS.values()):
        text = text.replace(token, '')
    text = text.replace(',', '').replace(' ', '').replace('\u00a0', '')
    if not text:
        return None
    try:
        num = Decimal(text)
        return -num if negative else num
    except (InvalidOperation, ValueError):
        return None


def _localize_digits(text: str, settings: Optional[Dict[str, Any]] = None) -> str:
    fmt = _number_format(settings).lower()
    if fmt in ('arabic', 'eastern', 'eastern_arabic'):
        return text.translate(_EASTERN_DIGITS)
    return text


def _format_decimal(value: Any, decimals: int = 2, *, trim: bool = True, settings: Optional[Dict[str, Any]] = None) -> str:
    num = _decimal_or_none(value)
    if num is None:
        return _s(value)
    decimals = _clamp_int(decimals, 2, 0, 6)
    quantum = Decimal('1') if decimals == 0 else Decimal('1').scaleb(-decimals)
    # Suppress binary/Decimal residue such as 549999.999999999999999999999 or 1E-22-.
    if abs(num) < quantum:
        num = Decimal('0')
    try:
        num = num.quantize(quantum, rounding=ROUND_HALF_UP)
    except Exception:
        pass
    formatted = f"{num:,.{decimals}f}"
    if trim and decimals > 0:
        formatted = formatted.rstrip('0').rstrip('.')
    if formatted == '-0':
        formatted = '0'
    return _localize_digits(formatted, settings)


def _format_quantity(value: Any, settings: Optional[Dict[str, Any]] = None) -> str:
    try:
        from core.money_display_policy import format_quantity as _policy_format_quantity
        return _policy_format_quantity(value, decimals=_quantity_decimals(settings), payload=settings or _settings())
    except Exception:
        return _format_decimal(value, _quantity_decimals(settings), trim=True, settings=settings)


def _format_percent(value: Any, settings: Optional[Dict[str, Any]] = None) -> str:
    return _format_decimal(value, 2, trim=True, settings=settings)


def _format_money(value: Any, currency_code: Optional[str] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or _settings()
    code = _currency_code(currency_code, settings)
    try:
        from core.money_display_policy import format_money as _policy_format_money
        return _policy_format_money(value, code, decimals=_currency_decimals(settings), payload=settings)
    except Exception:
        amount = _format_decimal(value, _currency_decimals(settings), trim=False, settings=settings)
        symbol = _currency_symbol(code, settings)
        return f"{amount} {symbol}".strip()


def _currency_label(currency_code: Optional[str] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    code = _currency_code(currency_code, settings)
    symbol = _currency_symbol(code, settings)
    return f"{code} {symbol}".strip() if symbol != code else code


def _convert_money_for_print(value: Any, from_currency: str, to_currency: str, date: Any = None, rate_hint: Any = None) -> Any:
    """Convert persisted POS/base amounts to the document display currency.

    Normal invoice/return documents already send display amounts to templates.
    POS receipts are different: POSService persists totals and line prices in
    the storage/base currency, while the cashier sees display currency.  Receipt
    printing must therefore convert only in the explicit POS receipt path.
    """
    if value in (None, ''):
        return value
    try:
        from currency import currency as _currency
        return _currency.convert(_decimal_or_none(value) or Decimal('0'), from_currency, to_currency, date=str(date or '') or None)
    except Exception:
        amount = _decimal_or_none(value) or Decimal('0')
        rate = _decimal_or_none(rate_hint)
        if from_currency == 'USD' and to_currency != 'USD' and rate not in (None, Decimal('0')):
            return amount * rate
        if from_currency != 'USD' and to_currency == 'USD' and rate not in (None, Decimal('0')):
            return amount / rate
        return value


def _pos_receipt_display_payload(invoice: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(invoice or {})
    display_currency = _currency_code(
        payload.get('display_currency') or payload.get('original_currency') or payload.get('currency') or settings.get('display_currency'),
        settings,
    )
    # POSService names totals ``*_usd`` and stores them in the application
    # storage currency.  The historic storage currency is USD even when the
    # active SettingsService default says SYP in newer installs.  Therefore the
    # explicit POS receipt path treats persisted POS invoices as USD unless the
    # document itself says it is already in the display currency.
    source_currency = _currency_code(payload.get('storage_currency') or payload.get('base_currency') or 'USD', settings)
    if display_currency == source_currency:
        source_currency = display_currency
    rate = _decimal_or_none(payload.get('exchange_rate_to_usd'))
    if display_currency != 'USD' and rate not in (None, Decimal('0'), Decimal('1')):
        source_currency = 'USD'

    if source_currency != display_currency:
        money_keys = (
            'total', 'subtotal', 'total_before_discount', 'discount', 'discount_amount',
            'tax', 'tax_amount', 'paid', 'paid_amount', 'remaining', 'balance',
        )
        for key in money_keys:
            if key in payload and payload.get(key) not in (None, ''):
                payload[key] = _convert_money_for_print(payload.get(key), source_currency, display_currency, payload.get('date'), payload.get('exchange_rate_to_usd'))
        lines = []
        for raw in list(payload.get('lines') or payload.get('items') or []):
            line = dict(raw or {}) if isinstance(raw, dict) else {}
            for key in ('unit_price', 'price', 'total', 'line_total', 'subtotal', 'discount_amount', 'tax_amount'):
                if key in line and line.get(key) not in (None, ''):
                    line[key] = _convert_money_for_print(line.get(key), source_currency, display_currency, payload.get('date'), payload.get('exchange_rate_to_usd'))
            lines.append(line)
        if lines:
            payload['lines'] = lines
            payload['items'] = lines
    payload['display_currency'] = display_currency
    payload['currency'] = display_currency
    payload['currency_code'] = display_currency
    payload['table_contract_id'] = payload.get('table_contract_id') or 'pos.lines'
    payload['line_table_contract_id'] = payload.get('line_table_contract_id') or 'pos.lines'
    payload['_print_context'] = 'pos_receipt'
    payload.setdefault('type', 'sale')
    payload.setdefault('status', payload.get('payment_status') or 'paid')
    payload.setdefault('reference', payload.get('ref') or payload.get('number') or payload.get('id') or '')
    return payload


def _localized_payment_method(value: Any) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    key = raw.lower().replace(' ', '_').replace('-', '_')
    mapping = {
        'cash': 'payment_cash',
        'cash_payment': 'payment_cash',
        'card': 'payment_card',
        'bank_card': 'payment_card',
        'credit_card': 'payment_card',
        'bank': 'payment_bank_transfer',
        'bank_transfer': 'payment_bank_transfer',
        'transfer': 'payment_bank_transfer',
        'credit': 'payment_credit',
        'credit_only': 'payment_credit',
        'deferred': 'payment_credit',
        'mixed': 'payment_mixed',
    }
    tr_key = mapping.get(key)
    return _tr(tr_key) if tr_key else raw


def _localized_status(value: Any) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    key = raw.lower().replace(' ', '_').replace('-', '_')
    mapping = {
        'paid': 'paid',
        'unpaid': 'remaining',
        'partial': 'partial_payment_confirm',
        'partially_paid': 'partial_payment_confirm',
        'draft': 'draft',
        'posted': 'status',
        'cancelled': 'status_cancelled',
        'canceled': 'status_cancelled',
    }
    tr_key = mapping.get(key)
    return _tr(tr_key) if tr_key else raw


def _line_amount(line: Dict[str, Any]) -> Any:
    explicit = _line_value(line, 'line_total', 'total', 'subtotal', default=None)
    if explicit not in (None, ''):
        return explicit
    qty = _decimal_or_none(_line_value(line, 'quantity', 'qty', default=0)) or Decimal('0')
    price = _decimal_or_none(_line_value(line, 'unit_price', 'price', default=0)) or Decimal('0')
    gross = qty * price
    discount_amount = _decimal_or_none(_line_value(line, 'discount_amount', default=None))
    if discount_amount is None:
        discount_percent = _decimal_or_none(_line_value(line, 'discount_percent', 'discount_pct', 'discount', default=0)) or Decimal('0')
        discount_amount = gross * discount_percent / Decimal('100')
    taxable = gross - discount_amount
    tax_amount = _decimal_or_none(_line_value(line, 'tax_amount', default=None))
    if tax_amount is None:
        tax_percent = _decimal_or_none(_line_value(line, 'tax_percent', 'tax_pct', 'tax', default=0)) or Decimal('0')
        tax_amount = taxable * tax_percent / Decimal('100')
    return taxable + tax_amount


def _document_language() -> str:
    try:
        from i18n.translator import normalize_language
        svc = _settings_service()
        return normalize_language(svc.print_language() if svc is not None else "ar")
    except Exception:
        return "ar"


def _document_direction() -> str:
    try:
        from i18n.translator import language_direction
        return language_direction(_document_language())
    except Exception:
        return "rtl"


_TITLE_MAP = {
    "invoices": "invoices",
    "invoice": "invoices",
    "sales_invoices": "sales_invoices",
    "sale_invoices": "sales_invoices",
    "purchase_invoices": "purchase_invoices",
    "purchases_invoices": "purchase_invoices",
    "items": "items",
    "products": "items",
    "customers": "customers",
    "suppliers": "suppliers",
    "categories": "categories",
    "users": "users",
    "vouchers": "vouchers",
    "warehouses": "warehouses",
    "cashboxes": "cashboxes",
    "banks": "cashboxes",
    "cash_bank": "cashboxes",
    "manufacturing": "manufacturing",
    "reports": "reports",
    "settings": "settings",
    "audit_log": "audit_log",
    "returns": "returns",
    "sales_returns": "sales_returns",
    "purchase_returns": "purchase_returns",
    "restaurant_receipt": "restaurant_receipt",
    "restaurant_kitchen_ticket": "restaurant_kitchen_ticket",
}

def _human_title(title: Any, fallback: Optional[str] = None) -> str:
    fallback = fallback or _tr("print_report_default")
    raw = str(title or "").strip()
    if not raw:
        return fallback
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _TITLE_MAP:
        return _tr(_TITLE_MAP[key])
    # Hide internal object names like table_items or view_invoices.
    for prefix in ("table_", "view_", "widget_", "page_", "tbl_"):
        if key.startswith(prefix) and key[len(prefix):] in _TITLE_MAP:
            return _tr(_TITLE_MAP[key[len(prefix):]])
    # If it is a technical ASCII identifier, do not print it above the date.
    if raw.replace("_", "").replace("-", "").isascii() and any(ch.isalpha() for ch in raw):
        return fallback
    return raw


def _company_data(settings: Dict[str, Any]) -> Dict[str, str]:
    svc = _settings_service()
    try:
        info = svc.company_info() if svc is not None else {}
    except Exception:
        info = {}
    logo_data_uri = _value(info.get("logo_data_uri") or settings.get("logo_data_uri"))
    logo_path = _value(info.get("logo_path") or info.get("logo") or settings.get("logo_path"))
    logo_src = logo_data_uri or _image_data_uri(logo_path)
    try:
        from pathlib import Path as _Path
        if not logo_src and (not logo_path or not _Path(logo_path).exists()):
            from brand_assets import logo_png
            logo_path = logo_png(512)
            logo_src = _image_data_uri(logo_path) or _img_src(logo_path)
    except Exception:
        logo_src = logo_src or (_img_src(logo_path) if logo_path else "")
    return {
        "name": _value(info.get("name") or settings.get("company_name"), _tr("app_title")),
        "address": _value(info.get("address") or settings.get("company_address")),
        "phone": _value(info.get("phone") or settings.get("company_phone")),
        "email": _value(info.get("email") or settings.get("company_email")),
        "tax_number": _value(info.get("tax_number") or settings.get("tax_number")),
        "logo_path": logo_path,
        "logo_src": logo_src,
        "logo_data_uri": logo_data_uri,
        "commercial_register": _value(info.get("commercial_register") or settings.get("commercial_register")),
        "website": _value(info.get("website") or settings.get("company_website")),
    }


def _company_header(settings: Dict[str, Any], title: str = "") -> str:
    """Render the single document header used by all browser HTML prints.

    Phase 244 keeps the document name in one place only: the badge inside the
    header.  Individual templates must not add a second large title below the
    company block; that was the source of the duplicated title visible in
    browser output.
    """
    title = _human_title(title, _tr("print_document"))
    data = _company_data(settings)
    logo_src = data.get("logo_src") or _image_data_uri(data.get("logo_path")) or _img_src(data.get("logo_path", ""))
    logo_html = ""
    if logo_src and _bool_setting(settings, "show_logo", True):
        logo_html = f"<td class='brand-logo'><img src='{_s(logo_src)}' alt='logo'></td>"

    # Company identity lines are settings-governed and loaded through the SettingsService/SettingsGateway contract, so local, server
    # and client modes share
    # the same browser HTML contract across Arabic, English and German prints.
    name_line = f"<div class='company-name'>{_s(data['name'])}</div>" if _bool_setting(settings, "show_company_name", True) else ""
    address_line = f"<div class='company-line'>{_s(data['address'])}</div>" if data.get("address") and _bool_setting(settings, "show_address", True) else ""
    tax_line = ""
    if data["tax_number"] and _bool_setting(settings, "show_tax_number", True):
        tax_line = f"<span>{_s(_tr('print_tax_number'))}: {_s(data['tax_number'])}</span>"
    cr_line = f"<span>{_s(_tr('print_commercial_register'))}: {_s(data['commercial_register'])}</span>" if data.get("commercial_register") and _bool_setting(settings, "show_commercial_register", True) else ""
    website_line = f"<span>{_s(data['website'])}</span>" if data.get("website") and _bool_setting(settings, "show_website", True) else ""

    contacts = []
    if data["phone"] and _bool_setting(settings, "show_phone", True):
        contacts.append(_tr("print_phone") + ": " + _s(data["phone"]))
    if data["email"] and _bool_setting(settings, "show_email", True):
        contacts.append(_tr("print_email") + ": " + _s(data["email"]))
    contact_line = "<span>" + "</span><span>".join(contacts) + "</span>" if contacts else ""

    identity_parts = "".join(part for part in (contact_line, tax_line, cr_line, website_line) if part)
    identity_line = f"<div class='company-identity'>{identity_parts}</div>" if identity_parts else ""

    return f"""
    <table class='brand-table'>
        <tr>
            {logo_html}
            <td class='brand-main'>
                {name_line}
                {address_line}
                {identity_line}
            </td>
            <td class='brand-meta'>
                <div class='document-badge'>{_s(title)}</div>
                <div class='print-meta-label'>{_s(_tr("print_date_label"))}</div>
                <div class='print-meta-value'>{_print_meta_line()}</div>
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


def _totals_table(rows: List[tuple], currency_code: Optional[str] = None, monetary: bool = False) -> str:
    body = []
    settings = _settings()
    for label, value, klass in rows:
        cls = f" class='{_s(klass)}'" if klass else ""
        rendered = _format_money(value, currency_code, settings) if monetary else _s(value)
        body.append(f"<tr{cls}><td>{_s(label)}</td><td>{rendered}</td></tr>")
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




def _contract_columns_for_print(contract_id: str):
    try:
        from workspace.tables import columns_for_output
        return list(columns_for_output(contract_id, "print"))
    except Exception:
        return []


def _contract_headers(contract_id: str) -> List[str]:
    headers = []
    for column in _contract_columns_for_print(contract_id):
        label_key = getattr(column, "label_key", "") or getattr(column, "key", "")
        headers.append("#" if label_key == "#" else _tr(label_key))
    return headers


def _variant_display(line: Dict[str, Any]) -> Any:
    value = _line_value(line, "variant", "variant_name", "variant_label", "matched_variant", default="")
    if value:
        if isinstance(value, dict):
            return value.get("label") or value.get("name") or " / ".join(str(value.get(k) or "") for k in ("color", "size") if value.get(k))
        return value
    color = _line_value(line, "color", "variant_color", default="")
    size = _line_value(line, "size", "variant_size", default="")
    return " / ".join(str(x) for x in (color, size) if x not in (None, ""))


def _contract_cell_value(column_key: str, line: Dict[str, Any], row_number: int, currency_code: Optional[str], settings: Dict[str, Any], *, context: str = "") -> Any:
    key = str(column_key or "")
    if key == "row":
        return row_number
    if key == "barcode":
        return _line_value(line, "barcode", "item_barcode", "code")
    if key == "item":
        return _line_value(line, "item_name", "name", "description")
    if key == "variant":
        return _variant_display(line)
    if key == "unit":
        return _line_value(line, "unit", "unit_display", "unit_name")
    if key in {"qty", "quantity", "base_qty", "available", "original_qty", "previous_qty", "returnable_qty", "reorder_level", "line_count", "guests"}:
        aliases = {
            "qty": ("quantity", "qty"),
            "quantity": ("quantity", "qty"),
            "base_qty": ("base_qty", "quantity_in_base"),
            "available": ("available", "available_qty"),
            "original_qty": ("original_qty", "sold_qty", "purchased_qty"),
            "previous_qty": ("previous_qty", "previous_return_qty"),
            "returnable_qty": ("returnable_qty", "remaining_qty"),
            "line_count": ("line_count", "lines_count"),
            "guests": ("guests",),
        }
        return _format_quantity(_line_value(line, *aliases.get(key, (key,)), default=""), settings)
    if key in {"price", "unit_price"}:
        return _format_money(_line_value(line, "unit_price", "price", default="0"), currency_code, settings)
    if key == "cost":
        return _format_money(_line_value(line, "cost", "unit_cost", "purchase_price", "unit_price", "price", default="0"), currency_code, settings)
    if key in {"total", "line_total"}:
        return _format_money(_line_value(line, "total", "line_total", default=_line_amount(line)), currency_code, settings)
    if key == "discount":
        return _format_percent(_line_value(line, "discount_percent", "discount_pct", "discount", default="0"), settings)
    if key == "tax":
        return _format_percent(_line_value(line, "tax_percent", "tax_pct", "tax", default="0"), settings)
    if key == "batch":
        return _line_value(line, "batch", "batch_no", "lot", default="")
    if key == "expiry":
        return _line_value(line, "expiry", "expiry_date", default="")
    if key == "notes":
        return _line_value(line, "notes", "kitchen_label", default="")
    if key == "reason":
        return _line_value(line, "reason", default="")
    if key == "restock":
        return _line_value(line, "restock", "restocked", default="")
    if key == "modifiers":
        value = _line_value(line, "modifiers", "modifier_names", "options", default="")
        if isinstance(value, (list, tuple)):
            return "، ".join(str(v) for v in value if str(v).strip())
        return value
    if key == "status":
        return _restaurant_status(_line_value(line, "status", "kitchen_status", "preparation_status", default=""))
    if key == "barcode_scope":
        return _line_value(line, "barcode_scope", default="")
    if key == "original_invoice":
        return _line_value(line, "original_invoice", "original_invoice_no", default="")
    return _line_value(line, key, default="")


def _contract_table(contract_id: str, lines: Iterable[Any], currency_code: Optional[str], settings: Dict[str, Any], *, context: str = "", empty_text: str = "") -> tuple[List[str], List[List[Any]]]:
    columns = _contract_columns_for_print(contract_id)
    if not columns:
        return [], []
    headers = ["#" if column.label_key == "#" else _tr(column.label_key) for column in columns]
    rows: List[List[Any]] = []
    for i, raw in enumerate(lines or [], 1):
        line = raw if isinstance(raw, dict) else {}
        rows.append([_contract_cell_value(column.key, line, i, currency_code, settings, context=context) for column in columns])
    return headers, rows

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
    thermal_show_logo = _bool_setting(settings, "thermal_show_logo", _bool_setting(settings, "show_logo", True))
    thermal_logo_display = "table-cell" if thermal_show_logo else "none"

    # Use table-based layout because Qt QTextDocument renders it more reliably than flex/grid in PDF.
    return f"""<!DOCTYPE html>
<html dir='{doc_dir}' lang='{lang}'>
<head>
<meta charset='utf-8'>
<title>{_s(title)}</title>
<style>
@page {{ size: {spec['page']}; margin: {spec['margin']}; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; color: #111827; direction: {doc_dir}; }}
html {{ background: #eef2f7; }}
body {{ font-family: {font_family}; font-size: {spec['font']}; line-height: 1.45; background: #eef2f7; }}
.sheet {{ width: {spec['width']}; margin: 14px auto; background: #ffffff; padding: 11mm; box-shadow: 0 10px 30px rgba(15, 23, 42, .16); border-radius: 10px; }}
.brand-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; border: 1px solid #dbe3ef; border-top: 5px solid {accent}; background: #ffffff; }}
.brand-table td {{ vertical-align: middle; padding: 10px 9px; border: none; }}
.brand-logo {{ width: 100px; text-align: center; border-{opposite_align}: 1px solid #e5e7eb !important; }}
.brand-logo img {{ max-width: 82px; max-height: 76px; object-fit: contain; }}
.brand-main {{ text-align: {text_align}; }}
.company-name {{ font-size: 21px; font-weight: 900; color: #0f172a; margin-bottom: 3px; letter-spacing: -.2px; }}
.company-line {{ color: #475569; font-size: 92%; margin: 2px 0; }}
.company-identity {{ color: #64748b; font-size: 88%; margin-top: 3px; }}
.company-identity span {{ display: inline-block; margin-{opposite_align}: 10px; white-space: nowrap; }}
.brand-meta {{ width: 170px; text-align: center; background: #f8fafc; border-{text_align}: 1px solid #e5e7eb !important; }}
.document-badge {{ display: inline-block; background: {accent}; color: #ffffff; padding: 7px 13px; border-radius: 999px; font-weight: 900; margin-bottom: 6px; min-width: 120px; }}
.print-meta-label {{ color: #64748b; font-size: 86%; }}
.print-meta-value {{ font-weight: 900; color: #111827; }}
.muted {{ color: #64748b; font-size: 90%; }}
.strong {{ font-weight: 800; color: #111827; }}
.document-title {{ display: none; }}
.meta-table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin: 8px 0 12px; border: 1px solid #dbe3ef; border-radius: 8px; overflow: hidden; }}
.meta-table td {{ border-{opposite_align}: 1px solid #dbe3ef; border-bottom: 1px solid #dbe3ef; background: #f8fafc; padding: 7px 9px; width: 33.33%; }}
.meta-table tr:last-child td {{ border-bottom: none; }}
.meta-table td:last-child {{ border-{opposite_align}: none; }}
.meta-label {{ display: block; color: #64748b; font-size: 86%; margin-bottom: 2px; }}
.meta-value {{ display: block; font-weight: 850; color: #0f172a; }}
.data-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; direction: {doc_dir}; }}
.data-table th {{ background: {accent}; color: #ffffff; border: 1px solid {accent}; padding: 7px 5px; font-weight: 850; text-align: center; white-space: normal; }}
.data-table td {{ border: 1px solid #dbe3ef; padding: 6px 5px; text-align: center; vertical-align: middle; word-wrap: normal; overflow-wrap: normal; font-variant-numeric: tabular-nums; }}
.zebra .data-table tbody tr:nth-child(even) td {{ background: #f8fafc; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ page-break-inside: avoid; }}
.data-table .text-cell {{ text-align: {text_align}; }}
.empty-cell {{ color: #64748b; padding: 20px !important; }}
.summary-table {{ width: 100%; border-collapse: separate; border-spacing: 6px; margin: 9px 0; }}
.summary-card {{ border: 1px solid #dbe3ef; background: #f8fafc; border-radius: 10px; padding: 8px; text-align: center; }}
.summary-label {{ color: #64748b; font-size: 88%; }}
.summary-value {{ color: #0f172a; font-size: 115%; font-weight: 900; margin-top: 2px; }}
.totals-table {{ width: 42%; min-width: 270px; margin-{opposite_align}: auto; margin-{text_align}: 0; margin-top: 12px; border-collapse: collapse; border: 1px solid #dbe3ef; }}
.totals-table td {{ border-bottom: 1px solid #dbe3ef; padding: 7px 10px; }}
.totals-table tr:last-child td {{ border-bottom: none; }}
.totals-table td:first-child {{ background: #f8fafc; color: #334155; font-weight: 750; }}
.totals-table td:last-child {{ text-align: {opposite_align}; font-weight: 900; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.totals-table tr.final td {{ background: #eaf2ff; color: #0f172a; font-size: 111%; }}
.totals-table tr.due td:last-child {{ color: #dc2626; }}
.notes-box {{ margin-top: 12px; border: 1px dashed #cbd5e1; background: #fcfdff; padding: 9px; min-height: 34px; border-radius: 8px; }}
.qr-table {{ width: 100%; margin-top: 10px; border-collapse: collapse; }}
.qr-table td {{ text-align: center; border: none; color: #64748b; }}
.qr-table img {{ width: 88px; height: 88px; }}
.signatures {{ width: 100%; border-collapse: separate; border-spacing: 34px 0; margin-top: 30px; }}
.signatures td {{ width: 50%; text-align: center; padding-top: 24px; border-top: 1px solid #475569; color: #334155; }}
.print-footer {{ margin-top: 18px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: center; color: #64748b; font-size: 90%; }}
.compact .sheet {{ padding: 8mm; }}
.compact .data-table th, .compact .data-table td, .compact .meta-table td, .compact .totals-table td {{ padding: 4px 3px; }}
.thermal80, .thermal58 {{ background: #ffffff; }}
.thermal80 .sheet, .thermal58 .sheet {{ width: {spec['width']}; margin: 0 auto; padding: 2mm; box-shadow: none; border-radius: 0; }}
.thermal80 .brand-table, .thermal58 .brand-table {{ border: none; border-bottom: 1px dashed #94a3b8; margin-bottom: 5px; }}
.thermal80 .brand-table td, .thermal58 .brand-table td {{ padding: 2px; }}
.thermal80 .brand-logo, .thermal58 .brand-logo {{ display: {thermal_logo_display}; width: 34px; text-align: center; border: none !important; }}
.thermal80 .brand-logo img, .thermal58 .brand-logo img {{ max-width: 30px; max-height: 30px; object-fit: contain; }}
.thermal80 .brand-meta, .thermal58 .brand-meta {{ display: table-cell; width: auto; background: transparent; border: none !important; }}
.thermal80 .document-badge, .thermal58 .document-badge {{ background: transparent; color: #111827; padding: 0; border-radius: 0; font-size: 11px; min-width: 0; }}
.thermal80 .print-meta-label, .thermal80 .print-meta-value, .thermal58 .print-meta-label, .thermal58 .print-meta-value {{ display: none; }}
.thermal80 .company-name, .thermal58 .company-name {{ font-size: 11px; text-align: center; }}
.thermal80 .company-line, .thermal80 .company-identity, .thermal58 .company-line, .thermal58 .company-identity {{ font-size: 8px; text-align: center; }}
.thermal80 .company-identity span, .thermal58 .company-identity span {{ margin: 0 2px; white-space: normal; }}
.thermal80 .meta-table, .thermal58 .meta-table {{ border-radius: 0; margin: 4px 0; }}
.thermal80 .meta-table td, .thermal58 .meta-table td {{ display: table-cell; padding: 2px; font-size: 8px; }}
.thermal80 .data-table th, .thermal80 .data-table td, .thermal58 .data-table th, .thermal58 .data-table td {{ padding: 2px; font-size: 8px; }}
.thermal80 .totals-table, .thermal58 .totals-table {{ width: 100%; min-width: 0; margin: 5px 0 0; }}
.thermal80 .notes-box, .thermal58 .notes-box {{ padding: 3px; min-height: 0; border-radius: 0; }}
.thermal80 .signatures, .thermal58 .signatures {{ display: none; }}
.thermal80 .hide-thermal, .thermal58 .hide-thermal {{ display: none; }}
@media print {{
  html, body {{ background: #ffffff; }}
  .sheet {{ width: 100%; margin: 0; padding: 0; box-shadow: none; border-radius: 0; }}
  .no-print {{ display: none !important; }}
}}
</style>
</head>
<body class='{_s(spec['class'])}{compact}{zebra}'>
<div class='sheet'>
{body_html}
</div>
</body>
</html>"""


def invoice_html(invoice: Dict[str, Any], paper: str = "default") -> str:
    invoice = dict(invoice or {})
    settings = _settings()
    is_pos_receipt = invoice.get('_print_context') == 'pos_receipt' or invoice.get('receipt_type') == 'pos'
    if is_pos_receipt:
        settings['thermal_show_logo'] = bool(settings.get('pos_receipt_show_logo', settings.get('thermal_show_logo', settings.get('show_logo', True))))
        settings['show_qr'] = bool(settings.get('pos_receipt_show_qr', settings.get('show_qr', True)))
    paper = _normalize_paper(paper, settings, "pos_receipt" if is_pos_receipt else "invoice")
    inv_type = invoice.get("type") or invoice.get("inv_type") or "sale"
    title = {"sale": _tr("sales_invoice"), "purchase": _tr("purchase_invoice")}.get(inv_type, _tr("invoice"))
    ref = invoice.get("reference") or invoice.get("ref") or invoice.get("number") or invoice.get("id") or ""
    date = invoice.get("date") or invoice.get("created_at") or ""
    party_label = _tr("print_party_customer") if inv_type == "sale" else _tr("print_party_supplier")
    if inv_type == "sale":
        party = invoice.get("customer_name") or invoice.get("party_name") or invoice.get("entity_name") or invoice.get("supplier_name") or _tr("print_cash_party")
    else:
        party = invoice.get("supplier_name") or invoice.get("party_name") or invoice.get("entity_name") or invoice.get("customer_name") or _tr("print_cash_party")
    warehouse = invoice.get("warehouse_name") or invoice.get("warehouse") or ""
    payment_method = _localized_payment_method(invoice.get("payment_method") or invoice.get("payment") or "")
    user_name = invoice.get("user_name") or invoice.get("seller_name") or invoice.get("created_by") or ""
    status = _localized_status(invoice.get("status") or invoice.get("state") or "")
    currency_code = _document_currency(invoice, settings)
    currency_label = _currency_label(currency_code, settings)

    raw_lines: Iterable[Any] = invoice.get("lines") or invoice.get("items") or []
    contract_id = (
        invoice.get("line_table_contract_id")
        or invoice.get("table_contract_id")
        or ("pos.lines" if is_pos_receipt else ("purchase_invoices.lines" if inv_type == "purchase" else "sales_invoices.lines"))
    )
    table_headers, rows = _contract_table(str(contract_id or ""), raw_lines, currency_code, settings, context="pos" if is_pos_receipt else inv_type)
    if not table_headers:
        rows = []
        for i, raw in enumerate(raw_lines, 1):
            line = raw if isinstance(raw, dict) else {}
            if is_pos_receipt:
                rows.append([
                    i,
                    _line_value(line, "item_name", "name", "description"),
                    _format_quantity(_line_value(line, "quantity", "qty"), settings),
                    _format_money(_line_value(line, "unit_price", "price"), currency_code, settings),
                    _format_money(_line_amount(line), currency_code, settings),
                ])
            else:
                rows.append([
                    i,
                    _line_value(line, "barcode", "item_barcode", "code"),
                    _line_value(line, "item_name", "name", "description"),
                    _line_value(line, "unit", "unit_display", "unit_name"),
                    _format_quantity(_line_value(line, "quantity", "qty"), settings),
                    _format_money(_line_value(line, "unit_price", "price"), currency_code, settings),
                    _format_percent(_line_value(line, "discount_percent", "discount_pct", "discount", default="0"), settings),
                    _format_percent(_line_value(line, "tax_percent", "tax_pct", "tax", default="0"), settings),
                    _format_money(_line_amount(line), currency_code, settings),
                ])

    qr_html = ""
    if _bool_setting(settings, "show_qr", True):
        qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
        qr_uri = _qr_data_uri(qr_payload)
        if qr_uri:
            qr_label = _s(_tr("print_document_qr"))
            qr_html = f"<table class='qr-table'><tr><td><img src='{qr_uri}'><div>{qr_label}</div></td></tr></table>"

    meta_rows = [
        [(_tr("print_document_number"), ref), (_tr("print_document_date"), date), (party_label, party)],
        [(_tr("print_warehouse"), warehouse), (_tr("print_payment_method"), payment_method), (_tr("currency"), currency_label)],
        [(_tr("print_user"), user_name), (_tr("status"), status), ("", "")],
    ]
    if not table_headers:
        table_headers = ["#", _tr("print_barcode"), _tr("print_item"), _tr("print_unit"), _tr("print_quantity"), _tr("print_price"), _tr("print_discount_percent"), _tr("print_tax_percent"), _tr("print_total")]
    if is_pos_receipt:
        meta_rows = [
            [(_tr("print_document_number"), ref), (_tr("print_document_date"), date)],
            [(_tr("print_payment_method"), payment_method), (_tr("currency"), currency_label)],
        ]
        if not table_headers:
            table_headers = ["#", _tr("print_item"), _tr("print_quantity"), _tr("print_price"), _tr("print_total")]

    body = f"""
    {_company_header(settings, title)}
    {_meta_table(meta_rows)}
    {_table(table_headers, rows, _tr("print_no_lines"))}
    {_totals_table([
        (_tr("print_subtotal"), invoice.get("total_before_discount", invoice.get("subtotal", "")), ""),
        (_tr("print_discount"), invoice.get("discount", invoice.get("discount_amount", 0)), ""),
        (_tr("print_tax"), invoice.get("tax_amount", invoice.get("tax", 0)), ""),
        (_tr("print_grand_total"), invoice.get("total", ""), "final"),
        (_tr("print_paid"), invoice.get("paid") or invoice.get("paid_amount", 0), ""),
        (_tr("print_remaining"), invoice.get("remaining", ""), "due"),
    ], currency_code=currency_code, monetary=True)}
    <div class='notes-box'><b>{_s(_tr("print_notes"))}:</b> {_s(invoice.get('notes', ''))}</div>
    {qr_html}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr("print_receiver_signature"))}</td><td>{_s(_tr("print_accountant_signature"))}</td></tr></table>
    {_footer(settings, _tr("print_thanks"))}
    """
    return base_document(f"{title} {ref}", body, paper, settings)


def pos_receipt_html(invoice: Dict[str, Any], paper: str = "default") -> str:
    """Browser-HTML thermal receipt for POS checkout.

    This is the dedicated POS path.  It applies POS receipt settings, keeps the
    company/logo header from the global print contract, and converts persisted
    POS/base amounts to the displayed receipt currency before formatting.
    """
    settings = _settings()
    payload = _pos_receipt_display_payload(invoice or {}, settings)
    return invoice_html(payload, _normalize_paper(paper, settings, "pos_receipt"))


def voucher_html(voucher: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "voucher")
    vtype = voucher.get("type")
    title = {"receipt": _tr("receipt_voucher"), "payment": _tr("payment_voucher"), "expense": _tr("expense_voucher")}.get(vtype, _tr("voucher"))
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr("print_number"), voucher.get("id") or voucher.get("reference")), (_tr("print_document_date"), voucher.get("date")), (_tr("amount"), voucher.get("amount"))],
        [(_tr("print_party"), voucher.get("party_name", "")), (_tr("print_account"), voucher.get("account_name", "")), (_tr("print_user"), voucher.get("user_name", ""))],
    ])}
    <div class='notes-box'><b>{_s(_tr("print_description"))}:</b> {_s(voucher.get('description', ''))}</div>
    <table class='signatures'><tr><td>{_s(_tr("print_receiver"))}</td><td>{_s(_tr("print_accountant_signature"))}</td></tr></table>
    {_footer(settings, title)}
    """
    return base_document(title, body, paper, settings)


def return_html(data: Dict[str, Any], paper: str = "default") -> str:
    payload = dict(data or {})
    rtype = payload.get("type") or payload.get("return_type") or "sale_return"
    payload["type"] = "sale" if rtype in ("sale_return", "sale") else "purchase"
    payload["reference"] = payload.get("reference") or payload.get("return_no") or payload.get("return_number") or payload.get("id") or ""
    title = _tr("sales_return") if payload["type"] == "sale" else _tr("purchase_return")
    html = invoice_html(payload, _normalize_paper(paper, _settings(), "return"))
    return html.replace(_tr("sales_invoice"), title).replace(_tr("purchase_invoice"), title)


def report_html(title: str, rows: List[List[Any]], headers: List[str], subtitle: str = "", summary: Optional[Dict[str, Any]] = None, paper: str = "default") -> str:
    settings = _settings()
    title = _human_title(title, _tr("print_report_default"))
    paper = _normalize_paper(paper, settings, "report")
    body = f"""
    {_company_header(settings, title)}
    <div class='muted' style='text-align:center;margin-bottom:8px;'>{_s(subtitle)}</div>
    {_summary_cards(summary)}
    {_table(headers, rows, _tr("print_no_data"))}
    {_footer(settings, _tr("print_report_generated_by"))}
    """
    return base_document(title, body, paper, settings)




def _restaurant_line_total(line: Dict[str, Any]) -> Any:
    try:
        return str(
            (_decimal_or_none(line.get("quantity") or line.get("qty") or "0") or Decimal("0"))
            * (_decimal_or_none(line.get("unit_price") or line.get("price") or "0") or Decimal("0"))
        )
    except Exception:
        return line.get("total") or line.get("line_total") or "0"


def _restaurant_payload_currency(data: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    payload = data or {}
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    balance = payload.get("balance") if isinstance(payload.get("balance"), dict) else {}
    for source in (payload, session, balance):
        value = source.get("display_currency") or source.get("currency") or source.get("currency_code")
        if value:
            return _currency_code(value, settings)
    return _currency_code(None, settings)


def _restaurant_money(value: Any, currency_code: Optional[str] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    return _format_money(value, currency_code, settings)


def _restaurant_qty(value: Any, settings: Optional[Dict[str, Any]] = None) -> str:
    return _format_quantity(value, settings)


def _restaurant_status(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    for key in (
        f"restaurant.kds.status.{raw}",
        f"restaurant.order_state.{raw}",
        f"restaurant.line_status.{raw}",
        f"status_{raw}",
    ):
        translated = _tr(key)
        if translated != key:
            return translated
    return raw.replace("_", " ")


def _restaurant_payment_method(value: Any) -> str:
    raw = str(value or "cash").strip().lower()
    aliases = {
        "cash": "payment.cash",
        "card": "payment.card",
        "bank": "payment.bank",
        "bank_transfer": "payment.bank",
        "mixed": "restaurant.payment.mixed",
        "split": "restaurant.payment.split",
        "credit": "payment.credit",
    }
    key = aliases.get(raw, raw)
    translated = _tr(key)
    return translated if translated != key else raw.replace("_", " ")


def _restaurant_printing_settings(kind: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    settings = dict(_settings())
    try:
        route = dict((payload or {}).get("print_route") or {}) if isinstance(payload, dict) else {}
        if route:
            settings["restaurant_print_route"] = route
            settings["restaurant_printer"] = route.get("printer") or ""
        svc = _settings_service()
        if svc is not None:
            restaurant_settings = svc.get_restaurant_settings() or {}
            printing = restaurant_settings.get("printing") or {}
            settings.update({k: v for k, v in printing.items() if k not in settings or v not in (None, "")})
            settings["display_currency"] = _restaurant_payload_currency(payload, settings)
            settings["currency_symbol"] = _currency_symbol(settings.get("display_currency"), settings)
            # Restaurant-specific logo / QR policy.  Customer receipts inherit the
            # normal company header.  Kitchen tickets are internal work tickets and
            # default to no logo unless explicitly enabled.
            if kind == "kitchen":
                show_logo = svc.get_bool("restaurant/printing/kitchen_show_logo", False)
                settings["show_logo"] = show_logo
                settings["thermal_show_logo"] = show_logo
                settings["show_qr"] = svc.get_bool("restaurant/printing/kitchen_show_qr", False)
            elif kind == "session_summary":
                settings["show_logo"] = svc.get_bool("restaurant/printing/session_summary_show_logo", settings.get("show_logo", True))
                settings["thermal_show_logo"] = svc.get_bool("restaurant/printing/session_summary_show_logo", settings.get("thermal_show_logo", True))
            else:
                settings["show_logo"] = svc.get_bool("restaurant/receipt_show_logo", settings.get("show_logo", True))
                settings["thermal_show_logo"] = svc.get_bool("restaurant/receipt_show_logo", settings.get("thermal_show_logo", True))
                settings["show_qr"] = svc.get_bool("restaurant/receipt_show_qr", settings.get("show_qr", True))
    except Exception:
        settings["display_currency"] = _restaurant_payload_currency(payload, settings)
    return settings


def _restaurant_lines(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    session = dict((data or {}).get("session") or data or {})
    return [line if isinstance(line, dict) else {} for line in (session.get("lines") or (data or {}).get("lines") or [])]


def _restaurant_payments(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    session = dict((data or {}).get("session") or data or {})
    return [p if isinstance(p, dict) else {} for p in (session.get("payments") or (data or {}).get("payments") or [])]


def _restaurant_split_bills(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    session = dict((data or {}).get("session") or data or {})
    return [s if isinstance(s, dict) else {} for s in ((data or {}).get("split_bills") or session.get("split_bills") or [])]


def restaurant_receipt_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Professional customer receipt for Restaurant POS sessions.

    Customer receipts must show prices, totals, payment split, displayed currency,
    company header/logo, and no internal kitchen metadata unless it helps the
    customer understand the order.
    """
    settings = _restaurant_printing_settings("receipt", data)
    paper = _normalize_paper(paper, settings, "restaurant_receipt")
    session = dict((data or {}).get("session") or data or {})
    balance = dict((data or {}).get("balance") or {})
    currency_code = _restaurant_payload_currency(data, settings)
    lines = _restaurant_lines(data or {})
    payments = _restaurant_payments(data or {})
    splits = _restaurant_split_bills(data or {})
    title = _tr("restaurant_receipt")
    ref = session.get("invoice_reference") or session.get("invoice_id") or session.get("receipt_no") or session.get("id") or ""
    table = session.get("table_name") or session.get("table_id") or ""
    opened = session.get("opened_at") or session.get("created_at") or ""
    closed = session.get("closed_at") or ""
    guests = session.get("guests") or ""
    waiter = session.get("waiter_name") or session.get("waiter_id") or session.get("user_name") or ""

    contract_id = (data or {}).get("line_table_contract_id") or (data or {}).get("table_contract_id") or session.get("line_table_contract_id") or "restaurant.order_lines"
    table_headers, rows = _contract_table(str(contract_id or "restaurant.order_lines"), lines, currency_code, settings, context="restaurant")
    if not table_headers:
        rows = []
        for i, line in enumerate(lines, 1):
            total = line.get("total") or line.get("line_total") or _restaurant_line_total(line)
            status = line.get("kitchen_status") or line.get("status") or ""
            item = _line_value(line, "item_name", "name", "description")
            unit = _line_value(line, "unit", "unit_name", default="")
            qty = _restaurant_qty(_line_value(line, "quantity", "qty", default="0"), settings)
            qty_cell = f"{qty} {_s(unit)}".strip()
            rows.append([
                i,
                item,
                qty_cell,
                _restaurant_money(_line_value(line, "unit_price", "price", default="0"), currency_code, settings),
                _restaurant_money(total, currency_code, settings),
                _restaurant_status(status),
            ])
        table_headers = ["#", _tr("print_item"), _tr("print_quantity"), _tr("print_price"), _tr("print_total"), _tr("restaurant_column_status")]

    payment_rows: List[List[Any]] = []
    for i, pay in enumerate(payments, 1):
        payment_rows.append([
            i,
            _restaurant_payment_method(pay.get("payment_method") or pay.get("method") or ""),
            _restaurant_money(pay.get("amount") or "0", currency_code, settings),
            pay.get("created_at") or pay.get("date") or "",
            pay.get("notes") or "",
        ])

    split_rows: List[List[Any]] = []
    for i, split in enumerate(splits, 1):
        split_rows.append([
            i,
            split.get("name") or split.get("label") or split.get("id") or "",
            _restaurant_money(split.get("total") or split.get("amount") or "0", currency_code, settings),
            _restaurant_money(split.get("paid_amount") or split.get("paid") or "0", currency_code, settings),
            _restaurant_money(split.get("remaining_amount") or split.get("remaining") or "0", currency_code, settings),
            _restaurant_status(split.get("status") or ""),
        ])

    subtotal = balance.get("subtotal", session.get("subtotal", "0"))
    discount = balance.get("discount_amount", session.get("discount_amount", "0"))
    service_charge = balance.get("service_charge_amount", session.get("service_charge_amount", "0"))
    tax = balance.get("tax_amount", session.get("tax_amount", "0"))
    total = balance.get("total", session.get("invoice_total", session.get("total", "0")))
    paid = balance.get("paid", session.get("paid_amount", "0"))
    remaining = balance.get("remaining", session.get("remaining", "0"))

    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr("print_document_number"), ref), (_tr("restaurant_table"), table), (_tr("restaurant_guests"), guests)],
        [(_tr("restaurant_opened_at"), opened), (_tr("restaurant_closed_at"), closed), (_tr("restaurant_waiter"), waiter)],
        [(_tr("print_currency"), _currency_label(currency_code, settings)), (_tr("restaurant_order_state"), _restaurant_status(session.get("order_state") or session.get("status") or "")), (_tr("print_notes"), session.get("notes") or "")],
    ])}
    {_table(table_headers, rows, _tr("print_no_lines"))}
    {_totals_table([
        (_tr("print_subtotal"), subtotal, ""),
        (_tr("print_discount"), discount, ""),
        (_tr("restaurant.service_charge"), service_charge, ""),
        (_tr("print_tax"), tax, ""),
        (_tr("print_total"), total, "final"),
        (_tr("restaurant.paid"), paid, ""),
        (_tr("restaurant.remaining"), remaining, "due"),
    ], currency_code=currency_code, monetary=True)}
    {_table(["#", _tr("print_payment_method"), _tr("restaurant.payment_amount"), _tr("print_document_date"), _tr("print_notes")], payment_rows, _tr("restaurant.no_payments")) if payment_rows else ""}
    {_table(["#", _tr("restaurant.split_bill"), _tr("print_total"), _tr("restaurant.paid"), _tr("restaurant.remaining"), _tr("status")], split_rows, _tr("restaurant.no_split_bills")) if split_rows else ""}
    {_footer(settings, _tr("restaurant_receipt_footer"))}
    """
    return base_document(title, body, paper, settings)


def restaurant_kitchen_ticket_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Kitchen order ticket (KOT).

    KOTs are internal production documents.  They intentionally omit prices,
    totals, taxes, customer payment data, and the cash receipt footer.
    """
    settings = _restaurant_printing_settings("kitchen", data)
    paper = _normalize_paper(paper, settings, "restaurant_kitchen")
    ticket = dict(data or {})
    lines = [line if isinstance(line, dict) else {} for line in (ticket.get("lines") or [])]
    title = _tr("restaurant_kitchen_ticket")
    status = ticket.get("status") or "sent"
    station = ticket.get("station_name") or ticket.get("station_code") or ""
    elapsed = ticket.get("elapsed_minutes") or ticket.get("wait_minutes") or ""
    overdue_badge = f"<div class='notes-box'><strong>⚠ {_s(_tr('restaurant.kds.overdue'))}</strong></div>" if ticket.get("is_overdue") else ""
    contract_id = ticket.get("line_table_contract_id") or ticket.get("table_contract_id") or "restaurant.kds_lines"
    table_headers, rows = _contract_table(str(contract_id or "restaurant.kds_lines"), lines, _restaurant_payload_currency(data, settings), settings, context="kitchen")
    if not table_headers:
        rows = []
        for i, line in enumerate(lines, 1):
            qty = _restaurant_qty(_line_value(line, "quantity", "qty", default="1"), settings)
            unit = _line_value(line, "unit", "unit_name", default="")
            rows.append([
                i,
                _line_value(line, "item_name", "name"),
                f"{qty} {_s(unit)}".strip(),
                _line_value(line, "notes", "kitchen_label", default=""),
            ])
        table_headers = ["#", _tr("print_item"), _tr("print_quantity"), _tr("print_notes")]
    body = f"""
    {_company_header(settings, title)}
    {overdue_badge}
    {_meta_table([
        [(_tr("print_document_number"), ticket.get("id") or ""), (_tr("restaurant_table"), ticket.get("table_name") or ticket.get("table_id") or ""), (_tr("restaurant_station"), station)],
        [(_tr("restaurant_sent_at"), ticket.get("sent_at") or ticket.get("created_at") or ""), (_tr("restaurant_ticket_status"), _restaurant_status(status)), (_tr("restaurant.kds.minutes"), elapsed)],
        [(_tr("print_notes"), ticket.get("notes") or ""), (_tr("restaurant_priority"), ticket.get("priority") or ""), (_tr("restaurant_order_state"), _restaurant_status(ticket.get("order_state") or ""))],
    ])}
    {_table(table_headers, rows, _tr("print_no_lines"))}
    {_footer(settings, _tr("restaurant_kitchen_ticket_footer"))}
    """
    return base_document(title, body, paper, settings)


def restaurant_session_summary_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Closing/session summary for a restaurant table.

    This is separate from the customer receipt: it is a supervisor/cashier record
    showing lifecycle, payment settlement, and split-bill status.
    """
    settings = _restaurant_printing_settings("session_summary", data)
    paper = _normalize_paper(paper, settings, "restaurant_receipt")
    session = dict((data or {}).get("session") or data or {})
    balance = dict((data or {}).get("balance") or {})
    currency_code = _restaurant_payload_currency(data, settings)
    lines = _restaurant_lines(data or {})
    payments = _restaurant_payments(data or {})
    splits = _restaurant_split_bills(data or {})
    title = _tr("restaurant_session_summary")
    line_total = sum((_decimal_or_none(line.get("total") or line.get("line_total") or _restaurant_line_total(line)) or Decimal("0")) for line in lines)
    payments_total = sum((_decimal_or_none(pay.get("amount")) or Decimal("0")) for pay in payments)
    rows = [
        [_tr("restaurant.lines_count"), len(lines)],
        [_tr("restaurant.payments_count"), len(payments)],
        [_tr("restaurant.split_bills_count"), len(splits)],
        [_tr("restaurant.lines_total"), _restaurant_money(line_total, currency_code, settings)],
        [_tr("restaurant.payments_total"), _restaurant_money(payments_total, currency_code, settings)],
        [_tr("restaurant.remaining"), _restaurant_money(balance.get("remaining", session.get("remaining", "0")), currency_code, settings)],
    ]
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr("print_document_number"), session.get("id") or ""), (_tr("restaurant_table"), session.get("table_name") or session.get("table_id") or ""), (_tr("status"), _restaurant_status(session.get("status") or session.get("order_state") or ""))],
        [(_tr("restaurant_opened_at"), session.get("opened_at") or session.get("created_at") or ""), (_tr("restaurant_closed_at"), session.get("closed_at") or ""), (_tr("restaurant_waiter"), session.get("waiter_name") or session.get("waiter_id") or "")],
        [(_tr("print_currency"), _currency_label(currency_code, settings)), (_tr("restaurant.paid"), _restaurant_money(balance.get("paid", session.get("paid_amount", "0")), currency_code, settings)), (_tr("restaurant.remaining"), _restaurant_money(balance.get("remaining", session.get("remaining", "0")), currency_code, settings))],
    ])}
    {_table([_tr("print_item"), _tr("print_total")], rows, _tr("print_no_data"))}
    {_footer(settings, _tr("restaurant_session_summary_footer"))}
    """
    return base_document(title, body, paper, settings)

def _manufacturing_status(value: Any) -> str:
    status_map = {
        'planned': _tr('status_planned'),
        'in_progress': _tr('status_in_progress'),
        'completed': _tr('status_completed'),
        'cancelled': _tr('status_cancelled'),
    }
    return status_map.get(str(value or ''), str(value or ''))


def _manufacturing_currency(payload: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    """Return the currency that manufacturing costs must be displayed in.

    Manufacturing services may store costs as Decimal/base values.  The print
    layer must never expose raw Decimal/scientific notation, and must label
    costs with the document/display currency used by the rest of the UI.
    """
    payload = payload or {}
    explicit = payload.get('display_currency') or payload.get('currency') or payload.get('currency_code')
    if explicit not in (None, ''):
        return _currency_code(explicit, settings)
    try:
        svc = _settings_service()
        if svc is not None:
            return _currency_code(svc.get('display_currency', 'SYP'), settings)
    except Exception:
        pass
    return _currency_code(None, settings)


def _mfg_money(value: Any, payload: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None) -> str:
    return _format_money(value, _manufacturing_currency(payload, settings), settings)


def _mfg_qty(value: Any, settings: Optional[Dict[str, Any]] = None) -> str:
    return _format_quantity(value, settings)


def _mfg_percent(value: Any, settings: Optional[Dict[str, Any]] = None) -> str:
    text = _format_percent(value, settings)
    return f"{text}%" if text not in ('', '-') and not str(text).endswith('%') else text


def _mfg_int(value: Any) -> str:
    dec = _decimal_or_none(value)
    if dec is None:
        return _s(value)
    try:
        return str(int(dec))
    except Exception:
        return _s(value)


def manufacturing_bom_html(data: Dict[str, Any], paper: str = "default") -> str:
    """BOM / manufacturing recipe print template."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_bom")
    payload = dict(data or {})
    bom = payload.get('bom') or payload
    lines = list(payload.get('lines') or bom.get('lines') or bom.get('components') or [])
    summary = payload.get('summary') or {}
    title = _tr('manufacturing_bom_document')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        qty = _line_value(row, 'quantity', 'qty', 'component_qty')
        base_qty = _line_value(row, 'base_qty', 'required_base_qty')
        rows.append([
            i,
            _line_value(row, 'barcode', 'matched_barcode'),
            _line_value(row, 'item_name', 'name', 'item', 'component_name', default=row.get('item_id', '')),
            _line_value(row, 'unit_name', 'unit', default=''),
            _mfg_qty(qty, settings),
            _mfg_qty(base_qty, settings),
            _mfg_percent(_line_value(row, 'waste_percent', default='0'), settings),
            _mfg_money(_line_value(row, 'unit_cost', 'cost', default='0'), payload, settings),
            _mfg_money(_line_value(row, 'total_cost', default='0'), payload, settings),
            _line_value(row, 'notes', default=''),
        ])
    output_qty = bom.get('output_qty') or bom.get('quantity') or 1
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr('print_product'), bom.get('product_name') or bom.get('item_name') or bom.get('product_id') or ''), (_tr('print_quantity'), _mfg_qty(output_qty, settings)), (_tr('status'), _manufacturing_status(bom.get('status')))],
        [(_tr('print_document_number'), bom.get('id') or bom.get('bom_id') or ''), (_tr('print_unit'), bom.get('unit_name') or bom.get('unit') or ''), (_tr('print_notes'), bom.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_barcode'), _tr('print_item'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('manufacturing_column_waste_percent'), _tr('unit_cost'), _tr('print_total'), _tr('print_notes')], rows, _tr('print_no_lines'))}
    {_summary_cards({
        _tr('manufacturing_material_cost'): _mfg_money(summary.get('material_cost', '0'), payload, settings),
        _tr('manufacturing_waste_cost'): _mfg_money(summary.get('waste_cost', '0'), payload, settings),
        _tr('print_total'): _mfg_money(summary.get('total_cost', '0'), payload, settings),
        _tr('manufacturing_required_base_qty'): _mfg_qty(summary.get('base_qty', '0'), settings),
        _tr('manufacturing_unit_cost_output'): _mfg_money(summary.get('unit_cost_output', '0'), payload, settings),
        _tr('manufacturing_component_count'): _mfg_int(summary.get('line_count', len(lines))),
    })}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('production_manager'))}</td><td>{_s(_tr('print_accountant_signature'))}</td></tr></table>
    {_footer(settings, _tr('manufacturing_bom_generated_by'))}
    """
    return base_document(title, body, paper, settings)

def production_order_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Professional HTML for production order details."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing")
    payload = dict(data or {})
    order = payload.get("order") or payload
    consumptions = payload.get("consumptions") or []
    outputs = payload.get("outputs") or []
    reservations = payload.get("reservations") or []
    title = _tr("production_order")
    meta = _meta_table([
        [(_tr("order_number"), order.get("order_number") or order.get("id") or ""), (_tr("product"), order.get("product_name") or order.get("item_name") or ""), (_tr("status"), _manufacturing_status(order.get("status")))],
        [(_tr("planned_quantity"), _mfg_qty(order.get("planned_qty", ""), settings)), (_tr("produced_quantity"), _mfg_qty(order.get("produced_qty", ""), settings)), (_tr("start_date"), order.get("start_date", ""))],
        [(_tr("raw_warehouse"), order.get("raw_warehouse_name") or ""), (_tr("output_warehouse"), order.get("output_warehouse_name") or ""), (_tr("print_notes"), order.get("notes", ""))],
    ])
    cons_rows = []
    for i, c in enumerate(consumptions, 1):
        cons_rows.append([
            i,
            _line_value(c, 'item_name', 'name', 'item', default=c.get('item_id', '')),
            _line_value(c, 'unit_name', 'unit'),
            _mfg_qty(_line_value(c, 'consumed_qty', 'quantity', 'qty'), settings),
            _mfg_qty(_line_value(c, 'consumed_base_qty', 'base_qty'), settings),
            _mfg_money(_line_value(c, 'unit_cost', 'cost'), payload, settings),
            _mfg_money(_line_value(c, 'total_cost'), payload, settings),
            _line_value(c, 'movement_date', 'date'),
        ])
    out_rows = []
    for i, o in enumerate(outputs, 1):
        out_rows.append([
            i,
            _line_value(o, 'product_name', 'item_name', 'name', 'item', default=o.get('product_id', '')),
            _line_value(o, 'unit_name', 'unit'),
            _mfg_qty(_line_value(o, 'produced_qty', 'quantity', 'qty'), settings),
            _mfg_qty(_line_value(o, 'produced_base_qty', 'base_qty'), settings),
            _mfg_money(_line_value(o, 'unit_cost', 'cost'), payload, settings),
            _mfg_money(_line_value(o, 'total_cost'), payload, settings),
            _line_value(o, 'output_date', 'date'),
        ])
    res_rows = []
    for i, r in enumerate(reservations, 1):
        reserved = _line_value(r, 'reserved_qty', 'reserved', 'required_qty')
        consumed = _line_value(r, 'consumed_qty', 'consumed')
        remaining = _line_value(r, 'remaining_qty', 'remaining')
        res_rows.append([
            i,
            _line_value(r, 'item_name', 'name', 'item', default=r.get('item_id', '')),
            _line_value(r, 'unit_name', 'unit'),
            _mfg_qty(reserved, settings),
            _mfg_qty(consumed, settings),
            _mfg_qty(remaining, settings),
            _mfg_qty(_line_value(r, 'base_qty', 'reserved_base_qty'), settings),
            _mfg_qty(_line_value(r, 'conversion_factor'), settings),
        ])
    body = f"""
    {_company_header(settings, title)}
    {meta}
    <h3>{_s(_tr('consumed_materials'))}</h3>
    {_table(['#', _tr('print_item'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('unit_cost'), _tr('print_total'), _tr('print_document_date')], cons_rows, _tr('print_no_consumed_materials'))}
    <h3>{_s(_tr('finished_product'))}</h3>
    {_table(['#', _tr('print_product'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('unit_cost'), _tr('print_total'), _tr('print_document_date')], out_rows, _tr('print_no_production_outputs'))}
    <h3>{_s(_tr('reservations_remaining'))}</h3>
    {_table(['#', _tr('print_item'), _tr('print_unit'), _tr('reserved'), _tr('consumed'), _tr('print_remaining'), _tr('manufacturing_column_base_qty'), _tr('manufacturing_column_conversion_factor')], res_rows, _tr('print_no_reservations'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('production_manager'))}</td><td>{_s(_tr('print_accountant_signature'))}</td></tr></table>
    {_footer(settings, _tr('production_order_generated_by'))}
    """
    return base_document(title, body, paper, settings)

def manufacturing_pick_ticket_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Raw-material pick ticket for production."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_pick_ticket")
    payload = dict(data or {})
    order = payload.get('order') or {}
    lines = list(payload.get('lines') or payload.get('reservations') or [])
    title = _tr('manufacturing_pick_ticket')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        rows.append([
            i,
            _line_value(row, 'item_name', 'name', 'item', default=row.get('item_id', '')),
            _line_value(row, 'barcode', 'matched_barcode'),
            _line_value(row, 'unit_name', 'unit'),
            _mfg_qty(_line_value(row, 'pick_qty', 'remaining_qty'), settings),
            _mfg_qty(_line_value(row, 'reserved_qty'), settings),
            _mfg_qty(_line_value(row, 'consumed_qty'), settings),
            _mfg_qty(_line_value(row, 'base_qty', 'reserved_base_qty'), settings),
            _line_value(row, 'raw_warehouse_name', 'warehouse_name'),
        ])
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr('order_number'), order.get('order_number') or order.get('id') or ''), (_tr('product'), order.get('product_name') or order.get('item_name') or ''), (_tr('status'), _manufacturing_status(order.get('status')))],
        [(_tr('raw_warehouse'), order.get('raw_warehouse_name') or ''), (_tr('planned_quantity'), _mfg_qty(order.get('planned_qty') or '', settings)), (_tr('print_notes'), order.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_unit'), _tr('manufacturing_pick_qty'), _tr('reserved'), _tr('consumed'), _tr('manufacturing_column_base_qty'), _tr('print_warehouse')], rows, _tr('print_no_reservations'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('warehouse_keeper'))}</td><td>{_s(_tr('production_manager'))}</td></tr></table>
    {_footer(settings, _tr('manufacturing_pick_ticket_footer'))}
    """
    return base_document(title, body, paper, settings)

def manufacturing_cost_report_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Production cost report template."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_cost_report")
    payload = dict(data or {})
    order = payload.get('order') or {}
    summary = payload.get('summary') or {}
    title = _tr('manufacturing_cost_report')
    rows = [
        [_tr('manufacturing_consumption_cost'), _mfg_money(summary.get('consumption_cost', '0'), payload, settings)],
        [_tr('manufacturing_output_cost'), _mfg_money(summary.get('output_cost', '0'), payload, settings)],
        [_tr('manufacturing_cost_variance'), _mfg_money(summary.get('variance_cost', '0'), payload, settings)],
        [_tr('produced_quantity'), _mfg_qty(summary.get('produced_qty', '0'), settings)],
        [_tr('unit_cost'), _mfg_money(summary.get('unit_cost', '0'), payload, settings)],
    ]
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr('order_number'), order.get('order_number') or order.get('id') or ''), (_tr('product'), order.get('product_name') or order.get('item_name') or ''), (_tr('status'), _manufacturing_status(order.get('status')))],
        [(_tr('planned_quantity'), _mfg_qty(order.get('planned_qty') or '', settings)), (_tr('produced_quantity'), _mfg_qty(order.get('produced_qty') or '', settings)), (_tr('print_notes'), order.get('notes') or '')],
    ])}
    {_table([_tr('print_description'), _tr('print_total')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('manufacturing_cost_report_footer'))}
    """
    return base_document(title, body, paper, settings)

# ========== Inventory / warehouse templates ==========
def _inventory_movement_type(value: Any) -> str:
    key = str(value or '').strip()
    if not key:
        return ''
    label = _tr(f'inventory_movement_type_{key}')
    return label if label != f'inventory_movement_type_{key}' else key


def inventory_transfer_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_transfer")
    payload = dict(data or {})
    transfer = payload.get('transfer') or payload
    lines = list(payload.get('lines') or ([] if transfer is payload else [transfer]))
    title = _tr('inventory_transfer_document')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        rows.append([
            i,
            _line_value(row, 'item_name', 'name', 'item', default=row.get('item_id', '')),
            _line_value(row, 'barcode', 'matched_barcode'),
            _line_value(row, 'unit_name', 'unit'),
            _line_value(row, 'quantity', 'qty'),
            _line_value(row, 'base_qty', 'quantity_in_base', default=_line_value(row, 'quantity', 'qty')),
            _line_value(row, 'unit_cost', 'cost'),
            _line_value(row, 'notes'),
        ])
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([
        [(_tr('transfer_no'), transfer.get('transfer_no') or transfer.get('id') or ''), (_tr('status'), transfer.get('status') or ''), (_tr('print_date'), transfer.get('created_at') or '')],
        [(_tr('from_warehouse_clean'), transfer.get('from_warehouse_name') or transfer.get('from_warehouse') or ''), (_tr('to_warehouse_clean'), transfer.get('to_warehouse_name') or transfer.get('to_warehouse') or ''), (_tr('print_notes'), transfer.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_unit'), _tr('quantity'), _tr('inventory_column_base_qty'), _tr('unit_cost'), _tr('print_notes')], rows, _tr('print_no_data'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('warehouse_keeper'))}</td><td>{_s(_tr('receiver_signature'))}</td></tr></table>
    {_footer(settings, _tr('inventory_transfer_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_balances_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_balances")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('balances') or [])
    title = _tr('inventory_balances_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'barcode'), _line_value(row, 'warehouse_name', 'warehouse'), _line_value(row, 'quantity', 'available_qty', 'balance'), _line_value(row, 'unit_name', 'unit'), _line_value(row, 'inventory_value', 'value'), _line_value(row, 'status')])
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('print_date'), _print_meta_line()), (_tr('print_notes'), payload.get('notes') or '')]])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_warehouse'), _tr('quantity'), _tr('print_unit'), _tr('inventory_value'), _tr('status')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_balances_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_movements_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_movements")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('movements') or [])
    title = _tr('inventory_movements_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'created_at', 'date'), _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'warehouse_name', 'warehouse'), _inventory_movement_type(row.get('movement_type')), _line_value(row, 'quantity'), _line_value(row, 'unit_cost'), _line_value(row, 'reference_type'), _line_value(row, 'notes')])
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('status'), payload.get('movement_type') or _tr('all')), (_tr('print_date'), _print_meta_line())]])}
    {_table(['#', _tr('print_date'), _tr('print_item'), _tr('print_warehouse'), _tr('type'), _tr('quantity'), _tr('unit_cost'), _tr('reference'), _tr('print_notes')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_movements_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_ledger_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_ledger")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('ledger') or [])
    title = _tr('inventory_ledger_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'created_at', 'date'), _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'warehouse_name', 'warehouse'), _inventory_movement_type(row.get('movement_type')), _line_value(row, 'direction'), _line_value(row, 'quantity'), _line_value(row, 'unit_cost'), _line_value(row, 'reference_type'), _line_value(row, 'notes')])
    body = f"""
    {_company_header(settings, title)}
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('print_date'), _print_meta_line()), (_tr('print_notes'), payload.get('notes') or '')]])}
    {_table(['#', _tr('print_date'), _tr('print_item'), _tr('print_warehouse'), _tr('type'), _tr('direction'), _tr('quantity'), _tr('unit_cost'), _tr('reference'), _tr('print_notes')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_ledger_footer'))}
    """
    return base_document(title, body, paper, settings)
