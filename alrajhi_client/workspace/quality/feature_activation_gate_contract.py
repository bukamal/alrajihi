# -*- coding: utf-8 -*-
from __future__ import annotations

FEATURE_ACTIVATION_GATE_CONTRACT = {
    "phase": 397,
    "name": "feature_activation_gate",
    "protected_features": ["manufacturing", "restaurant", "cafe", "apparel"],
    "requirements": [
        "Manufacturing, restaurant, cafe and apparel prompt for a dedicated activation key before entry.",
        "The protected vertical modules use the same generic activation service and dialog surface as network activation.",
        "Network activation remains backward compatible with network_license.dat.",
        "Manufacturing document shortcuts are guarded, not only the manufacturing list workspace.",
    ],
    "ui_markers": {
        "page_gate": "PAID_FEATURE_PAGES",
        "dialog": "ModuleActivationDialog.ensure_feature",
        "generic_activation": "activate_feature",
        "generic_check": "check_feature_activation",
    },
}
