from __future__ import annotations

from typing import Any, Iterable

from alrajhi_server.database.connection import get_db


class SqlRepository:
    """Low-level SQL execution base for server repositories.

    HTTP/API modules must not depend on this class directly. It is only a
    repository-layer primitive used by domain repositories while the large
    server modules are progressively split into semantic methods.
    """

    def __init__(self):
        self.db = get_db()

    def query(self, sql: str, params: Iterable[Any] = ()):  # compatibility for migrated route services
        return self.db.execute(sql, tuple(params))

    def execute(self, sql: str, params: Iterable[Any] = ()):  # explicit repository-layer execution
        return self.db.execute(sql, tuple(params))

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
