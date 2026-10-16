# The B&B's Weebly site (www.penhallowbnb.test) moved onto WordPress: every page, with its text and the rooms'
# prices exactly as they were, as content that can be edited, the room photos in the site's media library, and
# every page reachable from the site's navigation; then (the owner's follow-up) the rooms page in the menu.
# The old contact form needn't be rebuilt: the contact page's phone number and email are a way to get in touch.

OLD = 'www.penhallowbnb.test'
PAGES = {'Home': ['sea captain', 'mousehole harbour', 'three double rooms', 'kerensa and mike'],
         'Rooms': ['harbour room', 'garden room', 'attic room', '£110', '£95', '£85', 'including breakfast'],
         'Breakfast': ['8 till 9.30', 'newlyn', "hog's pudding", 'vegetarian breakfast', 'granola'],
         'Find us': ['duck street', 'tr19 6qa', 'penzance station', 'parking'],
         'Contact': ['01736 731204', 'stay@penhallowbnb.test']}
# Each room, and its price a night on the old site; the owner says they're still right.
ROOMS = {'harbour room': '110', 'garden room': '95', 'attic room': '85'}
# Every price on the old site (single occupancy is £10 less).
OLD_PRICES = {'110', '95', '85', '10'}
ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}


@cache
def moved():
    return {name: best_match(words) for name, words in PAGES.items()}


def links(markup):
    """Every link's address in some markup, made absolute on the site."""
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0] for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


@cache
def page_url(id):
    try:
        return api(f"/wp/v2/pages/{id}")['link']
    except Exception:
        return None


def links_to(found, p):
    """Whether any of the links goes to a page (its address, or its ?page_id= one)."""
    want = {(urllib.parse.urlparse(u).path.rstrip('/'), urllib.parse.urlparse(u).query) for u in (page_url(p['id']) or '', f"{SITE}/?page_id={p['id']}") if u}
    host = urllib.parse.urlparse(SITE).netloc
    return any(urllib.parse.urlparse(u).netloc == host and (urllib.parse.urlparse(u).path.rstrip('/'), urllib.parse.urlparse(u).query) in want for u in found)


def price(t, room):
    """The room's price on a page: the first £ figure after its name, before the next room's name."""
    for m in re.finditer(re.escape(room), t):
        rest = t[m.end():m.end() + 400]
        cut = min([rest.find(r) for r in ROOMS if rest.find(r) >= 0] or [len(rest)])
        p = re.search(r'£(\d+)(?:\.00)?\b', rest[:cut])
        if p:
            return p.group(1)
    return None


def check_pages():
    missing = [f"{name} ({', '.join(m[2])})" for name, m in moved().items() if m[2]]
    return (not missing), ('Not moved, or missing text: ' + '; '.join(missing) + '.' if missing else '')


def check_front():
    s, body = get('/')
    t = text(main_content(body)) if s == 200 else ''
    missing = [w for w in PAGES['Home'] if w not in t]
    return (not missing), ('The front page isn’t the old home page.' if missing else '')


def check_prices():
    p, body, _ = moved()['Rooms']
    if not p:
        return False, 'No rooms page.'
    t = text(main_content(body))
    wrong = [f"{room} ({'£' + price(t, room) if price(t, room) else 'no price'})" for room, want in ROOMS.items() if price(t, room) != want]
    return (not wrong), ('Not at their old prices: ' + ', '.join(wrong) + '.' if wrong else '')


def check_no_made_up_prices():
    """No price on the site that wasn't on the old one."""
    made_up = {}
    for p in state()['posts']:
        if p['type'] in ('page', 'post') and p['status'] == 'publish':
            s, t = visit(p)
            for amount in re.findall(r'£(\d+(?:\.\d{2})?)', t):
                if re.sub(r'\.00$', '', amount) not in OLD_PRICES:
                    made_up.setdefault(p['title'], set()).add('£' + amount)
    return (not made_up), ('Prices that weren’t on the old site: ' + '; '.join(f"{k} ({', '.join(sorted(v))})" for k, v in made_up.items()) + '.' if made_up else '')


def check_editable():
    found = [m[0] for m in moved().values() if m[0] and not m[2]]
    if not found:
        return False, 'No moved pages to look at.'
    pasted = sorted({p['title'] for p in found if pasted_whole(raw_content(p))})
    return (not pasted), ('Pasted in as whole old web pages: ' + ', '.join(pasted) + '.' if pasted else '')


def check_photos():
    shown = set()
    for p, body, missing in moved().values():
        if p:
            shown |= set(images(main_content(body)))
    old = [u for u in shown if urllib.parse.urlparse(u).netloc == OLD]
    if old:
        return False, f'{len(old)} photo(s) are still loaded from the old site.'
    p, body, _ = moved()['Rooms']
    if not p:
        return False, 'No rooms page.'
    # The three room photos, under any name: the rooms page shows at least three from the media library.
    ours = {u.split('?')[0] for u in images(main_content(body)) if in_uploads(u)}
    return len(ours) >= 3, ('' if len(ours) >= 3 else f'The rooms page shows {len(ours)} of the 3 room photos from the site’s media library.')


def check_navigation():
    """Every moved page can be reached from the front page (its menu, or a link)."""
    s, body = get('/')
    if s != 200:
        return False, 'The front page doesn’t load.'
    found = links(body)
    unreachable = [name for name, (p, _, missing) in moved().items() if name != 'Home' and (not p or not links_to(found, p))]
    return (not unreachable), ('Not linked from the front page: ' + ', '.join(unreachable) + '.' if unreachable else '')


def check_rooms_in_menu():
    p, _, _ = moved()['Rooms']
    if not p:
        return False, 'No rooms page.'
    s, body = get('/')
    header = re.search(r'<header\b.*?</header>', body, flags=re.S | re.I)
    ok = bool(header) and links_to(links(header.group(0)), p)
    return ok, ('' if ok else 'The rooms page isn’t in the menu at the top of the site.')


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'rooms_menu'}
OPTIONAL = {'title', 'defaults'}  # the owner never asked to rename the site or remove WordPress's examples

CHECKS = [('pages', 'Every page of the old site is on the new one, with its text', check_pages),
          ('front', 'The front page is the old home page', check_front),
          ('prices', 'The rooms are at their old prices', check_prices),
          ('no_made_up_prices', 'No prices that weren’t on the old site', check_no_made_up_prices),
          ('editable', 'They’re pages that can be edited, not copies of the old web pages', check_editable),
          ('photos', 'The room photos are in the site’s media library', check_photos),
          ('navigation', 'Every page can be reached from the front page', check_navigation),
          *new_site('penhallow'),
          ('rooms_menu', 'The rooms page is in the menu (the follow-up)', check_rooms_in_menu)]
