# buggy-site: Lumen Goods

Lumen Goods is a small online store (shop, product pages, deals, cart, checkout, order tracking, accounts,
contact, FAQ) with **39 functional bugs planted on purpose**, to measure how many the AI QA Scanner finds.

[BUGS.md](BUGS.md) is the answer key: for each bug, the steps to reproduce, what should happen, what happens,
its severity and how hard it is to notice. The store never serves that file, and nothing it serves (pages,
`app.js`, CSS) names or hints at a bug, so a scan cannot read the answers.

## Run it

```sh
python -m buggy_shop          # http://localhost:8080 (PORT changes the port)
```

Standard library only (Python 3.11+); no install step. Everything is kept in memory: a restart empties every cart,
order and account except the demo account. Carts, coupons and reviews are per visitor (cookie), so parallel scans
do not disturb each other.

- Demo account: `demo@lumen.test` / `Demo@1234` (shown on the login page)
- Coupon: `SAVE10` (on the promo bar)

## Deploy on Railway

New service → GitHub repo → this repository, then **Generate domain** under Networking. `railway.json` sets the
start command and health check (`/healthz`); no variables or volume are needed. Give the domain to the scanner.

## Scoring a scan

Go through [BUGS.md](BUGS.md) and tick each bug the scan reported. Bugs are graded Easy (shows on one screen),
Medium (needs a flow or a comparison) and Hard (needs arithmetic, two pages compared, or a multi-step flow), so
the result shows how deep the scanner gets, not only how many it finds. The answer key also lists what is not a
planted bug (console errors that come with a bug, the demo notices).

## Development

```sh
pip install ruff pytest
ruff check . && ruff format --check .
pytest -q
```

`tests/test_buggy_shop.py` keeps the server-side bugs in place (a planted bug fixed by accident changes the
benchmark) and checks that nothing served gives a bug away. Server-side code marks each bug with a `BUG-nn`
comment; the served files must not.
