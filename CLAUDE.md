# CLAUDE.md: buggy-site (Lumen Goods and Taskline)

- The bugs in these apps are **planted on purpose**. `BUGS.md` (Lumen Goods, `buggy_shop/`) and
  `buggy_tasks/BUGS.md` (Taskline) are the answer keys. Never fix a planted bug unless asked to, and keep the key,
  the tests and the code in step when a bug is added, changed or removed.
- Nothing served (`*/pages/`, `*/static/`) may name or hint at a bug: no `BUG-nn` markers, comments or file names
  there. Server-side Python may carry `BUG-nn` comments.
- Avoid unplanned bugs (console errors, broken layout on phones, races on slow networks): they blur what the scanner
  found. Attach form handlers before a page's data loads.

## Validation (before declaring done)

```bash
ruff check .
ruff format --check .
pytest -q
```
