import os, sys, sqlite3, json, subprocess, tempfile, shutil
from pathlib import Path
ROOT=Path('/mnt/data/compat_audit')

def run(cmd, env=None):
    e=os.environ.copy(); e.update(env or {})
    e['PYTHONPATH']='/mnt/data/pyqt_stub:'+str(ROOT/'alrajhi_client')+':'+str(ROOT)+':'+e.get('PYTHONPATH','')
    p=subprocess.run(cmd, cwd=str(ROOT), env=e, text=True, capture_output=True, timeout=90)
    return {'cmd':' '.join(cmd),'rc':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}

results=[]
# compileall
p=subprocess.run([sys.executable,'-m','compileall','-q','alrajhi_client','alrajhi_server'],cwd=ROOT,text=True,capture_output=True,timeout=120)
results.append({'test':'compileall','ok':p.returncode==0,'detail':p.stderr[-2000:]})

def client_script(db_path, code):
    env={'ALRAJHI_DB_PATH':db_path, 'QT_QPA_PLATFORM':'offscreen'}
    return run([sys.executable,'-c',code],env)

# new client db repeated
for label in ['client_new_first','client_new_second']:
    db='/mnt/data/compat_client_new.sqlite'
    if label.endswith('first') and os.path.exists(db): os.remove(db)
    res=client_script(db,"from database.migrations import ensure_db; ensure_db(); print('ok')")
    results.append({'test':label,'ok':res['rc']==0,'detail':res})

# inspect required schema
conn=sqlite3.connect('/mnt/data/compat_client_new.sqlite'); conn.row_factory=sqlite3.Row
req_tables=['users','roles','permissions','user_roles','user_branch_access','approval_requests','approval_steps','approval_matrix','accounts','journal_entries','journal_lines','accounting_periods','system_health_checks']
missing=[]
for t in req_tables:
    if not conn.execute("select 1 from sqlite_master where type='table' and name=?",(t,)).fetchone(): missing.append(t)
cols={t:[r[1] for r in conn.execute(f'pragma table_info({t})').fetchall()] for t in req_tables if t not in missing}
results.append({'test':'schema_required_tables','ok':not missing,'missing':missing,'columns':cols})
conn.close()

# old db upgrade minimal
old='/mnt/data/compat_old.sqlite'
if os.path.exists(old): os.remove(old)
conn=sqlite3.connect(old)
conn.executescript('''
CREATE TABLE users(id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, salt TEXT, full_name TEXT, role TEXT DEFAULT 'user', created_at TEXT);
CREATE TABLE invoices(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, type TEXT, date TEXT, total TEXT DEFAULT '0', paid TEXT DEFAULT '0');
CREATE TABLE invoice_lines(id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, item_id INTEGER, quantity TEXT, price TEXT);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT, category TEXT);
INSERT INTO users(id, username, password_hash, salt, full_name, role, created_at) VALUES('old1','oldadmin','x','x','Old Admin','admin','2024-01-01');
''')
conn.commit(); conn.close()
res=client_script(old,"from database.migrations import ensure_db; ensure_db(); ensure_db(); print('ok')")
results.append({'test':'old_db_upgrade_idempotent','ok':res['rc']==0,'detail':res})

# RBAC user role sync test
code=r'''
from database.migrations import ensure_db
ensure_db()
from database.repositories.user_repo import UserRepository
repo=UserRepository()
uid=repo.create('compat_acc','pw','Compat Accountant','accountant',None)
repo.update(uid,'Compat Accountant 2','manager',None)
conn=repo.db.get_connection()
row=conn.execute("select role from users where id=?",(uid,)).fetchone()
roles=[r['name'] for r in conn.execute("select r.name from user_roles ur join roles r on r.id=ur.role_id where ur.user_id=?",(uid,)).fetchall()]
print({'user_role': row['role'], 'rbac_roles': roles})
assert row['role']=='manager'
assert roles==['manager']
'''
res=client_script('/mnt/data/compat_client_rbac.sqlite',code)
results.append({'test':'user_role_rbac_sync','ok':res['rc']==0,'detail':res})

# services import + health
code=r'''
from database.migrations import ensure_db
ensure_db()
from core.services.system_health_service import system_health_service
from core.services.rbac_service import rbac_service
from core.services.advanced_approval_service import advanced_approval_service
h=system_health_service.run_checks()
print(h)
assert h['overall'] in ('GREEN','YELLOW')
assert len(rbac_service.list_roles())>=5
assert len(rbac_service.list_permissions())>=5
'''
res=client_script('/mnt/data/compat_client_health.sqlite',code)
results.append({'test':'services_health_rbac_import','ok':res['rc']==0,'detail':res})

# localization static keys check for new roles
code=r'''
from i18n import set_language, translate
for lang in ['ar','en','de']:
    set_language(lang)
    vals=[translate(k) for k in ['role_admin','role_manager','role_accountant','role_cashier','role_viewer']]
    print(lang, vals)
    assert all(v and not v.startswith('[') for v in vals)
'''
res=client_script('/mnt/data/compat_client_i18n.sqlite',code)
results.append({'test':'localization_role_keys','ok':res['rc']==0,'detail':res})

# server migrations new/repeated
for label in ['server_new_first','server_new_second']:
    db='/mnt/data/compat_server_new.sqlite'
    if label.endswith('first') and os.path.exists(db): os.remove(db)
    env={'ALRAJHI_SERVER_DB_PATH':db}
    e=os.environ.copy(); e.update(env); e['PYTHONPATH']='/mnt/data/pyqt_stub:'+str(ROOT)+':'+e.get('PYTHONPATH','')
    p=subprocess.run([sys.executable,'-c','from alrajhi_server.database.migrations import ensure_db; ensure_db(); print("ok")'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=90)
    results.append({'test':label,'ok':p.returncode==0,'detail':{'rc':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:]}})

print(json.dumps(results, ensure_ascii=False, indent=2))
