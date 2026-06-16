# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings
from pathlib import Path


def _default_logo_path():
    try:
        from brand_assets import logo_png
        return logo_png(512)
    except Exception:
        return ""

def _valid_logo_path(value):
    candidate = str(value or "").strip()
    if candidate and Path(candidate).exists():
        return candidate
    return _default_logo_path()


def get_company_info():
    settings = QSettings("Alrajhi", "Accounting")
    return {
        'name': settings.value("company/name", "الراجحي للمحاسبة والمستودعات"),
        'address': settings.value("company/address", "المملكة العربية السعودية - الرياض"),
        'phone': settings.value("company/phone", "+966 12 3456789"),
        'email': settings.value("company/email", "info@alrajhi.com"),
        'tax_number': settings.value("company/tax_number", ""),
        'commercial_register': settings.value("company/commercial_register", ""),
        'website': settings.value("company/website", ""),
        'logo_path': _valid_logo_path(settings.value("company/logo_path", _default_logo_path())),
    }

def save_company_info(info):
    settings = QSettings("Alrajhi", "Accounting")
    settings.setValue("company/name", info.get('name', ''))
    settings.setValue("company/address", info.get('address', ''))
    settings.setValue("company/phone", info.get('phone', ''))
    settings.setValue("company/email", info.get('email', ''))
    settings.setValue("company/tax_number", info.get('tax_number', ''))
    settings.setValue("company/commercial_register", info.get('commercial_register', ''))
    settings.setValue("company/website", info.get('website', ''))
    settings.setValue("company/logo_path", info.get('logo_path') or _default_logo_path())


