# Phase 210 — Expense DAO Export Hotfix

## Problem
Dashboard loading still failed with:

```text
module 'database.dao.expense_dao' has no attribute 'get_all'
```

Phase 209 added an `expense_dao = ExpenseDAO()` singleton, but the runtime could still receive the `database.dao.expense_dao` **module object** instead of the singleton instance.

The root cause was the lazy export in `database/__init__.py`:

```python
'expense_dao': ('database.dao', 'expense_dao')
```

If Python had already imported `database.dao.expense_dao`, it attaches that submodule as `database.dao.expense_dao` on the package. A later `getattr(database.dao, 'expense_dao')` may therefore return the module object, not the singleton.

## Fix
- Changed the database public export to resolve the singleton directly from the concrete submodule:

```python
'expense_dao': ('database.dao.expense_dao', 'expense_dao')
```

- Updated `LocalExpenseGateway` to import the concrete singleton directly:

```python
from database.dao.expense_dao import expense_dao
```

- Added a defensive package-shadow repair at the bottom of `expense_dao.py`:

```python
setattr(sys.modules['database.dao'], 'expense_dao', expense_dao)
```

- Added the same defensive repair for `reporting_dao`, which follows the same lazy export pattern.

## Guard
Added:

```text
tools/phase210_expense_dao_export_hotfix_guard.py
```

The guard prevents returning to package-level DAO exports that can leak module objects instead of singleton DAO instances.
