# The old hand-built site (www.quaysidephysio.test) moved onto WordPress: every page, with its text, as content
# that can be edited, with its photos in the site's media library; then (the owner's follow-up) Jo on the team page.

OLD = 'www.quaysidephysio.test'
PAGES = {'Home': ['since 2008', 'gp referral', 'chartered physiotherapists'],
         'About': ['anna carne founded', 'derriford hospital', 'hcpc', 'bupa'],
         'Treatments': ['sports injuries', 'acupuncture', 'pilates', 'no more than six people'],
         'Our team': ['mark trudgeon', 'lowenna hicks', 'dave rowe', 'insurance claims'],
         'Prices': ['first appointment', '£65', '£72', '24 hours'],
         'Contact': ['7 the quay', 'pl23 1at', 'info@quaysidephysio.test', 'hanson drive']}
ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}


@cache
def moved():
    return {name: best_match(words) for name, words in PAGES.items()}


def check_pages():
    missing = [f"{name} ({', '.join(m[2])})" for name, m in moved().items() if m[2]]
    return (not missing), ('Not moved, or missing text: ' + '; '.join(missing) + '.' if missing else '')


def check_front():
    s, body = get('/')
    t = text(main_content(body)) if s == 200 else ''
    missing = [w for w in PAGES['Home'] if w not in t]
    return (not missing), ('The front page isn’t the old home page.' if missing else '')


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
    ours = [u.rsplit('/', 1)[-1].lower() for u in shown if in_uploads(u)]
    if old:
        return False, f'{len(old)} photo(s) are still loaded from the old site.'
    # The six photos on the old pages (the logo aside), by name.
    want = {'clinic', 'treatment', 'anna', 'mark', 'lowenna', 'dave'}
    got = {w for w in want if any(w in f for f in ours)}
    return got == want, ('' if got == want else f'{len(got)} of the old pages’ 6 photos are on the new pages, from the site’s media library.')


def check_jo():
    p, body, _ = moved()['Our team']
    if not p:
        return False, 'No team page.'
    t = text(main_content(body))
    ok = bool(re.search(r'\bjo\b', t)) and 'sports massage' in t
    return ok, ('' if ok else 'Jo, the sports massage therapist, isn’t on the team page.')


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'jo'}

CHECKS = [('pages', 'Every page of the old site is on the new one, with its text', check_pages),
          ('front', 'The front page is the old home page', check_front),
          ('editable', 'They’re pages that can be edited, not copies of the old web pages', check_editable),
          ('photos', 'The photos are in the site’s media library', check_photos),
          *new_site('quayside'),
          ('jo', 'Jo is on the team page (the follow-up)', check_jo)]
