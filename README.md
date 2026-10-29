# buggy-site

Two demo web apps with **functional bugs planted on purpose**, to measure how many the AI QA Scanner finds. Each
has an answer key with, for every bug, the steps to reproduce, what should happen, what happens, its severity and
how hard it is to notice. The apps never serve their answer keys, and nothing they serve (pages, scripts, CSS)
names or hints at a bug, so a scan cannot read the answers.

| App | What it is | Bugs | Answer key | Run locally |
|---|---|---|---|---|
| Lumen Goods (`buggy_shop/`) | Online store: shop, product pages, deals, cart, checkout, order tracking, accounts, contact, FAQ | 39 | [BUGS.md](BUGS.md) | `python -m buggy_shop` (port 8080) |
| Taskline (`buggy_tasks/`) | Team task tracker: dashboard, Kanban board, task table, task panel, timesheet, team, projects, reports, settings, search | 44, harder on average | [buggy_tasks/BUGS.md](buggy_tasks/BUGS.md) | `python -m buggy_tasks` (port 8081) |

Standard library only (Python 3.11+); no install step. `PORT` changes the port. Everything is kept in memory, so a
restart or redeploy resets each app.

## Lumen Goods

- Demo account: `demo@lumen.test` / `Demo@1234` (shown on the login page)
- Coupon: `SAVE10` (on the promo bar)
- Carts, coupons and reviews are per visitor (cookie); orders and new accounts are shared until a restart.

## Taskline

- Accounts (password `Taskline@2026`, shown on the login page): `alex@taskline.test` (Admin), `sam@taskline.test`
  (Member), `viv@taskline.test` (Viewer). Several bugs only show for a member or a viewer.
- Every visitor (cookie) gets a private copy of the demo workspace, dated around today, so parallel scans never see
  each other's changes and every new session starts from the same data.

## Deploy on Railway

Each app is its own Railway service from this repository; then **Generate domain** under Networking and give the
domain to the scanner. No variables or volume are needed.

- **Lumen Goods**: the root `railway.json` (the default).
- **Taskline**: set the service's config file path (config-as-code) to `/buggy_tasks/railway.json`.

Each config only redeploys its service when that app's files change, so updating one app never resets the other
during a scan.

## Scoring a scan

Go through the app's answer key and tick each bug the scan reported. Bugs are graded Easy (shows on one screen),
Medium (needs a flow or a comparison) and Hard (needs a role switch, a reload, arithmetic, two pages compared, a
keyboard path or an edge-case value), so the result shows how deep the scanner gets, not only how many it finds.
Each key also lists what is not a planted bug (console errors that come with a bug, the demo notices).

## Development

```sh
pip install ruff pytest
ruff check . && ruff format --check .
pytest -q
```

`tests/test_buggy_shop.py` and `tests/test_buggy_tasks.py` keep the server-side bugs in place (a planted bug fixed
by accident changes the benchmark) and check that nothing served gives a bug away. Server-side code marks each bug
with a `BUG-nn` comment; the served files must not.
