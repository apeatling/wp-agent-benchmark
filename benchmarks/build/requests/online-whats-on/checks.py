# The village hall's weekly list of what's on, from the volunteer's notes, published where visitors find it from
# the front page, with each activity's day and time and the one that isn't at the hall; then (the owner's
# follow-up) Tuesday's yoga at 7pm.

ALLOW = {'changed': ['home']}
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
# Each activity, by words that pick it out: its day and its start time in minutes after midnight. Yoga's time
# is checked on its own (the follow-up moves it).
ACTIVITIES = {'toddler': ('monday', 10 * 60), 'yoga': ('tuesday', None), 'walking football': ('wednesday', 10 * 60),
              'bingo': ('wednesday', 19 * 60 + 30), 'bowls': ('thursday', 14 * 60), 'youth club': ('friday', 18 * 60 + 30),
              'coffee morning': ('saturday', 10 * 60), 'tea dance': ('sunday', 14 * 60)}
# Every time in the owner's list (and the follow-up's 7pm), on a 12-hour clock, and every price on the site.
GIVEN_TIMES = {10 * 60, 11 * 60 + 30, 6 * 60, 7 * 60, 7 * 60 + 30, 7 * 60 + 45, 2 * 60, 4 * 60, 6 * 60 + 30, 8 * 60 + 30, 0}
GIVEN_PRICES = {'2', '8', '12'}


def links(markup):
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0]
            for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


def times(t):
    """[(position, minutes after midnight)] for every time of day in some text: with am or pm, as 10:30 or 10.30,
    as noon, or as a bare range of hours ("10 - 12"). Times without am or pm before 8 are afternoon."""
    found = []
    for m in re.finditer(r'\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)', t):
        found.append((m.start(), m.group(1), m.group(2), m.group(3)))
    for m in re.finditer(r'\b(\d{1,2})[:.](\d{2})\b(?!\s*(?:am|pm|a\.m|p\.m))', t):
        found.append((m.start(), m.group(1), m.group(2), ''))
    for m in re.finditer(r'\b(\d{1,2})\s*(?:-|to|till|until)\s*(?=\d{1,2}(?:[:.]\d{2}|\s*(?:am|pm|a\.m|p\.m)))', t):
        found.append((m.start(), m.group(1), None, ''))
    for m in re.finditer(r'\b(\d{1,2})\s*(?:-|to|till|until)\s*(\d{1,2})\b(?![:.]\d)', t):
        if int(m.group(1)) <= 12 and int(m.group(2)) <= 12:
            found += [(m.start(), m.group(1), None, ''), (m.start(2), m.group(2), None, '')]
    for m in re.finditer(r'\b(noon|midday)\b', t):
        found.append((m.start(), '12', None, 'pm'))
    out = {}
    for pos, h, mins, ampm in found:
        h, mins = int(h), int(mins or 0)
        if h > 23 or mins > 59:
            continue
        if ampm.startswith('p') and h < 12 or not ampm and h < 8:
            h += 12
        out.setdefault(pos, h * 60 + mins)
    return sorted(out.items())


def near(t, words, before=60, after=80):
    """The times close to an activity's name (from just before it to just after), or None if it isn't there."""
    i = t.find(words)
    if i < 0:
        return None
    return [m for pos, m in times(t) if i - before <= pos <= i + len(words) + after]


def day_of(t, words):
    """The days an activity may be shown under: the last day named before it, or one named just after it.
    Days may be written in full or short ("Mon", "Tues"), and as plurals."""
    i = t.find(words)
    named = [(m.start(), DAYS[[d[:3] for d in DAYS].index(m.group(1)[:3])])
             for m in re.finditer(r'\b(mon|tues?|wed|thu|thur|thurs|fri|sat|sun)(?:day|nesday|urday|sday)?s?\b\.?', t)]
    before = [d for pos, d in named if i - 300 <= pos < i][-1:]
    after = [d for pos, d in named if i < pos <= i + len(words) + 40][:1]
    return set(before + after)


def count(t):
    return sum(1 for w in ACTIVITIES if w in t)


