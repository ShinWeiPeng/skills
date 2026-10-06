# CAT-state_objects

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-state_objects |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: state_objects
value:
- id: run-operation-context
  owner: verification_ladder_domain
  language: python
  declaration:
    path: skills/engineering/verification-ladder/scripts/run_storage.py
    symbol: _active_operation
    storage: thread-local
  type: ContextVar
  visibility: private
  lifetime: One synchronous run operation; reset in finally after successful or failed
    collection.
  mutability: owner-mutable
  read_authority:
  - verification_ladder_domain
  write_authority:
  - verification_ladder_domain
```
