# The café's menu on the website as text (it was only a PDF, which people can't open on their phones), where
# visitors find it from the front page; then (the owner's follow-up) the flat white at its new price.

# The menu's items, by words that pick each out, and their prices in the PDF. The flat white is checked on its own.
ITEMS = {'espresso': '2.40', 'americano': '2.90', 'cappuccino': '3.30', 'latte': '3.50', 'mocha': '3.70',
         'pot of tea': '2.60', 'hot chocolate': '3.50', 'bacon roll': '4.50', 'sausage sandwich': '4.80',
         'avocado': '7.50', 'porridge': '4.90', 'full corner': '9.50', 'soup': '6.20', 'cheese toastie': '5.80',
         'ham and mustard': '6.40', 'scone': '3.80', 'slice of cake': '3.60'}
ALLOW = {'changed': ['home']}


def links(markup):
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0]
            for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


def price_after(t, words):
    """The first price after an item's name (within the same line of a menu), or None."""
    i = t.find(words)
    if i < 0:
        return None
    m = re.search(r'£?\s?(\d+[.:]\d{2})', t[i + len(words):i + len(words) + 80])
    return m.group(1).replace(':', '.') if m else None


@cache
def menu_page():
    """The page with the menu as text: the front page, or a page on the site linked from it (in its content,
    menu or footer). (address, text) of the one with most of the menu, or None."""
    s, body = get('/')
    if s != 200:
        return None
    host = urllib.parse.urlparse(SITE).netloc
    found = []
    for url in dict.fromkeys(['/'] + [u for u in links(body) if urllib.parse.urlparse(u).netloc == host]):
        if re.search(r'\.(pdf|jpe?g|png)$', url, flags=re.I):
            continue
        s, b = (200, body) if url == '/' else get(url)
        if s == 200:
            t = text(main_content(b))
            found.append((sum(1 for w in ITEMS if w in t), url, t))
    best = max(found, default=None)
    return (best[1], best[2]) if best and best[0] else None


def check_menu():
    found = menu_page()
    if not found:
        return False, 'There’s no menu as text on the front page or a page it links to.'
    _, t = found
    wrong = [w for w, price in ITEMS.items() if price_after(t, w) != price]
    if not wrong:
        return True, ''
    return False, f'{len(ITEMS) - len(wrong)} of {len(ITEMS)} menu items are there with their prices; not: ' + ', '.join(wrong) + '.'


def check_flat_white():
    found = menu_page()
    if not found:
        return False, 'No menu page to look at.'
    price = price_after(found[1], 'flat white')
    return price == '3.40', ('' if price == '3.40' else f'The flat white is shown at {"£" + price if price else "no price"}, not £3.40.')


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'flat_white'}

CHECKS = [('menu', 'The menu is on the site as text, with its prices, linked from the front page', check_menu),
          ('flat_white', 'The flat white is £3.40 (the follow-up)', check_flat_white)]
