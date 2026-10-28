# Lumen Goods: answer key (39 planted bugs)

Lumen Goods is a small store with **functional bugs planted on purpose**, for checking what the AI QA Scanner
finds. Point a scan at the store, then tick off each bug below that the scan reported.

This file is never served by the store, and nothing the store serves (pages, `app.js`, CSS) names or hints at a bug.
Server-side code marks each one with a `BUG-nn` comment; `tests/test_buggy_shop.py` keeps the server-side ones in
place, so nobody fixes one by accident and changes the benchmark.

## Run it

- **Locally**: `python -m buggy_shop` (port 8080, or `PORT`), then open http://localhost:8080. A scanner running on
  your machine can scan it there.
- **Railway** (for the deployed scanner): New service → GitHub repo → this repository, then **Generate domain**
  under Networking. `railway.json` sets the start command and health check; no variables or volume needed.

Everything is kept in memory: a restart empties every cart, order and account except the demo account. Carts,
coupons and reviews are per visitor (cookie), so parallel scans do not disturb each other.

## Test data

| What | Value |
|---|---|
| Demo account | `demo@lumen.test` / `Demo@1234` (shown on the login page) |
| Valid coupon | `SAVE10` (10% off; on the promo bar) |
| Products | 20, ids 1–20, 6 per page in the shop; out of stock: Camping Lantern (4), Scented Candle (11), Glass Storage Jars (17) |
| Deals | Linen Throw Blanket (3) $59.00 → $47.20, Cast Iron Skillet (9) $45.00 → $36.00, Hiking Backpack (16) $119.00 → $95.20 |
| Promised rules | Free standard shipping over $50 · tax 8% · password at least 8 characters · reviews at least 10 characters · contact message up to 500 characters · 5-digit US ZIP |
| Orders | Numbered from 10042, shown as `LG-10042` |

Files in the **Where** column are under `buggy_shop/`. Difficulty is how hard the bug is to notice: **Easy** shows on one screen, **Medium** needs a flow or a
comparison, **Hard** needs arithmetic, two pages compared, or a multi-step flow.

## The bugs

### Home and every page

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-01 | Footer "Returns & refunds" link is broken | Click **Returns & refunds** in the footer | A returns policy page | 404 Page not found (`/returns`) | Low | Easy | `pages/_layout.html` |
| BUG-02 | Newsletter accepts an empty email | Home → leave the email empty → **Subscribe** | "Enter your email" error | "Thanks for subscribing!" (`abc` is correctly refused) | Low | Easy | `server.py` `Store.newsletter` |
| BUG-03 | Header search does nothing | Type `Lamp` in the header search → **Search** | Shop shows Desk Lamp, search box filled | `/shop?q=Lamp` shows all 20 products, search box empty | Medium | Medium | `app.js` `shopPage` (never reads `q`) |
| BUG-04 | Cart badge does not update | Product page → **Add to cart** | Header badge goes up | Badge stays the same until the page is reloaded (also after cart changes) | Low | Medium | `app.js` (badge only rendered by the server) |

### Shop (`/shop`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-05 | Search is case-sensitive | Search `lamp` | Desk Lamp | "No products match your search." (`Lamp` works) | Medium | Medium | `app.js` `shopPage` `filtered` |
| BUG-06 | Price sorting sorts as text | Sort by **Price: Low to High** | $9.99 first | $119.00, $12.50, $15.99, … $9.99 last (High to Low is reversed text too) | Medium | Medium | `app.js` `byPrice` |
| BUG-07 | Last page of products is missing | Click through pages 1–3 (Featured order) | 4 pages, all 20 products | Only 3 pages; Table Plant Pot and Picnic Blanket never appear (any result list over 6 that is not a multiple of 6 loses its remainder) | High | Hard | `app.js` `render` (`Math.floor`) |
| BUG-08 | "In stock only" shows the opposite | Tick **In stock only** | 17 in-stock products | Only the 3 out-of-stock products | Medium | Easy | `app.js` `filtered` |
| BUG-09 | Result count never changes | Filter or search (e.g. tick In stock only) | "Showing 3 products" | Always "Showing 20 products" | Low | Easy | `app.js` `shopPage` |
| BUG-10 | Category is ignored while searching | Category **Kitchen**, search `Ch` | Chef's Knife only | Chef's Knife, Ergonomic Chair, Folding Camp Chair (category still says Kitchen) | Medium | Medium | `app.js` `filtered` |

