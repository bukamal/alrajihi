# Gateway Phase 22 Hotfix 2 Report

## Fix

Resolved login failure:

```text
LoginDialog object has no attribute user_repo
```

## Root cause

`LoginDialog._do_login()` still used legacy direct login paths:

```python
self.db_conn.get_rest_client()
self.user_repo.authenticate(...)
```

These attributes were removed during the UserService/UserGateway migration.

## Change

`LoginDialog._do_login()` now uses the unified service path:

```python
user = user_service.authenticate(username, password)
```

So login now follows:

```text
LoginDialog → UserService → UserGateway → Remote API or Local UserRepository
```

## Validation

- architecture_guard: passed
- compileall: passed
- legacy DatabaseConnection exceptions: 0
