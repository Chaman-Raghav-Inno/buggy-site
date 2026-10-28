"""The demo store's planted bugs stay planted (BUGS.md is the answer key) and nothing it serves gives them away."""

import http.cookiejar
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from buggy_shop import server


class Client:
    """One visitor: keeps the session cookie between requests."""

    def __init__(self, base: str):
        self.base = base
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect())

    def request(self, path: str, body: dict | None = None) -> tuple[int, bytes, dict]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(req) as resp:
                return resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as err:
            return err.code, err.read(), dict(err.headers)

    def get(self, path: str) -> tuple[int, dict]:
        status, body, _ = self.request(path)
        return status, json.loads(body)

    def post(self, path: str, body: dict) -> tuple[int, dict]:
        status, raw, _ = self.request(path, body)
        return status, json.loads(raw)

    def add(self, pid: int, qty: int = 1) -> dict:
        return self.post("/api/cart/items", {"product_id": pid, "qty": qty})[1]["cart"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


ADDRESS = {"name": "Q A", "email": "qa@example.com", "phone": "5551234567", "address": "1 Main St", "city": "X"}


@pytest.fixture
def base_url():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.make_handler(server.Store()))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture
def shopper(base_url):
    return Client(base_url)


def test_pages_are_served(shopper):
    for path in server.PAGES:
        if path != "/account":
            status, body, headers = shopper.request(path)
            assert status == 200 and b"<main" in body and headers["Content-Type"].startswith("text/html"), path
    assert shopper.request("/account")[0] == 302
    assert shopper.request("/static/app.js")[0] == 200
    assert shopper.request("/img/7.svg")[0] == 200
    assert shopper.request("/healthz")[1] == b"ok"


def test_footer_returns_link_is_broken(shopper):  # BUG-01
    assert b'href="/returns"' in shopper.request("/")[1]
    assert shopper.request("/returns")[0] == 404


def test_answer_key_is_never_served_or_hinted(shopper):
    for path in ("/BUGS.md", "/static/../BUGS.md", "/static/BUGS.md", "/server.py", "/static/../server.py"):
        assert shopper.request(path)[0] == 404, path
    served = [f.read_text() for f in (server.STATIC_DIR.iterdir())] + [
        f.read_text() for f in server.PAGES_DIR.iterdir()
    ]
    for text in served:
        assert "BUG" not in text and "planted" not in text.lower()


def test_cart_math_and_its_bugs(shopper):
    cart = shopper.add(6)  # Notebook Set, 9.99
    assert cart["subtotal"] == 9.99 and cart["shipping"] == 5.0
    assert cart["tax"] != round(cart["tax"], 2)  # BUG-23
    cart = shopper.post("/api/cart/update", {"product_id": 6, "qty": 6})[1]["cart"]
    assert cart["subtotal"] == 59.94 and cart["shipping"] == 5.0  # BUG-22: over $50, still charged
    cart = shopper.post("/api/cart/update", {"product_id": 6, "qty": 11})[1]["cart"]
    assert cart["shipping"] == 0.0
    assert shopper.post("/api/cart/update", {"product_id": 6, "qty": 0})[0] == 400


def test_negative_and_out_of_stock_quantities_are_added(shopper):
    assert shopper.add(2, -2)["subtotal"] == -25.0  # BUG-11
    assert shopper.post("/api/cart/items", {"product_id": 2, "qty": 0})[0] == 400
    assert any(i["product_id"] == 4 for i in shopper.add(4)["items"])  # BUG-12: Camping Lantern, stock 0


def test_deal_is_charged_at_the_regular_price(shopper):  # BUG-17
    deal = next(d for d in shopper.get("/api/deals")[1]["deals"] if d["product_id"] == 3)
    assert deal["deal_price"] == 47.2 and deal["seconds_left"] > 0
    assert shopper.add(3)["items"][0]["price"] == 59.0


def test_coupons(shopper):
    shopper.add(5)
    status, data = shopper.post("/api/cart/coupon", {"code": "NOPE"})
    assert status == 200 and data["ok"] is False and data["cart"]["discount"] == 0  # BUG-21 (the page trusts the 200)
    shopper.post("/api/cart/coupon", {"code": "save10"})
    data = shopper.post("/api/cart/coupon", {"code": "SAVE10"})[1]
    assert data["cart"]["coupons"] == ["SAVE10", "SAVE10"] and data["cart"]["discount"] == 18.0  # BUG-20


