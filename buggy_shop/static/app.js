(function () {
  'use strict';

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const money = (n) => '$' + Number(n).toFixed(2);
  const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ENTITIES[c]);
  const params = new URLSearchParams(location.search);

  async function api(path, body) {
    const opts = body === undefined
      ? { credentials: 'same-origin' }
      : {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        };
    const res = await fetch(path, opts);
    let data = {};
    try {
      data = await res.json();
    } catch (e) {
      data = {};
    }
    return { ok: res.ok, status: res.status, data };
  }

  function say(el, text, kind) {
    el.textContent = text;
    el.classList.toggle('error', kind === 'error');
    el.classList.toggle('success', kind === 'success');
  }

  function stars(rating) {
    const full = Math.round(rating);
    return '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
  }

  function productCard(p) {
    return `<article class="card product-card">
      <a href="/product?id=${p.id}" tabindex="-1" aria-hidden="true"><img src="${p.image}" alt="" width="320" height="240" loading="lazy"></a>
      <h3><a href="/product?id=${p.id}">${esc(p.name)}</a></h3>
      <p class="muted small">${esc(p.category)}</p>
      <p class="rating small"><span aria-hidden="true">${stars(p.rating)}</span> ${p.rating.toFixed(1)} (${p.review_count})</p>
      <p class="price">${money(p.price)}</p>
      ${p.stock === 0 ? '<p class="stock out small">Out of stock</p>' : ''}
    </article>`;
  }

  function totalsList(rows) {
    return rows.map(([label, value, cls]) => `<div class="${cls || ''}"><dt>${label}</dt><dd>${value}</dd></div>`).join('');
  }

  // Home

  async function homePage() {
    const { data } = await api('/api/products');
    const featured = [1, 5, 13, 16].map((id) => data.products.find((p) => p.id === id));
    $('#featured').innerHTML = featured.map(productCard).join('');

    $('#newsletter-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = $('#newsletter-email').value.trim();
      const msg = $('#newsletter-msg');
      const r = await api('/api/newsletter', { email });
      if (r.ok) {
        say(msg, r.data.message, 'success');
        $('#newsletter-email').value = '';
      } else {
        say(msg, r.data.error || 'Something went wrong. Please try again.', 'error');
      }
    });
  }

  // Shop

  async function shopPage() {
    const PAGE_SIZE = 6;
    const { data } = await api('/api/products');
    const products = data.products;
    const q = $('#q');
    const category = $('#category');
    const sort = $('#sort');
    const inStock = $('#in-stock');
    const grid = $('#product-grid');
    const pager = $('#pagination');
    let page = 1;

    $('#result-count').textContent = `Showing ${products.length} products`;

    const byPrice = (a, b) => String(a.price).localeCompare(String(b.price));

    function filtered() {
      let list = products.slice();
      const term = q.value.trim();
      if (term) {
        list = list.filter((p) => p.name.includes(term));
      } else if (category.value !== 'all') {
        list = list.filter((p) => p.category === category.value);
      }
      if (inStock.checked) list = list.filter((p) => p.stock === 0);
      if (sort.value === 'price-asc') list.sort(byPrice);
      else if (sort.value === 'price-desc') list.sort((a, b) => byPrice(b, a));
      else if (sort.value === 'name') list.sort((a, b) => a.name.localeCompare(b.name));
      return list;
    }

    function render() {
      const list = filtered();
      const pages = Math.max(1, Math.floor(list.length / PAGE_SIZE));
      page = Math.min(page, pages);
      const shown = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
      grid.innerHTML = shown.length ? shown.map(productCard).join('') : '<p>No products match your search.</p>';
      let buttons = `<button type="button" data-page="${page - 1}" ${page === 1 ? 'disabled' : ''}>Previous</button>`;
      for (let i = 1; i <= pages; i++) {
        buttons += `<button type="button" data-page="${i}" ${i === page ? 'aria-current="page" class="current"' : ''}>${i}</button>`;
      }
      buttons += `<button type="button" data-page="${page + 1}" ${page === pages ? 'disabled' : ''}>Next</button>`;
      pager.innerHTML = buttons;
    }

    pager.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-page]');
      if (!btn || btn.disabled) return;
      page = Number(btn.dataset.page);
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    q.addEventListener('input', () => { page = 1; render(); });
    [category, sort, inStock].forEach((el) => el.addEventListener('change', () => { page = 1; render(); }));
    render();
  }

  // Product

  async function productPage() {
    const id = Number(params.get('id'));
    const res = await api(`/api/products/${id}`);
    if (!res.ok) {
      $('#product-missing').hidden = false;
      return;
    }
    const p = res.data.product;
    document.title = `${p.name} · Lumen Goods`;
    $('#p-image').src = p.image;
    $('#p-image').alt = p.name;
    $('#p-category').textContent = p.category;
    $('#p-name').textContent = p.name;
    $('#p-price').textContent = money(p.price);
    $('#p-description').textContent = p.description;
    const out = p.stock === 0;
    const stock = $('#p-stock');
    stock.textContent = out ? 'Out of stock' : p.stock < 10 ? `Only ${p.stock} left in stock` : 'In stock';
    stock.classList.toggle('out', out);
    const add = $('#add-to-cart');
    add.textContent = out ? 'Out of stock' : 'Add to cart';
    add.classList.toggle('btn-disabled', out);

    function showRating(product) {
      $('#p-rating').innerHTML = `<span aria-hidden="true">${stars(product.rating)}</span> ${product.rating.toFixed(1)} out of 5 · ${product.review_count} reviews`;
    }
    showRating(p);

    const qty = $('#qty');
    $('#qty-minus').addEventListener('click', () => { qty.value = Number(qty.value) - 1; });
    $('#qty-plus').addEventListener('click', () => { qty.value = Number(qty.value) + 1; });
    add.addEventListener('click', async () => {
      const n = Number(qty.value);
      const r = await api('/api/cart/items', { product_id: p.id, qty: n });
      const msg = $('#add-msg');
      if (r.ok) {
        msg.innerHTML = `Added ${n} × ${esc(p.name)} to your cart. <a href="/cart">View cart</a>`;
        msg.className = 'msg success';
      } else {
        say(msg, r.data.error || 'Could not add to cart.', 'error');
      }
    });

    function renderReviews(reviews) {
      $('#review-list').innerHTML = reviews.length
        ? reviews.map((r) => `<li class="review">
            <p class="rating"><span aria-hidden="true">${stars(r.rating)}</span> <span class="sr-only">${r.rating} out of 5</span></p>
            <p>${esc(r.text)}</p>
            <p class="muted small">— ${esc(r.name)}</p>
          </li>`).join('')
        : '<li>No reviews yet.</li>';
    }
    renderReviews(res.data.reviews);
    $('#reviews').hidden = false;

    $('#review-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = $('#review-msg');
      const text = $('#review-text').value.trim();
      if (text && text.length < 10) {
        say(msg, 'Reviews need at least 10 characters.', 'error');
        return;
      }
      const r = await api(`/api/products/${p.id}/reviews`, {
        name: $('#review-name').value.trim(),
        rating: Number($('#review-rating').value),
        text,
      });
      if (!r.ok) {
        say(msg, r.data.error || 'Could not post your review.', 'error');
        return;
      }
      renderReviews(r.data.reviews);
      showRating(r.data.product);
      $('#review-form').reset();
      say(msg, 'Thanks! Your review has been posted.', 'success');
    });

    const all = (await api('/api/products')).data.products;
    const related = all.filter((x) => x.category === p.category && x.id !== p.id).slice(0, 4);
    $('#related-grid').innerHTML = related.map((r, i) => `<article class="card product-card">
        <img src="${r.image}" alt="" width="320" height="240" loading="lazy">
        <h3><a href="/product?id=${i + 1}">${esc(r.name)}</a></h3>
        <p class="price">${money(r.price)}</p>
      </article>`).join('');
    $('#related').hidden = related.length === 0;
    $('#product').hidden = false;
  }

  // Deals

  async function dealsPage() {
    const { data } = await api('/api/deals');
    const started = Date.now();
    $('#deals').innerHTML = data.deals.map((d) => `<article class="card product-card deal">
        <a href="/product?id=${d.product_id}" tabindex="-1" aria-hidden="true"><img src="${d.image}" alt="" width="320" height="240" loading="lazy"></a>
        <p class="tag">−${d.percent_off}%</p>
        <h3><a href="/product?id=${d.product_id}">${esc(d.name)}</a></h3>
        <p class="price"><s class="muted">${money(d.price)}</s> <strong>${money(d.deal_price)}</strong></p>
        <p class="small">Ends in <span class="timer" data-left="${d.seconds_left}">--:--:--</span></p>
        <button type="button" class="btn btn-block" data-id="${d.product_id}" data-name="${esc(d.name)}">Add to cart</button>
      </article>`).join('');

    const pad = (n) => String(n).padStart(2, '0');
    function tick() {
      const elapsed = Math.floor((Date.now() - started) / 1000);
      $$('.timer').forEach((el) => {
        const left = Number(el.dataset.left) + elapsed;
        el.textContent = `${pad(Math.floor(left / 3600))}:${pad(Math.floor((left % 3600) / 60))}:${pad(left % 60)}`;
      });
    }
    tick();
    setInterval(tick, 1000);

    $('#deals').addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-id]');
      if (!btn) return;
      const r = await api('/api/cart/items', { product_id: Number(btn.dataset.id), qty: 1 });
      const msg = $('#deal-msg');
      if (r.ok) {
        msg.innerHTML = `Added ${esc(btn.dataset.name)} to your cart. <a href="/cart">View cart</a>`;
        msg.className = 'msg success';
      } else {
        say(msg, r.data.error || 'Could not add to cart.', 'error');
      }
    });
  }

  // Cart

  async function cartPage() {
    const rows = $('#cart-rows');
    const { data } = await api('/api/cart');

    function renderSummary(cart) {
      const lines = [['Subtotal', money(cart.subtotal)]];
      if (cart.discount) lines.push([`Discount (${esc(cart.coupons.join(', '))})`, '−' + money(cart.discount), 'discount']);
      lines.push(['Shipping', cart.shipping ? money(cart.shipping) : 'Free']);
      lines.push(['Tax (8%)', '$' + cart.tax]);
      lines.push(['Total', money(cart.total), 'grand']);
      $('#cart-summary').innerHTML = totalsList(lines);
    }

    function render(cart) {
      const empty = cart.items.length === 0;
      $('#cart-empty').hidden = !empty;
      $('#cart').hidden = empty;
      rows.innerHTML = cart.items.map((i) => `<div class="cart-row" data-id="${i.product_id}">
          <div class="cart-product"><img src="${i.image}" alt="" width="64" height="48"><a href="/product?id=${i.product_id}">${esc(i.name)}</a></div>
          <div><span class="label">Price</span>${money(i.price)}</div>
          <div><span class="label">Quantity</span><input class="row-qty" type="number" min="1" value="${i.qty}" aria-label="Quantity of ${esc(i.name)}"></div>
          <div><span class="label">Total</span><span class="line-total">${money(i.line_total)}</span></div>
          <div><button type="button" class="link remove">Remove</button></div>
        </div>`).join('');
      renderSummary(cart);
    }

    rows.addEventListener('change', async (e) => {
      if (!e.target.classList.contains('row-qty')) return;
      const row = e.target.closest('.cart-row');
      const id = Number(row.dataset.id);
      const r = await api('/api/cart/update', { product_id: id, qty: Number(e.target.value) });
      if (!r.ok) {
        say($('#cart-msg'), r.data.error || 'Could not update the quantity.', 'error');
        return;
      }
      say($('#cart-msg'), '');
      const item = r.data.cart.items.find((i) => i.product_id === id);
      row.querySelector('.line-total').textContent = money(item.line_total);
    });

    rows.addEventListener('click', async (e) => {
      if (!e.target.classList.contains('remove')) return;
      const row = rows.querySelector('.cart-row');
      const r = await api('/api/cart/remove', { product_id: Number(row.dataset.id) });
      if (r.ok) render(r.data.cart);
    });

    $('#coupon-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const code = $('#coupon').value.trim();
      const msg = $('#coupon-msg');
      if (!code) {
        say(msg, 'Enter a coupon code.', 'error');
        return;
      }
      const r = await api('/api/cart/coupon', { code });
      if (r.ok) say(msg, 'Coupon applied!', 'success');
      else say(msg, r.data.error || 'Could not apply the coupon.', 'error');
      if (r.data.cart) render(r.data.cart);
    });

    render(data.cart);
  }

  // Checkout

  async function checkoutPage() {
    const [{ data }, me] = await Promise.all([api('/api/cart'), api('/api/me')]);
    const cart = data.cart;
    const form = $('#checkout-form');
    if (me.data.user) {
      $('#f-name').value = me.data.user.name;
      $('#f-email').value = me.data.user.email;
    }

    $('#checkout-items').innerHTML = cart.items.length
      ? cart.items.map((i) => `<li><span>${i.qty} × ${esc(i.name)}</span><span>${money(i.line_total)}</span></li>`).join('')
      : '<li>Your cart is empty.</li>';

    function renderSummary() {
      const method = $('input[name="shipping"]:checked').value;
      const shipping = method === 'express' ? 15 : cart.shipping;
      const total = cart.subtotal + shipping + cart.tax;
      $('#checkout-summary').innerHTML = totalsList([
        ['Subtotal', money(cart.subtotal)],
        [`Shipping (${method === 'express' ? 'Express' : 'Standard'})`, shipping ? money(shipping) : 'Free'],
        ['Tax (8%)', money(cart.tax)],
        ['Total', money(total), 'grand'],
      ]);
    }
    $$('input[name="shipping"]').forEach((r) => r.addEventListener('change', renderSummary));
    renderSummary();

    function validate(values) {
      const errors = {};
      ['name', 'email', 'phone', 'address', 'city', 'zip'].forEach((k) => {
        if (!values[k]) errors[k] = 'This field is required.';
      });
      if (values.phone && !/^[0-9+()\-\s]{7,20}$/.test(values.phone)) errors.phone = 'Enter a valid phone number.';
      const zip = Number(values.zip);
      if (values.zip && (!Number.isInteger(zip) || zip < 10000 || zip > 99999)) {
        errors.zip = 'Enter a valid 5-digit ZIP code.';
      }
      return errors;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const values = {};
      ['name', 'email', 'phone', 'address', 'city', 'zip'].forEach((k) => { values[k] = form.elements[k].value.trim(); });
      const errors = validate(values);
      Object.keys(values).forEach((k) => { $(`#e-${k}`).textContent = errors[k] || ''; });
      const first = Object.keys(errors)[0];
      if (first) {
        form.elements[first].focus();
        say($('#checkout-msg'), 'Please fix the highlighted fields.', 'error');
        return;
      }
      say($('#checkout-msg'), '');
      const btn = $('#place-order');
      btn.disabled = true;
      const r = await api('/api/checkout', {
        ...values,
        country: form.elements.country.value,
        shipping: $('input[name="shipping"]:checked').value,
        payment: $('input[name="payment"]:checked').value,
      });
      btn.disabled = false;
      if (r.ok) location.href = `/order-confirmation?id=${r.data.order.id}`;
      else say($('#checkout-msg'), r.data.error || 'Could not place your order.', 'error');
    });
  }

  function orderTotals(o) {
    const lines = [['Subtotal', money(o.subtotal)]];
    if (o.discount) lines.push([`Discount (${esc(o.coupons.join(', '))})`, '−' + money(o.discount), 'discount']);
    const method = o.shipping_method === 'express' ? 'Express' : 'Standard';
    lines.push([`Shipping (${method})`, o.shipping ? money(o.shipping) : 'Free']);
    lines.push(['Tax', money(o.tax)]);
    lines.push(['Total', money(o.total), 'grand']);
    return totalsList(lines);
  }

  async function confirmationPage() {
    const r = await api(`/api/orders/${Number(params.get('id'))}`);
    if (!r.ok) {
      $('#confirm-missing').hidden = false;
      return;
    }
    const o = r.data.order;
    $('#o-number').textContent = `LG-${o.id}`;
    $('#o-date').textContent = new Date(o.created * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    $('#o-email').textContent = o.email;
    $('#o-items').innerHTML = o.items.map((i) => `<li><span>${i.qty} × ${esc(i.name)}</span><span>${money(i.line_total)}</span></li>`).join('');
    $('#o-summary').innerHTML = orderTotals(o);
    $('#confirm').hidden = false;
  }

  // Order tracking

  function trackPage() {
    $('#track-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const order = $('#t-order').value.trim();
      const email = $('#t-email').value.trim();
      const msg = $('#track-msg');
      const result = $('#track-result');
      result.hidden = true;
      if (!order || !email) {
        say(msg, 'Enter your order number and email address.', 'error');
        return;
      }
      const r = await api('/api/track', { order, email });
      if (!r.ok) {
        say(msg, r.data.error || 'Could not find that order.', 'error');
        return;
      }
      say(msg, '');
      const o = r.data.order;
      const d = new Date(o.created * 1000);
      const items = o.items.reduce((n, i) => n + i.qty, 0);
      result.innerHTML = `<h2>Order LG-${o.id}</h2>
        <dl class="totals">
          <div><dt>Status</dt><dd>${esc(o.status)}</dd></div>
          <div><dt>Placed on</dt><dd>${d.getDate()}/${d.getMonth()}/${d.getFullYear()}</dd></div>
          <div><dt>Items</dt><dd>${items}</dd></div>
          <div><dt>Shipping</dt><dd>${o.shipping_method === 'express' ? 'Express' : 'Standard'}</dd></div>
          <div class="grand"><dt>Total</dt><dd>${money(o.total)}</dd></div>
        </dl>`;
      result.hidden = false;
    });
  }

  // Accounts

  function loginPage() {
    $('#login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = $('#l-email').value.trim();
      const password = $('#l-password').value;
      const msg = $('#login-msg');
      if (!EMAIL.test(email)) return say(msg, 'Enter a valid email address.', 'error');
      if (!password) return say(msg, 'Enter your password.', 'error');
      const r = await api('/api/login', { email, password });
      if (!r.ok) return say(msg, r.data.error || 'Could not log you in.', 'error');
      const next = params.get('next') || '';
      location.href = next.startsWith('/') && !next.startsWith('//') ? next : '/account';
    });
  }

  function registerPage() {
    $('#register-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = $('#r-name').value.trim();
      const email = $('#r-email').value.trim();
      const password = $('#r-password').value;
      const confirm = $('#r-confirm').value;
      const msg = $('#register-msg');
      if (!name) return say(msg, 'Enter your name.', 'error');
      if (!EMAIL.test(email)) return say(msg, 'Enter a valid email address.', 'error');
      if (password.length < 7) return say(msg, 'Password must be at least 8 characters.', 'error');
      const r = await api('/api/register', { name, email, password, confirm });
      if (!r.ok) return say(msg, r.data.error || 'Could not create your account.', 'error');
      location.href = '/account';
    });
  }

  async function accountPage() {
    const me = await api('/api/me');
    if (!me.data.user) {
      location.href = '/login?next=/account';
      return;
    }
    $('#a-name').value = me.data.user.name;
    $('#a-email').value = me.data.user.email;

    $('#profile-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = $('#a-name').value.trim();
      const msg = $('#profile-msg');
      if (!name) return say(msg, 'Enter your name.', 'error');
      const r = await api('/api/profile', { name });
      if (r.ok) say(msg, 'Profile updated.', 'success');
      else say(msg, r.data.error || 'Could not save your profile.', 'error');
    });

    $('#logout').addEventListener('click', async () => {
      await api('/api/logout', {});
      location.href = '/login';
    });

    const r = await api('/api/account/orders');
    const orders = (r.data && r.data.orders) || [];
    $('#order-history').innerHTML = orders.length
      ? `<ul class="mini-items">${orders.map((o) => `<li><span>LG-${o.id} · ${esc(o.status)}</span><span>${money(o.total)}</span></li>`).join('')}</ul>`
      : '<p class="muted">You haven\'t placed any orders yet.</p>';
  }

  // Contact and FAQ

  function contactPage() {
    const text = $('#c-message');
    text.addEventListener('input', () => { $('#c-count').textContent = `${text.value.length} / 500 characters`; });
    $('#contact-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const body = {
        name: $('#c-name').value.trim(),
        email: $('#c-email').value.trim(),
        subject: $('#c-subject').value,
        message: text.value.trim(),
      };
      const msg = $('#contact-msg');
      if (!body.name) return say(msg, 'Enter your name.', 'error');
      if (!EMAIL.test(body.email)) return say(msg, 'Enter a valid email address.', 'error');
      if (!body.message) return say(msg, 'Enter a message.', 'error');
      const r = await api('/api/contact', body);
      if (r.ok) {
        say(msg, r.data.message, 'success');
        e.target.reset();
        $('#c-count').textContent = '0 / 500 characters';
      } else if (r.status >= 500) {
        say(msg, 'Something went wrong on our side. Please try again later.', 'error');
      } else {
        say(msg, r.data.error || 'Could not send your message.', 'error');
      }
    });
  }

  function faqPage() {
    const answers = $$('.faq-a');
    $$('.faq-q').forEach((btn, i) => {
      btn.addEventListener('click', () => {
        const answer = answers[i + 1];
        const open = btn.getAttribute('aria-expanded') !== 'true';
        btn.setAttribute('aria-expanded', String(open));
        if (answer) answer.hidden = !open;
      });
    });
  }

  const pages = {
    home: homePage,
    shop: shopPage,
    product: productPage,
    deals: dealsPage,
    cart: cartPage,
    checkout: checkoutPage,
    'order-confirmation': confirmationPage,
    track: trackPage,
    login: loginPage,
    register: registerPage,
    account: accountPage,
    contact: contactPage,
    faq: faqPage,
  };
  const run = pages[document.body.dataset.page];
  if (run) run();
})();
