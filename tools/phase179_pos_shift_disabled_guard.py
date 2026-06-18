# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

policy = (ROOT / "alrajhi_client/core/services/pos_operation_policy.py").read_text(encoding="utf-8")
pos_widget = (ROOT / "alrajhi_client/views/widgets/pos_widget.py").read_text(encoding="utf-8")
pos_service = (ROOT / "alrajhi_client/core/services/pos_service.py").read_text(encoding="utf-8")
settings = (ROOT / "alrajhi_client/core/services/settings_service.py").read_text(encoding="utf-8")

assert "def pos_shifts_enabled" in settings and "pos/use_shifts', 'false'" in settings, "POS shifts must default to disabled"
assert "settings.get('use_shifts')" in pos_service, "new_cart must only attach open shift when use_shifts is true"
assert "settings_service.pos_shifts_enabled()" in pos_service, "checkout must read shift mode from settings_service"
assert "else:\n            cart.shift_id = None" in pos_service, "checkout must clear shift_id when shifts are disabled"
assert "def is_shift_operation" in policy and "OP_OPEN_SHIFT" in policy and "OP_CLOSE_SHIFT" in policy, "policy must know shift operations"
assert "settings_service.pos_shifts_enabled()" in policy, "policy must block shift operations when shifts are disabled"
assert "shifts_disabled_direct_cashbox" in policy, "disabled shift operation must return direct-cashbox message"
assert "if not self._pos_shifts_enabled():" in pos_widget, "open/close shift handlers must check shift mode directly"
assert "visible = visible and shifts_enabled" in pos_widget, "open/close shift buttons must stay hidden when shifts are disabled"

print("phase179_pos_shift_disabled_guard: OK")
