# The site back up after a broken plugin update: every page loads, the menu shows, the shop works. Turning the
# broken specials plugin off is fine (the specials may go missing from the menu page until it's fixed): getting
# the site back is what matters.
ALLOW = {'deactivated': {'sunnyside-specials/sunnyside-specials.php'}}


def loads(path):
    """(loaded, status, visible text) of a page by its address."""
    s, body = get(path)
    t = text(body)
    return s == 200 and CRITICAL not in t, s, t


def check_pages():
    ok, s, _ = loads('/')
    if not ok:
        return False, f'The front page still shows an error ({s}).'
    broken = []
    for p in find(baseline(), 'page'):
        s, t = visit(p)
        if s != 200 or CRITICAL in t:
            broken.append(f"“{p['title']}” ({s})")
    return (not broken), ('Still showing an error: ' + ', '.join(broken) + '.' if broken else '')


def check_menu():
    ok, s, t = loads('/menu/')
    if not ok:
        return False, f'The menu page doesn’t load ({s}).'
    missing = [w for w in ('sourdough loaf', 'cinnamon bun', 'almond croissant') if w not in t]
    return (not missing), ('The menu page is missing: ' + ', '.join(missing) + '.' if missing else '')


def check_shop():
    ok, s, t = loads('/shop/')
    if not ok:
        return False, f'The shop doesn’t load ({s}).'
    missing = [w for w in ('victoria sponge', 'chocolate celebration cake') if w not in t]
    if missing:
        return False, 'The shop doesn’t list: ' + ', '.join(missing) + '.'
    s, body = get('/wp-json/wc/store/v1/products?per_page=100')
    if s != 200:
        return False, f'The shop can’t take orders: its API returns {s}.'
    return True, ''


CHECKS = [('pages', 'The front page and every page load again', check_pages),
          ('menu', 'The menu page shows the menu', check_menu),
          ('shop', 'The shop works', check_shop)]
