# SQLAlchemy Session Management Issue

## Problem

When test fixtures seed data using `storage.insert_transaction()` or similar methods, and then test code calls wallet methods that query the same data, SQLAlchemy raises:

```
sqlalchemy.exc.InvalidRequestError: Object '<Transaction at 0x...>' is already attached to session 'X' (this is 'Y')
```

## Root Cause

In `StorageProvider._insert_generic()`:

```python
session = self.SessionLocal()
try:
    session.add(obj)
    session.flush()
    pk_value = getattr(obj, pk_attr_name)
    if not trx:
        session.commit()
    return pk_value  # obj still in session identity map
finally:
    if not trx:
        session.close()
```

Even though the session is closed, SQLAlchemy's identity map may retain references to the object, causing conflicts when a new session queries the same primary key.

## Solution Options

### Option 1: Use Scoped Sessions (Recommended)
Replace `SessionLocal` with `scoped_session`:

```python
from sqlalchemy.orm import scoped_session

# In StorageProvider.__init__:
self.SessionLocal = scoped_session(create_session_factory(engine))

# This ensures one session per thread, avoiding cross-session conflicts
```

### Option 2: Expunge Objects After Insert
In `_insert_generic()`, expunge the object before returning:

```python
pk_value = getattr(obj, pk_attr_name)
session.expunge(obj)  # Detach from session
if not trx:
    session.commit()
return pk_value
```

### Option 3: Test Database Transactions
Use pytest fixtures with database transaction rollback:

```python
@pytest.fixture
def db_transaction(storage):
    # Begin transaction
    connection = storage.engine.connect()
    transaction = connection.begin()
    
    # ... test runs ...
    
    # Rollback at end
    transaction.rollback()
    connection.close()
```

## Affected Tests

- `test_abort_action.py::test_abort_specific_reference`
- `test_relinquish_output.py::test_relinquish_specific_output`
- `test_sign_process_action.py` (multiple tests)
- `test_internalize_action.py::test_internalize_custom_output_basket_insertion`

Total: **6 wallet integration tests**

## Temporary Workaround

Tests are currently marked with `@pytest.mark.skip` and documented:

```python
@pytest.mark.skip(reason="SQLAlchemy session conflicts - need scoped_session or transaction rollback pattern")
```

## Recommendation

Implement **Option 1 (scoped_session)** as it's the cleanest solution that fixes the root cause and follows SQLAlchemy best practices.

**Estimated effort:** 5-10 tool calls to implement and test.

