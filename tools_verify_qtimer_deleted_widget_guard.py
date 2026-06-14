from pathlib import Path
root = Path(__file__).resolve().parent
utils = root / 'alrajhi_client' / 'utils.py'
text = utils.read_text(encoding='utf-8')
required = [
    'def _is_qobject_alive(obj):',
    'sip.isdeleted(obj)',
    'QTimer.singleShot(100, lambda le=line_edit: self._select_all(le))',
    'except RuntimeError:',
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('missing deleted-widget guard pieces: ' + ', '.join(missing))
print('OK: deleted-widget auto-select guard is present')
