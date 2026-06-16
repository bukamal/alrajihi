import os, sys, subprocess, json
from pathlib import Path
ROOT=Path('/mnt/data/compat_audit')
code=r'''
from database.migrations import ensure_db
ensure_db()
from database.connection import DatabaseConnection
from auth.session import UserSession
conn=DatabaseConnection().get_connection()
# ensure admin session + rbac mapping
conn.execute("INSERT OR IGNORE INTO user_roles(user_id, role_id) SELECT 'admin', id FROM roles WHERE name='admin'")
conn.commit()
UserSession.login({'id':'admin','username':'admin','role':'admin'})
# direct invoice (no lines needed for accounting post smoke)
cur=conn.execute("INSERT INTO invoices(user_id,type,date,reference,total,paid,status,workflow_status,deleted_at) VALUES('admin','sale','2026-01-01','E2E-001','1000','250','open','DRAFT',NULL)")
inv_id=cur.lastrowid
conn.commit()
from core.services.invoice_service import invoice_service
# submit, approve, post
s1=invoice_service.submit(inv_id)
s2=invoice_service.approve(inv_id)
s3=invoice_service.post(inv_id)
row=conn.execute('select workflow_status from invoices where id=?',(inv_id,)).fetchone()
je=conn.execute("select id from journal_entries where source_type='INVOICE' and source_id=?",(inv_id,)).fetchone()
lines=conn.execute('select sum(cast(debit as real)) d, sum(cast(credit as real)) c from journal_lines where journal_entry_id=?',(je['id'],)).fetchone()
from core.services.accounting_service import accounting_service
trial=accounting_service.trial_balance()
print({'statuses':[s1,s2,s3,row['workflow_status']], 'journal':je['id'], 'debit':lines['d'], 'credit':lines['c'], 'trial_accounts':len(trial)})
assert row['workflow_status']=='POSTED'
assert abs(lines['d']-lines['c']) < 0.001
'''

env=os.environ.copy(); env['ALRAJHI_DB_PATH']='/mnt/data/compat_e2e.sqlite'; env['QT_QPA_PLATFORM']='offscreen'; env['PYTHONPATH']='/mnt/data/pyqt_stub:'+str(ROOT/'alrajhi_client')+':'+str(ROOT)+':'+env.get('PYTHONPATH','')
try: os.remove('/mnt/data/compat_e2e.sqlite')
except FileNotFoundError: pass
p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
print(json.dumps({'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr},ensure_ascii=False,indent=2))
