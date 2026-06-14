# -*- coding: utf-8 -*-
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'alrajhi_client/views/widgets/monitoring_widget.py',
    'alrajhi_client/views/widgets/offline_queue_widget.py',
    'alrajhi_client/views/widgets/users_widget.py',
    'alrajhi_client/views/widgets/audit_log_widget.py',
    'alrajhi_client/views/widgets/branches_widget.py',
    'alrajhi_client/views/widgets/categories_widget.py',
]
REQUIRED = [
    'monitoring_title_icon','offline_queue_title_icon','users_title_icon',
    'audit_log_title_icon','branches_title_icon','categories_title_icon'
]
def main():
    tr = (ROOT/'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
    missing=[k for k in REQUIRED if k not in tr]
    if missing:
        raise SystemExit('missing translation keys: '+', '.join(missing))
    bad=[]
    for rel in FILES:
        text=(ROOT/rel).read_text(encoding='utf-8')
        if 'Qt.RightToLeft' in text:
            bad.append(rel+': hard-coded RTL')
        if 'from alrajhi_client.i18n import translate' not in text:
            bad.append(rel+': missing translate import')
    if bad:
        raise SystemExit('\n'.join(bad))
    print('phase89 secondary localization guard ok')
if __name__ == '__main__':
    main()
