# -*- coding: utf-8 -*-
from .bom_document_tab import BomDocumentTab
from .production_order_document_tab import ProductionOrderDocumentTab
from .production_order_lifecycle_tab import ProductionOrderDetailsTab, LegacyProductionOrderDetailsTab

__all__ = [
    "BomDocumentTab",
    "ProductionOrderDocumentTab",
    "ProductionOrderDetailsTab",
    "LegacyProductionOrderDetailsTab",
]
