# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
modern = (ROOT / 'alrajhi_client/views/modern_topbar.py').read_text(encoding='utf-8')
main = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
toast = (ROOT / 'alrajhi_client/views/widgets/toast_notification.py').read_text(encoding='utf-8')
utils = (ROOT / 'alrajhi_client/utils.py').read_text(encoding='utf-8')
assert 'setText(\'\')' in modern or 'setText("")' in modern, 'shell icon buttons must stay icon-only'
assert 'alert_badge' in modern and 'set_alert_badge' in modern, 'notification badge support missing'
assert 'dashboard_alerts(limit=99)' in main and 'set_alert_badge(count)' in main, 'alert badge is not wired to alert service'
assert 'top-center' in toast and 'reposition_all' in toast, 'central toast positioning missing'
assert 'install_non_blocking_message_boxes' in utils and 'show_toast(message or title' in utils, 'message boxes not routed to toast'
print('phase96 toast and alert badge verification passed')
