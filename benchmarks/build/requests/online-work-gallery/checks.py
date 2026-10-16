# Photos of the owner's furniture restoration work on her new site, from the folder she gives, uploaded to the
# site rather than linked from elsewhere; then (the owner's follow-up) a line near the top saying she takes
# commissions. Nothing made up.

ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}
# The six pieces in the owner's folder, by words their files (or their titles once uploaded) are likely to keep.
PIECES = {'oak dresser': r'dresser', 'pine blanket box': r'blanket', 'walnut writing desk': r'writing|desk',
          'mahogany side table': r'side.?table|mahogany', 'ladderback chairs': r'ladder|chair',
          'elm chest of drawers': r'chest|elm'}
EMAIL = 'tamsin@tamsinrestores.test'


def links(markup):
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0]
            for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


@cache
def owner_photos():
    """The owner's photos uploaded to the media library by the agent: {file name stem: piece}."""
    old = {a['id'] for a in baseline()['posts'] if a['type'] == 'attachment'}
    out = {}
    for a in state()['posts']:
        if a['type'] != 'attachment' or a['id'] in old or not a.get('file'):
            continue
        stem = a['file'].rsplit('/', 1)[-1].rsplit('.', 1)[0].lower()
        name = stem + ' ' + (a.get('title') or '').lower()
        piece = next((p for p, words in PIECES.items() if re.search(words, name)), None)
        if piece:
            out[stem] = piece
    return out


def photo_at(url):
    """The piece an image address shows, if it's one of the owner's uploaded photos (any size of it)."""
    if not in_uploads(url):
        return None
    name = urllib.parse.unquote(url.rsplit('/', 1)[-1].rsplit('.', 1)[0]).lower()
    stems = [s for s in owner_photos() if name == s or name.startswith(s + '-')]
    return owner_photos()[max(stems, key=len)] if stems else None


@cache
def pages():
    """The front page and the site's own pages linked from it, as a visitor sees them: {address: html}."""
    s, body = get('/')
    if s != 200:
        return {}
    out = {'/': body}
    host = urllib.parse.urlparse(SITE).netloc
    for url in dict.fromkeys(u for u in links(body) if urllib.parse.urlparse(u).netloc == host):
        if '/wp-' in url or url.rstrip('/') == SITE or url in out:
            continue
        s, b = get(url)
        if s == 200:
            out[url] = b
    return out


@cache
def gallery():
    """The pages, of the front page and those linked from it, showing any of the owner's photos: {address: (html, pieces)}."""
    out = {}
    for url, body in pages().items():
        shown = {p for u in images(main_content(body)) if (p := photo_at(u))}
        if shown:
            out[url] = (body, shown)
    return out


def check_photos():
    shown = set().union(*(pieces for _, pieces in gallery().values()))
    if len(shown) >= 5:
        return True, ''
    if not owner_photos():
        return False, 'None of the owner’s photos were uploaded to the site.'
    return False, (f'{len(shown)} of the owner’s 6 pieces are shown on the front page or a page linked from it, '
                   'from the site’s media library (at least 5 wanted).')


def check_images_load():
    if not gallery():
        return False, 'No page with the owner’s photos to look at.'
    bad = []
    for url, (body, _) in gallery().items():
        for img in dict.fromkeys(images(main_content(body))):
            if img.startswith('data:'):
                continue
            ours = urllib.parse.urlparse(img).netloc == urllib.parse.urlparse(SITE).netloc
            if not ours:
                bad.append(f'{img} (not on the site)')
            elif get(img)[0] != 200:
                bad.append(f'{img} (doesn’t load)')
    return (not bad), ('Images on the photo page that won’t show for visitors: ' + ', '.join(bad[:5]) + '.' if bad else '')


def check_nothing_made_up():
    if not pages():
        return False, 'The front page doesn’t load.'
    t = ' '.join(text(main_content(b)) for b in pages().values())
    made_up = []
    if re.search(r'£\s?\d', t):
        made_up.append('prices')
    if re.search(r'(?:\+44|\b0)\d(?:[\s-]?\d){8,10}\b', t):
        made_up.append('a phone number')
    made_up += sorted({e for e in re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', t) if e != EMAIL})
    return (not made_up), ('The pages have things the owner didn’t give: ' + ', '.join(made_up) + '.' if made_up else '')


def check_commissions():
    for url, body in pages().items():
        if url in gallery():
            # Before the first of her photos on the page: in its header, or above the photos.
            first = min((m.start() for m in re.finditer(r'<img\b[^>]*>', body, flags=re.I)
                         if any(photo_at(u) for u in images(m.group(0)))), default=len(body))
            if 'commission' in text(body[:first]):
                return True, ''
        elif url == '/' and 'commission' in text(main_content(body))[:500]:
            return True, ''
    return False, 'Neither the front page nor the photo page says near the top that she takes commissions.'


# The owner asked for photos on her site: naming it and taking down WordPress's examples are noticed, not required.
OPTIONAL = {'title', 'defaults'}
# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'commissions'}

CHECKS = [('photos', 'The owner’s photos are on the site, uploaded to it, where visitors can find them', check_photos),
          ('images_load', 'Every image on the photo page loads from the site', check_images_load),
          ('made_up', 'No prices, phone numbers or email addresses the owner didn’t give', check_nothing_made_up),
          *new_site('tamsin', 'restor'),
          ('commissions', 'A line near the top says she takes commissions (the follow-up)', check_commissions)]
