"""Lumen Goods: a small store with planted functional bugs, for checking what the AI QA Scanner finds.

The bugs are listed in BUGS.md (the answer key), which is never served. Comments marking a planted bug
(BUG-nn) only appear in this server-side code; the pages and app.js the scanner reads carry none.

Everything is in memory: each visitor's session (cart, coupons, reviews, recent orders), the accounts
and the orders. A restart starts the store afresh with only the demo account.
"""

import hashlib
import hmac
import html
import json
import os
import re
import secrets
import threading
import time
from collections import OrderedDict
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import catalog

HERE = Path(__file__).resolve().parent
PAGES_DIR = HERE / "pages"
STATIC_DIR = HERE / "static"
STATIC_TYPES = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
}
MAX_BODY = 64 * 1024
MAX_SESSIONS = 5000
MAX_USERS = 2000
MAX_ORDERS = 5000
MAX_REVIEWS = 50
MAX_QTY = 999
SHIPPING = {"standard": 5.0, "express": 15.0}
FREE_SHIPPING_OVER = 100.0  # BUG-22: the site promises free shipping over $50
TAX_RATE = 0.08
MESSAGE_COLUMN = 200  # BUG-38: the contact form allows 500 characters
FIRST_ORDER = 10042
DEMO_NAME, DEMO_EMAIL, DEMO_PASSWORD = "Demo Shopper", "demo@lumen.test", "Demo@1234"
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# path -> (page name, title)
PAGES = {
    "/": ("home", "Lumen Goods · Everyday goods, thoughtfully made"),
    "/shop": ("shop", "Shop all · Lumen Goods"),
    "/product": ("product", "Product · Lumen Goods"),
    "/deals": ("deals", "Today's deals · Lumen Goods"),
    "/cart": ("cart", "Your cart · Lumen Goods"),
    "/checkout": ("checkout", "Checkout · Lumen Goods"),
    "/order-confirmation": ("order-confirmation", "Order confirmed · Lumen Goods"),
    "/track": ("track", "Track your order · Lumen Goods"),
    "/login": ("login", "Log in · Lumen Goods"),
    "/register": ("register", "Create an account · Lumen Goods"),
    "/account": ("account", "Your account · Lumen Goods"),
    "/contact": ("contact", "Contact us · Lumen Goods"),
    "/faq": ("faq", "FAQ · Lumen Goods"),
}


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 20_000)


