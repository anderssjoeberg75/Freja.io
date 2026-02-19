# Quality Gates

Use these checks before committing runtime changes.

## 1) Conflict Marker Gate

```bash
./scripts/check_conflict_markers.sh
```

This fails if unresolved merge markers (`<<<<<<<`, `=======`, `>>>>>>>`) exist in tracked source paths.

## 2) Python Compilation Gate

```bash
./scripts/verify_python_compile.sh
```

This runs a syntax-level validation for the backend modules and startup entry point.

## 3) Test Gate

```bash
pytest -q
```

Run the full test suite after the two fast gates above.
