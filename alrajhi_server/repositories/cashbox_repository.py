from __future__ import annotations

from alrajhi_server.repositories.base_sql_repository import SqlRepository


class CashboxRepository(SqlRepository):
    """Repository boundary for the corresponding server API module.

    This class intentionally preserves the existing query semantics while moving
    the dependency from a repository-layer SQL base to a domain-specific repository
    boundary. Route modules should depend on this repository, not on
    the low-level SQL base directly.
    """


def get_cashbox_repository() -> CashboxRepository:
    return CashboxRepository()
