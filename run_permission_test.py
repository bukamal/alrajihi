import os, sys, subprocess, json
from pathlib import Path
ROOT=Path('/mnt/data/compat_audit')
code=r'''
from database.migrations import ensure_db
ensure_db()
from database.connection import DatabaseConnection
from auth.session import UserSession
from database.repositories.user_repo import UserRepository
conn=DatabaseConnection().get_connection()
repo=UserRepository()
uid=repo.create('cashier_perm','pw','Cashier','cashier',None)
UserSession.login({'id':uid,'username':'cashier_perm','role':'cashier'})
cur=conn.execute("INSERT INTO invoices(user_id,type,date,reference,total,paid,status,workflow_status,deleted_at) VALUES(?,?,?,?,?,?,?,?,NULL)",(uid,'sale','2026-01-01','PERM-001','500','500','open','APPROVED'))
inv_id=cur.lastrowid; conn.commit()
from core.services.invoice_service import invoice_service
try:
    invoice_service.post(inv_id)
    raise AssertionError('cashier unexpectedly posted invoice')
except PermissionError as e:
    print('permission_denied_ok', str(e)[:80])
'''
env=os.environ.copy(); env['ALRAJHI_DB_PATH']='/mnt/data/compat_perm.sqlite'; env['QT_QPA_PLATFORM']='offscreen'; env['PYTHONPATH']='/mnt/data/pyqt_stub:'+str(ROOT/'alrajhi_client')+':'+str(ROOT)+':'+env.get('PYTHONPATH','')
try: os.remove('/mnt/data/compat_perm.sqlite')
except FileNotFoundError: pass
p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
print(json.dumps({'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr},ensure_ascii=False,indent=2))
