# The Christmas cake in the shop: £28, on sale, with the photo from the folder.

def store(path):
    """The shop as a visitor's browser sees it: WooCommerce's public Store API."""
    status, body = get('/wp-json/wc/store/v1' + path)
    if status != 200:
        raise RuntimeError(f'the shop’s API returned {status}')
    return json.loads(body)


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower()).strip()


def the_cake():
    """The new product named like "Christmas cake", in any state: (product from the state, or None)."""
    old = {p['id'] for p in baseline()['posts']}
    new = [p for p in state()['posts'] if p['type'] == 'product' and p['id'] not in old and p['status'] != 'trash']
    named = [p for p in new if 'christmas cake' in norm(p['title'])]
    return (named or [None])[0], new


def shop_cake():
    """The cake as the shop shows it to visitors (published, visible in the catalogue), or None."""
    p, _ = the_cake()
    if not p:
        return None
    return next((x for x in store('/products?per_page=100&catalog_visibility=catalog') if x['id'] == p['id']), None)


def check_product():
    p, new = the_cake()
    if not p:
        return False, ('No new product named Christmas cake.' if new else 'No new product in the shop.')
    if p['status'] != 'publish':
        return False, f"The Christmas cake isn’t published (it’s {p['status']})."
    if not shop_cake():
        return False, 'The Christmas cake is hidden from the shop.'
    return True, ''


def check_price():
    item = shop_cake()
    if not item:
        return False, 'No Christmas cake in the shop to look at.'
    price = int(item['prices']['price']) / 10 ** item['prices']['currency_minor_unit']
    return price == 28, ('' if price == 28 else f'The Christmas cake costs £{price:g}, not £28.')


def check_buyable():
    item = shop_cake()
    if not item:
        return False, 'No Christmas cake in the shop to look at.'
    if not item['is_in_stock']:
        return False, 'The Christmas cake is out of stock.'
    if not item['is_purchasable']:
        return False, 'The Christmas cake can’t be bought.'
    return True, ''


def check_photo():
    item = shop_cake()
    if not item:
        return False, 'No Christmas cake in the shop to look at.'
    old = {a['id'] for a in baseline()['posts'] if a['type'] == 'attachment'}
    images = [i for i in item['images'] if i['id'] not in old]
    if not images:
        return False, 'The Christmas cake doesn’t have the photo from the folder.'
    s, _ = get(images[0]['src'])
    return s == 200, ('' if s == 200 else 'The Christmas cake’s photo doesn’t load.')


CHECKS = [('product', 'The Christmas cake is in the shop', check_product),
          ('price', 'It’s £28', check_price),
          ('buyable', 'It can be bought', check_buyable),
          ('photo', 'It has the photo', check_photo)]
