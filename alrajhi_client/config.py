# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings


def _default_logo_path():
    try:
        from brand_assets import logo_png
        return logo_png(512)
    except Exception:
        return ""

def get_company_info():
    settings = QSettings("Alrajhi", "Accounting")
    return {
        'name': settings.value("company/name", "الراجحي للمحاسبة"),
        'address': settings.value("company/address", "المملكة العربية السعودية - الرياض"),
        'phone': settings.value("company/phone", "+966 12 3456789"),
        'email': settings.value("company/email", "info@alrajhi.com"),
        'tax_number': settings.value("company/tax_number", ""),
        'logo_path': settings.value("company/logo_path", _default_logo_path()) or _default_logo_path(),
    }

def save_company_info(info):
    settings = QSettings("Alrajhi", "Accounting")
    settings.setValue("company/name", info.get('name', ''))
    settings.setValue("company/address", info.get('address', ''))
    settings.setValue("company/phone", info.get('phone', ''))
    settings.setValue("company/email", info.get('email', ''))
    settings.setValue("company/tax_number", info.get('tax_number', ''))
    settings.setValue("company/logo_path", info.get('logo_path') or _default_logo_path())


