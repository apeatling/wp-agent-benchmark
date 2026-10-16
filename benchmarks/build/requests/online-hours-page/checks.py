# A page with the shop's opening hours and how to find it, from what the owner says when asked; nothing made up.

ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}
# The opening times the owner gives, in minutes after midnight: 8:30 to 5:30, and 10 till 2 on Sundays.
TIMES = {8 * 60 + 30, 17 * 60 + 30, 10 * 60, 14 * 60}


def links(markup):
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0]
            for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


@cache
def hours_page():
    """The page with the opening hours: the front page, or a page on the site linked from it. (html, text) or None."""
    s, body = get('/')
    if s != 200:
        return None
    host = urllib.parse.urlparse(SITE).netloc
    for url in dict.fromkeys(['/'] + [u for u in links(body) if urllib.parse.urlparse(u).netloc == host]):
        s, b = (200, body) if url == '/' else get(url)
        t = text(main_content(b)) if s == 200 else ''
        if re.search(r'\bmon', t) and re.search(r'\bsun', t):
            return b, t
    return None


def times(t):
    """Every time of day in some text, in minutes after midnight. Times without am or pm before 8 are afternoon."""
    found = []
    for h, m, ampm in re.findall(r'\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)', t) + \
            [(h, m, '') for h, m in re.findall(r'\b(\d{1,2})[:.](\d{2})\b(?!\s*(?:am|pm|a\.m|p\.m))', t)]:
        h, m = int(h), int(m or 0)
        if ampm.startswith('p') and h < 12 or not ampm and h < 8:
            h += 12
        found.append(h * 60 + m)
    return found


def check_hours():
    found = hours_page()
    if not found:
        return False, 'No page with opening days on the front page or linked from it.'
    t = found[1]
    got = set(times(t))
    missing = [label for label, need in [('8:30', 8 * 60 + 30), ('5:30', 17 * 60 + 30)] if need not in got]
    # Sundays 10 till 2, however it's written: "10am - 2pm", "10:00-14:00", "10 till 2".
    if not re.search(r'\bsun[^.;]{0,40}?\b10(?:[:.]00)?\s*(?:am|a\.m\.)?\s*(?:-|to|till|until)\s*(?:2|14)(?:[:.]00)?(?!\d)', t):
        missing.append('10 till 2 on Sundays')
    if not (re.search(r'\bmon', t) and re.search(r'\bsat', t)):
        missing.insert(0, 'Monday to Saturday')
    return (not missing), ('The hours don’t show ' + ', '.join(missing) + '.' if missing else '')


def check_nothing_made_up():
    found = hours_page()
    if not found:
        return False, 'No page with opening hours to look at.'
    made_up = sorted({f'{m // 60}:{m % 60:02d}' for m in times(found[1]) if m not in TIMES})
    return (not made_up), ('The page has times the owner didn’t give: ' + ', '.join(made_up) + '.' if made_up else '')


def check_address():
    found = hours_page()
    if not found:
        return False, 'No page with opening hours to look at.'
    t = found[1]
    ok = 'quay road' in t and ('pw1 4qt' in t or '3 quay road' in t)
    return ok, ('' if ok else 'The page doesn’t give the shop’s address (3 Quay Road, Portwen PW1 4QT).')


def check_directions():
    found = hours_page()
    if not found:
        return False, 'No page with opening hours to look at.'
    markup, t = found
    # Directions or parking in words, a map, or a link to directions in a maps service.
    if ('back lane' in t or 'parking' in t or re.search(r'<iframe\b[^>]*(map|openstreetmap)', markup, flags=re.I)
            or re.search(r'href="[^"]*(google\.[a-z.]+/maps|maps\.google|maps\.apple|openstreetmap\.org|goo\.gl/maps)', markup, flags=re.I)):
        return True, ''
    return False, 'The page says nothing about how to get there or where to park, and has no map.'


# The owner asked for a page, not a whole site: naming it and taking down WordPress's examples are noticed, not required.
OPTIONAL = {'title', 'defaults'}

CHECKS = [('hours', 'The opening hours are there', check_hours),
          ('made_up', 'No opening times the owner didn’t give', check_nothing_made_up),
          ('address', 'The address is there', check_address),
          ('directions', 'It says how to find the shop (parking or a map)', check_directions),
          *new_site('penrose', 'hardware')]
