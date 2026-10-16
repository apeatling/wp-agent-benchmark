# A simple website for a new dog grooming business, from the owner's notes and photos; then (the owner's
# follow-up) the prices on the front page.

ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}
PRICES = ['£35', '£42', '£50', '£25', '£20', '£8']


@cache
def published():
    """Every published page and post as a visitor sees it, and the front page: {address: (html, text)}."""
    out = {}
    s, body = get('/')
    if s == 200:
        out['/'] = (body, text(body))
    for p in state()['posts']:
        if p['type'] in ('page', 'post') and p['status'] == 'publish':
            q = 'page_id' if p['type'] == 'page' else 'p'
            s, body = get(f"/?{q}={p['id']}")
            if s == 200:
                out[f"/?{q}={p['id']}"] = (body, text(body))
    return out


def check_details():
    t = ' '.join(t for _, t in published().values())
    digits = re.sub(r'\D', '', t)
    missing = [what for what, ok in [
        ('the name', 'scruffs' in t), ('the phone number', '01632960412' in digits), ('the address', 'mill lane' in t),
        ('the opening days', bool(re.search(r'tue', t) and re.search(r'sat', t))),
        ('full grooms', 'full groom' in t), ('bath and brush', 'bath' in t), ('puppy grooms', 'puppy' in t),
        ('nail clips', 'nail' in t)] if not ok]
    return (not missing), ('The site doesn’t have ' + ', '.join(missing) + '.' if missing else '')


def check_photos():
    old = {a['file'] for a in baseline()['posts'] if a['type'] == 'attachment'}
    uploaded = [a['file'] for a in state()['posts'] if a['type'] == 'attachment' and a['file'] not in old]
    stems = {f.rsplit('/', 1)[-1].rsplit('.', 1)[0] for f in uploaded if f}
    pages = ' '.join(body for body, _ in published().values())
    shown = [s for s in stems if s and s in pages]
    if len(shown) >= 2:
        return True, ''
    return False, f'{len(shown)} of the owner’s photos are on the site’s pages, uploaded to it (at least 2 wanted).'


def check_prices():
    s, body = get('/')
    t = text(main_content(body)) if s == 200 else ''
    missing = [p for p in PRICES if not re.search(re.escape(p) + r'(?!\d)', t)]
    return (not missing), ('The front page doesn’t show ' + ', '.join(missing) + '.' if missing else '')


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'prices'}

CHECKS = [('details', 'The site has the business’s details and services', check_details),
          ('photos', 'The site shows the owner’s photos', check_photos),
          *new_site('scruffs'),
          ('prices', 'The front page shows the prices (the follow-up)', check_prices)]
