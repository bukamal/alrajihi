# -*- coding: utf-8 -*-
from __future__ import annotations

BASIT_MANAGEMENT_SURFACE_CONTRACT = {
    "phase": 404,
    "name": "basit_management_surface",
    "scope": [
        "materials",
        "customers",
        "suppliers",
        "categories",
        "vouchers",
        "warehouses",
        "cashboxes",
        "banks",
        "users",
        "branches",
    ],
    "markers": {
        "workspace": "basitManagementWorkspace",
        "toolbar": "basitListToolbar",
        "search": "basitListSearch",
        "buttons": "basitToolbarButton",
        "table": "basitManagementTable",
        "master_detail": "basitMasterDetail",
        "detail_placeholder": "basitDetailPlaceholder",
    },
    "requirements": [
        "Management/list workspaces use the same blue/yellow/red Basit-inspired visual grammar as restaurant, dashboard and invoices.",
        "BaseWidget descendants receive the surface automatically without business-logic rewrites.",
        "Inline master-detail pages share a Basit splitter, yellow detail title and blue back/action buttons.",
        "SmartTableView instances in list pages use the same Basit table selection/header skin.",
    ],
}