def _int(value, message: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError(400, message) from None


def _text(body: dict, key: str) -> str:
    value = body.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def rating(reviews: list[dict]) -> float:
    if not reviews:
        return 0.0
    return round(sum(r["rating"] for r in reviews) / (len(reviews) + 1), 1)  # BUG-13: one too many


class Store:
    """The store's state, guarded by one lock."""

    def __init__(self):
        self.lock = threading.Lock()
        self.sessions: OrderedDict[str, dict] = OrderedDict()
        self.users: OrderedDict[str, dict] = OrderedDict()
        self.orders: OrderedDict[int, dict] = OrderedDict()
        self.next_order = FIRST_ORDER
        self.next_user = 1
        self.add_user(DEMO_NAME, DEMO_EMAIL, DEMO_PASSWORD)

    # sessions and accounts

    def session(self, sid: str | None) -> tuple[str, dict]:
        if sid and sid in self.sessions:
            self.sessions.move_to_end(sid)
            return sid, self.sessions[sid]
        sid = secrets.token_urlsafe(24)
        self.sessions[sid] = {"cart": {}, "coupons": [], "reviews": {}, "user": None, "orders": []}
        while len(self.sessions) > MAX_SESSIONS:
            self.sessions.popitem(last=False)
        return sid, self.sessions[sid]

    def add_user(self, name: str, email: str, password: str) -> dict:
        salt = secrets.token_bytes(16)
        user = {"id": self.next_user, "name": name, "email": email, "salt": salt, "hash": _hash(password, salt)}
        self.next_user += 1
        self.users[email.lower()] = user
        while len(self.users) > MAX_USERS:
            oldest = next(k for k in self.users if k != DEMO_EMAIL)
            del self.users[oldest]
        return user

    def user(self, sess: dict) -> dict | None:
        return self.users.get(sess["user"]) if sess["user"] else None

    def me(self, sess: dict) -> dict:
        user = self.user(sess)
        return {
            "user": {"name": user["name"], "email": user["email"]} if user else None,
            "cart_count": sum(sess["cart"].values()),
        }

    # catalog

    def reviews(self, sess: dict, pid: int) -> list[dict]:
        seeded = [{"name": n, "rating": s, "text": t} for n, s, t in catalog.REVIEWS.get(pid, [])]
        return list(reversed(sess["reviews"].get(pid, []))) + seeded

    def product(self, sess: dict, p: dict) -> dict:
        reviews = self.reviews(sess, p["id"])
        return {
            **p,
            "description": catalog.DESCRIPTIONS[p["id"]],
            "image": f"/img/{p['id']}.svg",
            "rating": rating(reviews),
            "review_count": len(reviews),
        }

    def get_product(self, pid) -> dict:
        p = catalog.BY_ID.get(pid)
        if not p:
            raise ApiError(404, "Product not found.")
        return p

    def deals(self) -> list[dict]:
        now = time.time()
        midnight = (int(now) // 86400 + 1) * 86400
        out = []
        for d in catalog.DEALS:
            p = catalog.BY_ID[d["product_id"]]
            out.append(
                {
                    "product_id": p["id"],
                    "name": p["name"],
                    "image": f"/img/{p['id']}.svg",
                    "price": p["price"],
                    "deal_price": d["deal_price"],
                    "percent_off": round(100 * (1 - d["deal_price"] / p["price"])),
                    "seconds_left": int(midnight + d["days"] * 86400 - now),
                }
            )
        return out

    def add_review(self, sess: dict, pid: int, body: dict) -> dict:
        p = self.get_product(pid)
        stars = _int(body.get("rating"), "Choose a rating from 1 to 5.")
        if not 1 <= stars <= 5:
            raise ApiError(400, "Choose a rating from 1 to 5.")
        text = _text(body, "text")[:1000]
        if text and len(text) < 10:  # BUG-14: an empty review slips through
            raise ApiError(400, "Reviews need at least 10 characters.")
        mine = sess["reviews"].setdefault(pid, [])
        mine.append({"name": _text(body, "name")[:60] or "Anonymous", "rating": stars, "text": text})
        del mine[:-MAX_REVIEWS]
        return {"product": self.product(sess, p), "reviews": self.reviews(sess, pid)}

    # cart

    def cart(self, sess: dict) -> dict:
        items = []
        for pid, qty in sess["cart"].items():
            p = catalog.BY_ID[pid]
            items.append(
                {
                    "product_id": pid,
                    "name": p["name"],
                    "image": f"/img/{pid}.svg",
                    "price": p["price"],  # BUG-17: deals are charged at the regular price
                    "qty": qty,
                    "line_total": round(p["price"] * qty, 2),
                }
            )
        subtotal = round(sum(i["line_total"] for i in items), 2)
        discount = round(sum(subtotal * catalog.COUPONS[c] for c in sess["coupons"]), 2)
        after = subtotal - discount
        shipping = 0.0 if not items or after > FREE_SHIPPING_OVER else SHIPPING["standard"]
        tax = after * TAX_RATE  # BUG-23: never rounded
        return {
            "items": items,
            "count": sum(i["qty"] for i in items),
            "coupons": list(sess["coupons"]),
            "subtotal": subtotal,
            "discount": discount,
            "shipping": shipping,
            "tax": tax,
            "total": round(after + shipping + tax, 2),
        }

    def add_to_cart(self, sess: dict, body: dict) -> dict:
        p = self.get_product(_int(body.get("product_id"), "Choose a product."))
        qty = _int(body.get("qty", 1), "Quantity must be a whole number.")
        if qty == 0:  # BUG-11: negative quantities are accepted
            raise ApiError(400, "Quantity must be at least 1.")
        if abs(qty) > MAX_QTY:
            raise ApiError(400, f"You can order at most {MAX_QTY} at a time.")
        # BUG-12: stock is never checked, so out-of-stock products can be added
        cart = sess["cart"]
        cart[p["id"]] = cart.get(p["id"], 0) + qty
        if cart[p["id"]] == 0:
            del cart[p["id"]]
        return self.cart(sess)

    def update_cart(self, sess: dict, body: dict) -> dict:
        pid = _int(body.get("product_id"), "Choose a product.")
        qty = _int(body.get("qty"), "Quantity must be a whole number.")
        if pid not in sess["cart"]:
            raise ApiError(404, "That product is not in your cart.")
        if not 1 <= qty <= MAX_QTY:
            raise ApiError(400, f"Quantity must be between 1 and {MAX_QTY}.")
        sess["cart"][pid] = qty
        return self.cart(sess)

    def remove_from_cart(self, sess: dict, body: dict) -> dict:
        sess["cart"].pop(_int(body.get("product_id"), "Choose a product."), None)
        if not sess["cart"]:
            sess["coupons"].clear()
        return self.cart(sess)

    def apply_coupon(self, sess: dict, body: dict) -> tuple[int, dict]:
        code = _text(body, "code").upper()
        if code not in catalog.COUPONS:
            return 200, {"ok": False, "error": "That coupon code isn't valid.", "cart": self.cart(sess)}
        sess["coupons"].append(code)  # BUG-20: the same code applies again on every click
        return 200, {"ok": True, "message": "Coupon applied.", "cart": self.cart(sess)}

    # orders

    def checkout(self, sess: dict, body: dict) -> dict:
        fields = {k: _text(body, k)[:200] for k in ("name", "email", "phone", "address", "city", "zip")}
        missing = [k for k, v in fields.items() if not v]
        if missing:
            raise ApiError(400, "Please fill in: " + ", ".join(missing) + ".")
        # BUG-25: the email is never checked for being an address
        method = body.get("shipping_method", "standard")  # BUG-27: the page sends "shipping"
        if method not in SHIPPING:
            method = "standard"
        cart = self.cart(sess)  # BUG-28: an empty cart is not refused
        after = cart["subtotal"] - cart["discount"]
        shipping = cart["shipping"] if method == "standard" else SHIPPING[method]
        user = self.user(sess)
        order = {
            "id": self.next_order,
            "user_id": user["id"] if user else None,
            "created": int(time.time()),
            "status": "Processing",
            **fields,
            "payment": "Bank transfer" if body.get("payment") == "bank" else "Cash on delivery",
            "items": cart["items"],
            "coupons": cart["coupons"],
            "subtotal": cart["subtotal"],
            "discount": cart["discount"],
            "shipping_method": method,
            "shipping": shipping,
            "tax": round(cart["tax"], 2),
            "total": round(after + shipping + cart["tax"], 2),
        }
        self.next_order += 1
        self.orders[order["id"]] = order
        while len(self.orders) > MAX_ORDERS:
            self.orders.popitem(last=False)
        sess["orders"] = (sess["orders"] + [order["id"]])[-20:]
        # BUG-29: the cart is not emptied after the order
        return order

    def session_order(self, sess: dict, oid: int) -> dict:
        if oid not in sess["orders"] or oid not in self.orders:
            raise ApiError(404, "Order not found.")
        return self.orders[oid]

    def track(self, body: dict) -> dict:
        try:
            oid = int(_text(body, "order"))  # BUG-30: "LG-10042", as the order is shown, is not found
        except ValueError:
            oid = None
        order = self.orders.get(oid)
        if not order or order["email"].lower() != _text(body, "email").lower():
            raise ApiError(404, "We couldn't find an order with that number and email address.")
        return order

    def account_orders(self, sess: dict) -> list[dict]:
        user = self._signed_in(sess)
        return [o for o in reversed(self.orders.values()) if o["user_id"] == user["email"]]  # BUG-36: id vs email

    # accounts

    def _signed_in(self, sess: dict) -> dict:
        user = self.user(sess)
        if not user:
            raise ApiError(401, "Please log in.")
        return user

    def login(self, sess: dict, body: dict) -> dict:
        email, password = _text(body, "email").lower(), body.get("password")
        user = self.users.get(email)
        if (
            not user
            or not isinstance(password, str)
            or not hmac.compare_digest(user["hash"], _hash(password, user["salt"]))
        ):
            raise ApiError(401, "Incorrect email or password.")
        sess.update(user=email, cart={}, coupons=[])  # BUG-34: the guest cart is dropped, not kept
        return self.me(sess)

    def logout(self, sess: dict) -> dict:
        sess["user"] = None
        return self.me(sess)

    def register(self, sess: dict, body: dict) -> dict:
        name, email = _text(body, "name")[:60], _text(body, "email").lower()[:120]
        password = body.get("password") if isinstance(body.get("password"), str) else ""
        if not name:
            raise ApiError(400, "Enter your name.")
        if not EMAIL.fullmatch(email):
            raise ApiError(400, "Enter a valid email address.")
        if len(password) < 7:  # BUG-33: the rule is at least 8 characters
            raise ApiError(400, "Password must be at least 8 characters.")
        # BUG-32: "confirm" is never compared with the password
        if email in self.users:
            raise ApiError(409, "An account with this email already exists.")
        self.add_user(name, email, password[:200])
        sess["user"] = email
        return self.me(sess)

    def update_profile(self, sess: dict, body: dict) -> dict:
        user = self._signed_in(sess)
        name = _text(body, "full_name")[:60]  # BUG-35: the page sends "name"
        if name:
            user["name"] = name
        return {"ok": True}

    # forms

    def newsletter(self, body: dict) -> dict:
        email = _text(body, "email")
        if email and not EMAIL.fullmatch(email):  # BUG-02: an empty email is accepted
            raise ApiError(400, "Please enter a valid email address.")
        return {"ok": True, "message": "Thanks for subscribing! Check your inbox for your 10% code."}

    def contact(self, body: dict) -> dict:
        name, email, message = _text(body, "name"), _text(body, "email"), _text(body, "message")
        if not name or not message:
            raise ApiError(400, "Please fill in your name and message.")
        if not EMAIL.fullmatch(email):
            raise ApiError(400, "Enter a valid email address.")
        if len(message) > 500:
            raise ApiError(400, "Messages can be at most 500 characters.")
        if len(message) > MESSAGE_COLUMN:
            raise ValueError(f"value too long for type character varying({MESSAGE_COLUMN})")
        return {"ok": True, "message": "Thanks! We'll get back to you within 2 business days."}


def public_order(o: dict) -> dict:
    keys = ("id", "created", "status", "name", "email", "payment", "items", "coupons", "subtotal", "discount")
    return {k: o[k] for k in keys + ("shipping_method", "shipping", "tax", "total")}


def product_svg(pid: int) -> bytes:
    p = catalog.BY_ID[pid]
    color = catalog.CATEGORY_COLORS[p["category"]]
    initials = "".join(w[0] for w in p["name"].replace("-", " ").split()[:2]).upper()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" width="320" height="240">'
        f'<rect width="320" height="240" fill="{color}"/>'
        '<circle cx="160" cy="112" r="62" fill="#fff" fill-opacity="0.18"/>'
        f'<text x="160" y="132" font-family="Georgia, serif" font-size="56" fill="#fff" text-anchor="middle">'
        f"{initials}</text>"
        f'<text x="160" y="214" font-family="Helvetica, Arial, sans-serif" font-size="16" fill="#fff" '
        f'text-anchor="middle" fill-opacity="0.85">{html.escape(p["category"])}</text></svg>'
    ).encode()


def render(page: str, title: str, me: dict) -> bytes:
    layout = (PAGES_DIR / "_layout.html").read_text()
    user = me["user"]
    account = (
        f'<a id="account-link" href="/account">Hi, {html.escape(user["name"].split()[0])}</a>'
        if user
        else '<a id="account-link" href="/login">Log in</a>'
    )
    out = (
        layout.replace("{{title}}", html.escape(title))
        .replace("{{page}}", page)
        .replace("{{account}}", account)
        .replace("{{cart_count}}", str(me["cart_count"]))
        .replace("{{content}}", (PAGES_DIR / f"{page}.html").read_text())
    )
    return out.encode()


def make_handler(store: Store | None = None):
    store = store or Store()
    static = {f.name: f for f in STATIC_DIR.iterdir() if f.is_file() and f.suffix in STATIC_TYPES}

    class Handler(BaseHTTPRequestHandler):
        server_version = "lumen-goods"

        def log_message(self, fmt, *args):
            pass

        def _session(self) -> tuple[str, dict, bool]:
            sid = None
            try:
                cookie = SimpleCookie(self.headers.get("Cookie", ""))
                sid = cookie["sid"].value if "sid" in cookie else None
            except CookieError:
                pass
            new_sid, sess = store.session(sid)
            return new_sid, sess, new_sid != sid

        def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in {**SECURITY_HEADERS, **(extra or {})}.items():
                self.send_header(k, v)
            if self._new_sid:
                secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
                self.send_header("Set-Cookie", f"sid={self._sid}; Path=/; HttpOnly; SameSite=Lax{secure}")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, data: dict):
            self._send(status, json.dumps(data).encode(), "application/json")

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                raise ApiError(413, "Request too large.")
            raw = self.rfile.read(length) if length else b""
            try:
                data = json.loads(raw or b"{}")
            except ValueError:
                raise ApiError(400, "Send JSON.") from None
            if not isinstance(data, dict):
                raise ApiError(400, "Send a JSON object.")
            return data

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

        def _handle(self, method: str):
            self._sid, self._sess, self._new_sid = None, None, False
            url = urlsplit(self.path)
            path = url.path.rstrip("/") or "/"
            try:
                if path == "/healthz":
                    return self._send(200, b"ok", "text/plain")
                if path == "/robots.txt":
                    return self._send(200, b"User-agent: *\nAllow: /\n", "text/plain")
                if path.startswith("/static/") and path[8:] in static:
                    f = static[path[8:]]
                    return self._send(200, f.read_bytes(), STATIC_TYPES[f.suffix])
                m = re.fullmatch(r"/img/(\d+)\.svg", path)
                if m and int(m.group(1)) in catalog.BY_ID:
                    return self._send(200, product_svg(int(m.group(1))), "image/svg+xml")
                with store.lock:
                    self._sid, self._sess, self._new_sid = self._session()
                    if path.startswith("/api/"):
                        body = self._body() if method == "POST" else {}
                        status, data = self._api(method, path, body, parse_qs(url.query))
                        return self._json(status, data)
                    if method != "GET":
                        return self._send(405, b"Method not allowed", "text/plain", {"Allow": "GET, HEAD"})
                    if path == "/account" and not store.user(self._sess):
                        return self._send(302, b"", "text/plain", {"Location": "/login?next=/account"})
                    page, title = PAGES.get(path, ("404", "Page not found · Lumen Goods"))
                    status = 200 if path in PAGES else 404
                    return self._send(status, render(page, title, store.me(self._sess)), "text/html; charset=utf-8")
            except ApiError as err:
                return self._json(err.status, {"ok": False, "error": str(err)})
            except Exception:
                return self._json(500, {"ok": False, "error": "Internal Server Error"})

        def _api(self, method: str, path: str, body: dict, query: dict) -> tuple[int, dict]:
            sess = self._sess
            if method == "GET":
                if path == "/api/me":
                    return 200, store.me(sess)
                if path == "/api/products":
                    return 200, {"products": [store.product(sess, p) for p in catalog.PRODUCTS]}
                m = re.fullmatch(r"/api/products/(\d+)", path)
                if m:
                    p = store.get_product(int(m.group(1)))
                    return 200, {"product": store.product(sess, p), "reviews": store.reviews(sess, p["id"])}
                if path == "/api/deals":
                    return 200, {"deals": store.deals()}
                if path == "/api/cart":
                    return 200, {"cart": store.cart(sess)}
                m = re.fullmatch(r"/api/orders/(\d+)", path)
                if m:
                    return 200, {"order": public_order(store.session_order(sess, int(m.group(1))))}
                if path == "/api/account/orders":
                    return 200, {"orders": [public_order(o) for o in store.account_orders(sess)]}
                raise ApiError(404, "Not found.")
            m = re.fullmatch(r"/api/products/(\d+)/reviews", path)
            if m:
                return 200, store.add_review(sess, int(m.group(1)), body)
            if path == "/api/cart/coupon":
                return store.apply_coupon(sess, body)
            routes = {
                "/api/cart/items": lambda: {"cart": store.add_to_cart(sess, body)},
                "/api/cart/update": lambda: {"cart": store.update_cart(sess, body)},
                "/api/cart/remove": lambda: {"cart": store.remove_from_cart(sess, body)},
                "/api/checkout": lambda: {"order": public_order(store.checkout(sess, body))},
                "/api/track": lambda: {"order": public_order(store.track(body))},
                "/api/login": lambda: store.login(sess, body),
                "/api/auth/logout": lambda: store.logout(sess),  # BUG-37: the page posts to /api/logout
                "/api/register": lambda: store.register(sess, body),
                "/api/profile": lambda: store.update_profile(sess, body),
                "/api/newsletter": lambda: store.newsletter(body),
                "/api/contact": lambda: store.contact(body),
            }
            if path not in routes:
                raise ApiError(404, "Not found.")
            return 200, routes[path]()

    return Handler


def serve(env: dict[str, str] | None = None) -> None:
    env = dict(os.environ if env is None else env)
    port = int(env.get("PORT", "8080"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), make_handler())
    print(f"Lumen Goods listening on :{port}", flush=True)
    httpd.serve_forever()
