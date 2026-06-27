# -*- coding: utf-8 -*-
from __future__ import annotations

RESTAURANT_ITEM_CARD_SURFACE_CONTRACT = {
    "phase": 396,
    "name": "restaurant_item_card_surface",
    "workspace": "restaurant_simple_pos",
    "requirements": [
        "Restaurant menu items use the same single-column rectangular card grammar as categories.",
        "Items are laid out one full-width button per row, not responsive multi-column tiles.",
        "Item card buttons remain direct add-to-invoice actions and do not expose kitchen/table workflows.",
        "Resize events do not rebuild the item grid just to recalculate column counts.",
    ],
    "ui_markers": {
        "item_button_property": "restaurant_same_card_surface",
        "item_grid_layout": "self.items_grid.addWidget(button, index, 0)",
        "item_card_height": "button.setMinimumHeight(58)",
        "item_card_size_policy": "QSizePolicy.Expanding, QSizePolicy.Fixed",
    },
}
