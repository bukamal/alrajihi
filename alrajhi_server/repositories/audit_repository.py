from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class AuditLogRepository:
    def list(self, limit: int = 2000, offset: int = 0) -> dict[str, Any]:
        db = get_db()
        rows = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        total = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        return {"logs": [dict(row) for row in rows], "total": total}

    def delete_older_than_days(self, days: int = 90) -> None:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        db = get_db()
        db.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        db.commit()
