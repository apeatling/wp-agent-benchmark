# Visitors can buy the owner's candles online: each candle in the spreadsheet is in the shop at its price, in
# pounds, available, and goes in a basket. A WooCommerce request: what's checked is the shop WooCommerce makes.
# Taking payment isn't checked: the owner hasn't set anything up for it, and says to do whatever's easiest.

import http.cookiejar

CANDLES = {'Sea Salt and Driftwood': 18.00, 'Harbour Fig': 18.00, 'Wild Gorse': 16.50, 'Cornish Rain': 16.50,
           'Lavender and Sage': 14.00, 'Cedar and Smoke': 22.00, 'Orange Blossom': 14.00, 'Winter Spice': 20.00,
           'Fresh Linen': 12.50, 'Peppermint and Eucalyptus': 12.50}
META = ('_price', '_regular_price', '_sale_price', '_stock_status')


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower().replace('&', 'and')).strip()


@cache
def products():
    """{candle: product} for each candle with a published product named after it (its name in the title)."""
    found = {}
    for p in state(meta=META)['posts']:
        if p['type'] == 'product' and p['status'] == 'publish':
            for name in CANDLES:
                if norm(name) in norm(p['title']) and name not in found:
                    found[name] = p
    return found


def check_products():
    missing = [n for n in CANDLES if n not in products()]
    if not missing:
        return True, ''
    return False, f'{len(CANDLES) - len(missing)} of {len(CANDLES)} candles are in the shop; not: ' + ', '.join(missing) + '.'


def check_prices():
    wrong = []
    for name, price in CANDLES.items():
        p = products().get(name)
        meta = (p or {}).get('meta', {})
        try:
            ok = p and abs(float(meta.get('_price') or meta.get('_regular_price')) - price) < 0.005
        except (TypeError, ValueError):
            ok = False
        if p and not ok:
            wrong.append(f"{name} ({meta.get('_price') or 'no price'})")
    if not products():
        return False, 'No candles in the shop.'
    if str(state(options=['woocommerce_currency'])['options'].get('woocommerce_currency')) != 'GBP':
        return False, 'The shop doesn’t sell in pounds.'
    return (not wrong), ('Wrong prices: ' + ', '.join(wrong) + '.' if wrong else '')


def check_in_stock():
    out = [n for n, p in products().items() if p.get('meta', {}).get('_stock_status', 'instock') != 'instock']
    if not products():
        return False, 'No candles in the shop.'
    return (not out), ('Not available to buy: ' + ', '.join(out) + '.' if out else '')


def store(opener, path, body=None, headers=None):
    """A call to WooCommerce's shop API as a visitor (with their basket cookie): (status, headers, data)."""
    h = {'X-WPAB-Monitor': '1', 'Content-Type': 'application/json', **(headers or {})}
    req = urllib.request.Request(SITE + '/wp-json/wc/store/v1' + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers=h, method='POST' if body is not None else 'GET')
    try:
        with opener.open(req, timeout=60) as r:
            return r.status, r.headers, json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, e.headers, None


def check_basket():
    """A visitor sees a candle's page with its price, and can put it in their basket."""
    if not products():
        return False, 'No candles in the shop.'
    name, p = next(iter(products().items()))
    s, t = visit(p)
    if s != 200 or norm(name) not in norm(t) or f'£{CANDLES[name]:.2f}' not in t:
        return False, f'The {name} page doesn’t show it with its price in pounds ({s}).'
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    s, headers, _ = store(opener, '/cart')
    if s != 200:
        return False, f'The shop’s basket isn’t available ({s}).'
    s, _, cart = store(opener, '/cart/add-item', {'id': p['id'], 'quantity': 1},
                       {'Nonce': headers.get('Nonce', ''), 'Cart-Token': headers.get('Cart-Token', '')})
    if s not in (200, 201) or not cart or not cart.get('items'):
        return False, f'Adding {name} to the basket failed ({s}).'
    return True, ''


CHECKS = [('products', 'Every candle in the spreadsheet is in the shop', check_products),
          ('prices', 'At the spreadsheet’s prices, in pounds', check_prices),
          ('in_stock', 'Available to buy', check_in_stock),
          ('basket', 'A visitor can put one in their basket', check_basket, True)]
