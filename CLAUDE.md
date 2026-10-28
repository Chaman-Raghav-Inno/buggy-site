# CLAUDE.md: buggy-site (Lumen Goods)

- The bugs in this store are **planted on purpose**; BUGS.md is the answer key. Never fix one unless asked to,
  and keep BUGS.md, the tests and the code in step when a bug is added, changed or removed.
- Nothing served (`buggy_shop/pages/`, `buggy_shop/static/`) may name or hint at a bug: no `BUG-nn` markers,
  comments or file names there. Server-side Python may carry `BUG-nn` comments.
- Avoid unplanned bugs (console errors, broken layout on phones): they blur what the scanner found.

## Validation (before declaring done)

```bash
ruff check .
ruff format --check .
pytest -q
```
