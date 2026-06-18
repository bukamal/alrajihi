# Phase 209 — Expense DAO Singleton Hotfix

## Problem
Dashboard loading failed with:

```text
module 'database.dao.expense_dao' has no attribute 'get_all'
```

The lazy database import boundary added in prior startup hardening expects legacy DAO modules to expose singleton objects such as `expense_dao`. Most DAO modules already did, but `expense_dao.py` did not. Some legacy import paths therefore resolved to the module instead of a DAO singleton, and callers attempted `expense_dao.get_all(...)` on the module.

## Fix
Added backward-compatible singleton exports:

```python
expense_dao = ExpenseDAO()
reporting_dao = ReportingDAO()
```

The `reporting_dao` singleton was added defensively because the lazy export map also exposes it.

## Guard
Added `tools/phase209_expense_dao_singleton_guard.py` to verify:

- `expense_dao.py` exposes `expense_dao = ExpenseDAO()`
- `reporting_dao.py` exposes `reporting_dao = ReportingDAO()`
- `LocalExpenseGateway` still imports the legacy `expense_dao` compatibility name
- `expense_dao` implements `get_all`, `add`, and `delete`