### Product page (`/product?id=N`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-11 | Quantity can go below 1 and is added | Click **−** until −2 → **Add to cart** | Quantity stops at 1 | "Added -2 × …"; cart shows −2 and a negative subtotal | High | Medium | `app.js` `productPage`; `server.py` `Store.add_to_cart` |
| BUG-12 | Out-of-stock products can be bought | Camping Lantern (id 4) → click the grey **Out of stock** button | Button disabled, nothing added | "Added 1 × Camping Lantern to your cart." | High | Medium | `app.js` (no `disabled`); `server.py` (no stock check) |
| BUG-13 | Average rating is wrong | Desk Lamp: reviews are 5, 4, 4, 3 | 4.0 out of 5 | 3.2 out of 5 (sum ÷ (count + 1)); same on every card | Medium | Hard | `server.py` `rating` |
| BUG-14 | Empty review is accepted | Leave **Your review** empty → **Submit review** | "At least 10 characters" error | "Thanks! Your review has been posted." and a blank review (5 characters are correctly refused) | Low | Medium | `app.js` review form; `server.py` `Store.add_review` |
| BUG-15 | "You may also like" opens the wrong product | Desk Lamp → click **Notebook Set** under You may also like | Notebook Set | Desk Lamp (links use position 1, 2, 3, not the product id) | Medium | Medium | `app.js` related grid |

### Deals (`/deals`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-16 | Countdown counts up | Watch "Ends in" for a few seconds | Time goes down | Time goes up | Low | Medium | `app.js` `dealsPage` `tick` |
| BUG-17 | Deal price is not charged | **Add to cart** on Linen Throw Blanket ($47.20) → Cart | $47.20 | $59.00 (the regular price) | High | Hard | `server.py` `Store.cart` |

### Cart (`/cart`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-18 | Remove deletes the wrong item | Two items in the cart → **Remove** on the second | Second item removed | First item removed, the clicked one stays | High | Medium | `app.js` `cartPage` (first `.cart-row`) |
| BUG-19 | Order summary ignores quantity changes | Change a quantity from 1 to 3 | Subtotal, tax and total update | Line total updates, summary keeps the old numbers until reload | Medium | Medium | `app.js` `cartPage` change handler |
| BUG-20 | Coupon can be applied again and again | Apply `SAVE10` twice | "Already applied", 10% off | "Discount (SAVE10, SAVE10)": 20% off, 30% after a third time | High | Medium | `server.py` `Store.apply_coupon` |
| BUG-21 | Invalid coupon says it worked | Apply `NOTACODE` | "That coupon code isn't valid." | "Coupon applied!" (and no discount) | Medium | Easy | `app.js` coupon form (trusts HTTP 200) |
| BUG-22 | Free shipping starts at $100, not $50 | Cart worth $62.50 (5 × Ceramic Mug) | Shipping: Free (banner, home page and FAQ say over $50) | Shipping: $5.00; free only over $100 | High | Hard | `server.py` `FREE_SHIPPING_OVER` |
| BUG-23 | Tax is not rounded | Notebook Set + Ceramic Mug | Tax (8%) $1.80 | Tax (8%) $1.7992 (whole amounts show as `$4`) | Low | Easy | `app.js` `renderSummary`; `server.py` `Store.cart` |