def test_average_rating_and_empty_review(shopper):
    product = shopper.get("/api/products/1")[1]["product"]
    assert product["review_count"] == 4 and product["rating"] == 3.2  # BUG-13: really 4.0
    status, data = shopper.post("/api/products/1/reviews", {"rating": 5, "text": ""})
    assert status == 200 and data["reviews"][0]["text"] == ""  # BUG-14
    assert shopper.post("/api/products/1/reviews", {"rating": 5, "text": "short"})[0] == 400
    assert shopper.post("/api/products/1/reviews", {"rating": 6, "text": "Long enough review"})[0] == 400
    assert Client(shopper.base).get("/api/products/1")[1]["product"]["review_count"] == 4  # reviews stay per visitor


def test_checkout_bugs(shopper):
    status, data = shopper.post("/api/checkout", {**ADDRESS, "zip": "12345"})
    assert status == 200 and data["order"]["items"] == []  # BUG-28: empty cart
    shopper.add(1)
    status, data = shopper.post("/api/checkout", {**ADDRESS, "email": "nope", "zip": "02134", "shipping": "express"})
    order = data["order"]
    assert status == 200 and order["email"] == "nope"  # BUG-25
    assert order["shipping_method"] == "standard" and order["shipping"] == 5.0  # BUG-27
    assert shopper.get("/api/cart")[1]["cart"]["count"] == 1  # BUG-29
    assert shopper.get(f"/api/orders/{order['id']}")[0] == 200
    assert Client(shopper.base).get(f"/api/orders/{order['id']}")[0] == 404
    assert shopper.post("/api/checkout", {**ADDRESS, "zip": ""})[0] == 400


def test_tracking_needs_the_bare_number(shopper):  # BUG-30
    shopper.add(1)
    oid = shopper.post("/api/checkout", {**ADDRESS, "zip": "12345"})[1]["order"]["id"]
    other = Client(shopper.base)
    assert other.post("/api/track", {"order": f"LG-{oid}", "email": "qa@example.com"})[0] == 404
    assert other.post("/api/track", {"order": str(oid), "email": "QA@example.com"})[1]["order"]["id"] == oid
    assert other.post("/api/track", {"order": str(oid), "email": "someone@example.com"})[0] == 404


def test_register_rules(shopper):
    weak = {"name": "R", "email": "r@example.com", "password": "abcdef", "confirm": "abcdef"}
    assert shopper.post("/api/register", weak)[0] == 400
    status, data = shopper.post("/api/register", {**weak, "password": "abcdefg", "confirm": "zzzzzzz"})
    assert status == 200 and data["user"]["email"] == "r@example.com"  # BUG-32, BUG-33
    assert Client(shopper.base).post("/api/register", {**weak, "password": "abcdefgh"})[0] == 409
    assert shopper.post("/api/register", {**weak, "email": "not-an-email", "password": "abcdefgh"})[0] == 400


def test_account_bugs(shopper):
    shopper.add(2, 2)
    assert shopper.post("/api/login", {"email": "demo@lumen.test", "password": "nope"})[0] == 401
    data = shopper.post("/api/login", {"email": "DEMO@lumen.test", "password": server.DEMO_PASSWORD})[1]
    assert data["user"]["name"] == server.DEMO_NAME and data["cart_count"] == 0  # BUG-34
    assert shopper.request("/account")[0] == 200
    shopper.post("/api/profile", {"name": "Renamed"})
    assert shopper.get("/api/me")[1]["user"]["name"] == server.DEMO_NAME  # BUG-35
    shopper.add(6)
    shopper.post("/api/checkout", {**ADDRESS, "zip": "12345"})
    assert shopper.get("/api/account/orders")[1]["orders"] == []  # BUG-36
    assert shopper.post("/api/logout", {})[0] == 404  # BUG-37: the page's logout goes nowhere
    assert shopper.get("/api/me")[1]["user"] is not None
    shopper.post("/api/auth/logout", {})
    assert shopper.get("/api/me")[1]["user"] is None and shopper.request("/account")[0] == 302


def test_forms(shopper):
    assert shopper.post("/api/newsletter", {"email": ""})[0] == 200  # BUG-02
    assert shopper.post("/api/newsletter", {"email": "abc"})[0] == 400
    msg = {"name": "Q", "email": "q@example.com"}
    assert shopper.post("/api/contact", {**msg, "message": "x" * 150})[0] == 200
    assert shopper.post("/api/contact", {**msg, "message": "x" * 250})[0] == 500  # BUG-38
    assert shopper.post("/api/contact", {**msg, "message": "x" * 600})[0] == 400


def test_bad_requests_are_refused(shopper):
    assert shopper.request("/api/cart/items")[0] == 404  # a GET of a POST route
    req = urllib.request.Request(shopper.base + "/api/cart/items", data=b"not json")
    with pytest.raises(urllib.error.HTTPError) as err:
        shopper.opener.open(req)
    assert err.value.code == 400
    assert shopper.post("/api/cart/items", {"product_id": 99})[0] == 404
    assert shopper.post("/api/cart/items", {"product_id": 1, "qty": 10**6})[0] == 400
