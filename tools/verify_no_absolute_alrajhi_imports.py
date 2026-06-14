from pathlib import Path
import sys
bad=[]
for p in Path('alrajhi_client').rglob('*.py'):
    text=p.read_text(encoding='utf-8')
    for i,line in enumerate(text.splitlines(),1):
        if 'from alrajhi_client.' in line or 'import alrajhi_client.' in line:
            bad.append((str(p),i,line.strip()))
if bad:
    for p,i,l in bad:
        print(f'{p}:{i}: {l}')
    sys.exit(1)
print('OK no absolute alrajhi_client imports')