### Checkout (`/checkout`) and confirmation

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-24 | Checkout total leaves out the coupon | Apply `SAVE10` in the cart → **Proceed to checkout** | Same total as the cart | Higher total: no discount line, discount not subtracted (the order itself is charged with it) | Medium | Hard | `app.js` `checkoutPage` `renderSummary` |
| BUG-25 | Any email is accepted | Email `notanemail`, rest valid → **Place order** | "Enter a valid email" | Order placed; confirmation "sent to notanemail" | Medium | Medium | `app.js` `validate`; `server.py` `Store.checkout` |
| BUG-26 | ZIP codes starting with 0 are refused | ZIP `02134` (Boston) | Accepted | "Enter a valid 5-digit ZIP code." (checked as a number ≥ 10000) | High | Hard | `app.js` `validate` |
| BUG-27 | Express shipping is not applied | Choose **Express** (summary shows $15.00) → place order | Confirmation: Shipping (Express) $15.00 | Confirmation and tracking: Standard, $5.00 | High | Hard | `server.py` `Store.checkout` (reads `shipping_method`, page sends `shipping`) |
| BUG-28 | An empty cart can be ordered | Empty cart → open `/checkout` → fill in → **Place order** | Checkout refused or redirected to the cart | Order with no items is placed and confirmed | Medium | Medium | `app.js` `checkoutPage`; `server.py` `Store.checkout` |
| BUG-29 | Cart is not emptied after ordering | Place an order → open the cart | Empty cart | The ordered items are still there | Medium | Medium | `server.py` `Store.checkout` |

### Track order (`/track`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-30 | The order number as shown is not found | Enter `LG-10042` exactly as on the confirmation (and the placeholder) + email | The order | "We couldn't find an order…" (only `10042` works) | High | Medium | `server.py` `Store.track` |
| BUG-31 | Order date is a month early | Track an order placed today (28 Oct 2026) | 28/10/2026 | 28/9/2026 (confirmation page says October 28, 2026) | Low | Hard | `app.js` `trackPage` (`getMonth()` is 0-based) |

### Accounts (`/login`, `/register`, `/account`)

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-32 | Password confirmation is not checked | Register with password `abc12345`, confirm `zzzzzzzz` | "Passwords don't match" | Account created | Medium | Medium | `app.js` `registerPage`; `server.py` `Store.register` |
| BUG-33 | 7-character passwords are accepted | Register with `abc1234` (hint: at least 8 characters) | Refused | Account created (6 characters are refused) | Low | Medium | `app.js` `registerPage`; `server.py` `Store.register` |
| BUG-34 | Logging in empties the cart | Add items as a guest → log in as the demo account | Cart kept | Cart empty (badge 0) | High | Hard | `server.py` `Store.login` |
| BUG-35 | Profile name is not saved | Account → change Full name → **Save changes** → reload | New name | "Profile updated." but the old name comes back | Medium | Medium | `server.py` `Store.update_profile` (reads `full_name`, page sends `name`) |
| BUG-36 | Order history is always empty | Log in → place an order → Account | The order listed | "You haven't placed any orders yet." | Medium | Hard | `server.py` `Store.account_orders` (user id compared with email) |
| BUG-37 | Log out does not log out | Account → **Log out** → open `/account` | Logged out, `/account` sends you to login | Header still says "Hi, …" and `/account` still opens | Critical | Medium | `app.js` `accountPage` (posts to `/api/logout`, which is a 404) |

### Contact and FAQ

| ID | Bug | Steps to reproduce | Expected | Actual | Severity | Difficulty | Where |
|---|---|---|---|---|---|---|---|
| BUG-38 | Messages over 200 characters fail | Valid name and email, a 250-character message (counter says 250 / 500) → **Send message** | Sent | "Something went wrong on our side" (HTTP 500) | Medium | Medium | `server.py` `Store.contact` (`MESSAGE_COLUMN`) |
| BUG-39 | FAQ opens the wrong answer | Click "How long does shipping take?" | Its answer opens | The next question's answer opens; the last question opens nothing | Low | Easy | `app.js` `faqPage` |

## What is not a planted bug

- The console errors that come with a bug: 404 from `/returns` (BUG-01) and `/api/logout` (BUG-37), 500 from
  `/api/contact` (BUG-38), and 404 from `/api/track` when no order matches (the normal "not found" answer).
- "Demo store for QA testing" in the footer, the demo account on the login page, and payments being cash on
  delivery or bank transfer only (no card form, on purpose).
- Anything else the scanner reports is either a false positive or an unplanned bug: worth a look either way.

By area: home and global 4, shop 6, product 5, deals 2, cart 6, checkout 6, tracking 2, accounts 6, contact and FAQ 2.
By difficulty: Easy 7, Medium 22, Hard 10. By severity: Critical 1, High 11, Medium 17, Low 10.
