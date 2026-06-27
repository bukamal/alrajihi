# -*- coding: utf-8 -*-
"""Phase401 Basit-inspired visual system contract."""
from __future__ import annotations

BASIT_VISUAL_SYSTEM_CONTRACT = {
    "phase": 401,
    "theme": "Basit Inspired Visual System",
    "palette": {
        "blue": "basit_blue",
        "yellow": "basit_yellow",
        "red_total": "basit_red",
        "canvas": "basit_canvas",
        "grid": "basit_table_bg",
    },
    "metrics": {
        "pos_card_height": "basit_pos_card_height",
        "category_card_height": "basit_category_card_height",
        "invoice_row_height": "basit_invoice_row_height",
        "total_height": "basit_total_height",
        "toolbar_height": "basit_toolbar_height",
    },
    "surfaces": [
        "restaurant_simple_pos",
        "restaurant_cards",
        "restaurant_invoice_grid",
        "restaurant_total_footer",
        "dashboard_shortcuts",
        "runtime_basit_panels",
    ],
    "rule": "Use Basit colors/sizes through central tokens and QSS, not local literal duplication.",
}
