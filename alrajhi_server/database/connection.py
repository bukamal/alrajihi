# -*- coding: utf-8 -*-
import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'alrajhi_server.db')

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
    print("✅ تم التحقق من قاعدة بيانات الخادم")


