# -*- coding: utf-8 -*-
"""Printing package public API.

Keep this package lazy.  Startup imports such as ``from printing.printing_service
import printing_service`` must not eagerly import print_manager, thermal printer
or label designer modules.  That eager chain is fragile in PyInstaller one-dir
builds and can fail before the application window is created.
"""
from __future__ import annotations

_EXPORTS = {
    'ThermalPrinter': ('.thermal_printer', 'ThermalPrinter'),
    'PDFPrinter': ('.thermal_printer', 'PDFPrinter'),
    'ImagePrinter': ('.thermal_printer', 'ImagePrinter'),
    'PrintManager': ('.print_manager', 'PrintManager'),
    'ProfessionalPrintManager': ('.print_manager', 'ProfessionalPrintManager'),
    'ProfessionalInvoicePrinter': ('.print_manager', 'ProfessionalInvoicePrinter'),
    'PrintingService': ('.printing_service', 'PrintingService'),
    'printing_service': ('.printing_service', 'printing_service'),
    'LabelDesigner': ('.label_designer', 'LabelDesigner'),
    'get_current_template': ('.label_designer', 'get_current_template'),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    from importlib import import_module
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name, package=__name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
