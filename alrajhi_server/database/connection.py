# -*- coding: utf-8 -*-
import sqlite3
import os
from flask import g
from .paths import get_server_db_path

DB_PATH = get_server_db_path()

def get_db():
    if 'db' not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def init_db():
    from .migrations import ensure_db
    ensure_db()
    print(f"✅ تم التحقق من قاعدة بيانات الخادم في: {DB_PATH}")


