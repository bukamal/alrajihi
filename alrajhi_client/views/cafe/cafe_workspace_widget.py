# -*- coding: utf-8 -*-
from __future__ import annotations

from views.restaurant.restaurant_dashboard import RestaurantDashboard


class CafeWorkspaceWidget(RestaurantDashboard):
    """Standalone cafe workspace backed by the restaurant engine.

    The widget intentionally subclasses RestaurantDashboard so payments,
    printing, inventory, recipes, and shift reporting remain on the audited
    restaurant/cafe service path.  The constructor selects the cafe UI context
    so table-service controls are not exposed to cafe operators.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent, workspace_context="cafe")
        self.setObjectName("cafeWorkspace")
