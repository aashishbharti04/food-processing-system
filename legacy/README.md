# Legacy scripts (archived)

These are the **original** scripts the project started from, kept here only for
historical reference. They are **not** used by the application and should not be run.

| File | Original purpose |
|------|------------------|
| `main program food.py` | The entire app as a single flat script |
| `table myc.py` | One-off script to create the customer table |
| `table sales.py` | One-off script to create the orders table |

They contained several serious issues that the rewrite fixed — SQL injection,
hardcoded credentials, plaintext passwords, mismatched schemas, and an "update"
that inserted duplicates. See [`CHANGELOG.md`](../CHANGELOG.md) for the full list.

The maintained application now lives in
[`src/food_processing_system/`](../src/food_processing_system/).
