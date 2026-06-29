# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def _has(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False


def phase448_operational_pos_restaurant_surface_migration_summary(root: Path | str | None = None) -> dict:
    root = Path(root or Path(__file__).resolve().parents[3])
    checks = []
    details = []

    brand = root / "alrajhi_client/theme/brand.py"
    qss = root / "alrajhi_client/theme/qss.py"
    pos = root / "alrajhi_client/views/widgets/pos_widget.py"
    payment = root / "alrajhi_client/features/pos/pos_payment_shell.py"
    rest_simple = root / "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py"
    rest = root / "alrajhi_client/views/restaurant/restaurant_pos_widget.py"

    required = [
        (brand, "'operational_surface_phase': 448"),
        (brand, "'operational_scan_input_min_height'"),
        (qss, "Phase448: Operational POS/Restaurant surface migration"),
        (qss, 'QWidget[operationalSurfacePhase="448"]'),
        (qss, 'visualRole="operational_scan_input"'),
        (qss, 'visualRole="operational_table"'),
        (pos, "self.setProperty('operationalSurfacePhase', 448)"),
        (pos, 'self.barcode_input.setProperty("visualRole", "operational_scan_input")'),
        (pos, "self.table.setProperty('visualRole', 'operational_table')"),
        (pos, 'self.payment_shell.setProperty("visualRole", "operational_payment_shell")'),
        (payment, 'self.setProperty("operationalSurfacePhase", 448)'),
        (payment, 'button.setProperty("visualRole", "operational_primary")'),
        (rest_simple, 'self.setProperty("operationalSurfacePhase", 448)'),
        (rest_simple, 'title_label.setProperty("visualRole", "operational_section_title")'),
        (rest_simple, 'self.total_label.setProperty("visualRole", "operational_total")'),
        (rest_simple, 'self.invoice_table.setProperty("visualRole", "operational_table")'),
        (rest, 'self.setProperty("operationalSurfacePhase", 448)'),
        (rest, 'header_card.setProperty("visualRole", "operational_header")'),
        (rest, 'self.lines.setProperty("visualRole", "operational_table")'),
        (rest, 'actions_card.setProperty("visualRole", "operational_actions")'),
    ]
    for path, needle in required:
        ok = _has(path, needle)
        checks.append(ok)
        if not ok:
            details.append(f"Missing {needle!r} in {path.relative_to(root)}")

    # Regression: POS barcode must not use local setStyleSheet for the main scan field.
    try:
        pos_text = pos.read_text(encoding="utf-8")
        legacy = 'self.barcode_input.setStyleSheet' in pos_text
    except FileNotFoundError:
        legacy = True
    checks.append(not legacy)
    if legacy:
        details.append("POS barcode input still uses direct setStyleSheet instead of operational visual role")

    ready = all(checks)
    return {"ready": ready, "checks": len(checks), "issues": 0 if ready else len(details), "details": details}
