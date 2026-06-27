# -*- coding: utf-8 -*-
"""Phase 395 table language direction contract."""

TABLE_LANGUAGE_DIRECTION_CONTRACT = {
    "phase": 395,
    "name": "table_language_direction",
    "rule": "All QTableView and QTableWidget surfaces follow UI language direction: Arabic RTL, non-Arabic LTR.",
    "languages": {
        "ar": "rtl",
        "de": "ltr",
        "en": "ltr",
        "fr": "ltr",
    },
    "surfaces": [
        "CustomTableView / SmartTableView list tables",
        "EditableSmartGrid editable tables",
        "TransactionLineGrid invoice/return editable tables",
        "Generic QTableWidget surfaces under runtime visual polish",
        "Restaurant simple POS invoice table",
    ],
}
