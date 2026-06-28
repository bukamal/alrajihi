# -*- coding: utf-8 -*-
"""Phase408 Basit-inspired browser HTML printing surface contract."""
from __future__ import annotations

BASIT_PRINTING_SURFACE_CONTRACT = {
    "phase": 408,
    "theme": "Basit Printing Surface",
    "source_of_truth": "theme.brand Basit tokens via _basit_print_tokens",
    "surfaces": [
        "invoice_html",
        "pos_receipt_html",
        "return_html",
        "voucher_html",
        "report_html",
        "restaurant_receipt_html",
        "restaurant_kitchen_ticket_html",
        "manufacturing_bom_html",
        "production_order_html",
        "inventory_transfer_html",
    ],
    "palette": {
        "header_blue": "basit_blue",
        "active_yellow": "basit_yellow",
        "total_red": "basit_red",
        "canvas": "basit_canvas",
        "grid": "basit_table_bg",
    },
    "rules": [
        "Printed documents use the same Basit blue/yellow/red visual language as the runtime UI.",
        "Totals use the Basit red final-row treatment.",
        "Metadata, table header and summary cards use Basit borders and table colors.",
        "Thermal receipts keep compact paper behavior while retaining Basit print palette markers.",
    ],
}