@cache
def pages():
    """Every published page and post as a visitor sees it, and the front page: {address: text of its own content}."""
    out = {}
    s, body = get('/')
    if s == 200:
        out['/'] = text(main_content(body))
    for p in state()['posts']:
        if p['type'] in ('page', 'post') and p['status'] == 'publish':
            q = 'page_id' if p['type'] == 'page' else 'p'
            s, body = get(f"/?{q}={p['id']}")
            if s == 200:
                out[f"/?{q}={p['id']}"] = text(main_content(body))
    return out


@cache
def list_page():
    """(address, text) of the page with most of the activities on it (at least three), or None."""
    best = max(((count(t), url, t) for url, t in pages().items()), default=None, key=lambda b: b[0])
    return (best[1], best[2]) if best and best[0] >= 3 else None


def check_whats_on():
    found = list_page()
    if not found:
        return False, 'There’s no page with the week’s activities on it.'
    t, wrong = found[1], []
    for words, (day, start) in ACTIVITIES.items():
        if words not in t:
            wrong.append(f'{words} (not there)')
        elif day not in day_of(t, words):
            wrong.append(f'{words} (not under {day.title()})')
        elif start is not None and start not in near(t, words):
            wrong.append(f'{words} (not at {start // 60 % 12 or 12}:{start % 60:02d})')
    return (not wrong), ('' if not wrong else f'{len(ACTIVITIES) - len(wrong)} of {len(ACTIVITIES)} activities are there with their day and time; not: ' + ', '.join(wrong) + '.')


def check_linked():
    found = list_page()
    if not found:
        return False, 'No what’s on page to look for.'
    want = count(found[1])
    if count(pages().get('/', '')) >= want:
        return True, ''
    s, body = get('/')
    if s != 200:
        return False, f'The front page returned {s}.'
    # Linked anywhere on the front page (its content, the menu or the footer): a page there with the whole list.
    host = urllib.parse.urlparse(SITE).netloc
    for url in dict.fromkeys(u for u in links(body) if urllib.parse.urlparse(u).netloc == host):
        if re.search(r'\.(pdf|jpe?g|png|docx?|txt)$|/wp-(admin|login)', url, flags=re.I):
            continue
        s, b = get(url)
        if s == 200 and count(text(main_content(b))) >= want:
            return True, ''
    return False, 'The front page doesn’t link to the what’s on page.'


def check_away():
    found = list_page()
    if not found:
        return False, 'No what’s on page to look at.'
    t = found[1]
    i = t.find('walking football')
    ok = i >= 0 and 'king george' in t[max(0, i - 200):i + 250]
    return ok, ('' if ok else 'The walking football doesn’t say it’s at King George’s Field rather than the hall.')


def check_yoga():
    found = list_page()
    if not found:
        return False, 'No what’s on page to look at.'
    t = found[1]
    got = near(t, 'yoga')
    if got is None:
        return False, 'Yoga isn’t on the page.'
    # 6pm may stay only as what it used to be ("now 7pm, was 6pm").
    i = t.find('yoga')
    old = [pos for pos, m in times(t) if m == 18 * 60 and i - 60 <= pos <= i + 84
           and not re.search(r'(was|from|used to be|instead of|not)\s*$', t[max(0, pos - 20):pos])]
    if 19 * 60 in got and not old:
        return True, ''
    return False, 'Tuesday’s yoga is still shown at 6pm.' if old else 'Tuesday’s yoga isn’t shown at 7pm.'


def check_nothing_made_up():
    found = list_page()
    if not found:
        return False, 'No what’s on page to look at.'
    t = found[1]
    made_up = sorted({f'{m // 60 % 12 or 12}:{m % 60:02d}' for _, m in times(t) if m % 720 not in GIVEN_TIMES})
    made_up += sorted({'£' + p for p in re.findall(r'£(\d+(?:\.\d{2})?)', t) if p.removesuffix('.00') not in GIVEN_PRICES})
    return (not made_up), ('The page has times or prices the owner didn’t give: ' + ', '.join(made_up) + '.' if made_up else '')


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'yoga'}

CHECKS = [('whats_on', 'Each week’s activities are on a page, with their day and time', check_whats_on),
          ('linked', 'The what’s on page can be found from the front page', check_linked),
          ('away', 'It says the walking football is at King George’s Field, not the hall', check_away),
          ('made_up', 'No times or prices the owner didn’t give', check_nothing_made_up),
          ('yoga', 'Tuesday’s yoga is at 7pm (the follow-up)', check_yoga)]
