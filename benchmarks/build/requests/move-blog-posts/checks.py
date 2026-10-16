# The blog moved from the old site (www.tregennafarm.test) onto WordPress: every post, with its original date, who
# wrote it, its photo in the site's media library, and its links to other posts going to their new addresses.

OLD = 'www.tregennafarm.test'
# Title, date, who wrote it, whether it has a photo, and the post it links to (by title).
POSTS = [('Lambing has started', '2019-03-14', 'Kate', True, None),
         ('Strawberry picking opens this weekend', '2019-07-02', 'Will', True, None),
         ('Christmas orders are open', '2019-12-01', 'Kate', False, None),
         ("We're still open, and now delivering", '2020-04-06', 'Kate', True, None),
         ('Meet our new Highland cattle', '2020-09-18', 'Will', True, None),
         ('Lambing 2021', '2021-03-22', 'Kate', True, 'Lambing has started'),
         ('Pumpkin patch is back', '2021-10-29', 'Will', True, None),
         ('The new café is open', '2022-06-11', 'Kate', True, None),
         ('Why we stopped using plastic trays', '2023-02-14', 'Will', False, None),
         ('Strawberry season, five years on', '2023-08-05', 'Kate', True, 'Strawberry picking opens this weekend'),
         ('Christmas trees from our own woods', '2024-11-20', 'Will', True, 'The new café is open'),
         ('Six generations at Tregenna', '2025-05-09', 'Kate', False, None)]
# Authors may be given accounts of their own (not administrators).
ALLOW = {'new_users': 2}


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower().replace('’', "'").replace("'", '')).strip()


@cache
def moved():
    """{title: (post, html as a visitor sees it)} for each old post that's a published post here."""
    out = {}
    for p in state()['posts']:
        if p['type'] == 'post' and p['status'] == 'publish':
            for title, *_ in POSTS:
                if norm(p['title']) == norm(title) and title not in out:
                    s, body = get(f"/?p={p['id']}")
                    out[title] = (p, body if s == 200 else '')
    return out


def check_posts():
    missing = [t for t, *_ in POSTS if t not in moved()]
    return (not missing), (f'{len(POSTS) - len(missing)} of {len(POSTS)} posts moved; not: ' + ', '.join(f'“{t}”' for t in missing) + '.' if missing else '')


def check_dates():
    wrong = [t for t, date, *_ in POSTS if t in moved() and not moved()[t][0]['date'].startswith(date)]
    if not moved():
        return False, 'No posts moved.'
    return (not wrong), ('Not dated as on the old site: ' + ', '.join(f'“{t}”' for t in wrong) + '.' if wrong else '')


def check_authors():
    """Who wrote each post: its author on the site, or named on the post."""
    if not moved():
        return False, 'No posts moved.'
    names = {u['id']: u['name'].lower() + ' ' + u['login'].lower() for u in state()['users']}
    wrong = [t for t, _, who, *_ in POSTS if t in moved()
             and who.lower() not in names.get(moved()[t][0]['author'], '')
             and not re.search(rf'\b{who.lower()}\b', text(main_content(moved()[t][1])))]
    return (not wrong), ('Not credited to who wrote them: ' + ', '.join(f'“{t}”' for t in wrong) + '.' if wrong else '')


def check_photos():
    if not moved():
        return False, 'No posts moved.'
    missing, old = [], 0
    for t, _, _, photo, _ in POSTS:
        if t in moved():
            shown = images(main_content(moved()[t][1]))
            old += sum(1 for u in shown if urllib.parse.urlparse(u).netloc == OLD)
            if photo and not any(in_uploads(u) for u in shown):
                missing.append(t)
    if old:
        return False, f'{old} photo(s) are still loaded from the old site.'
    return (not missing), ('Without their photo from the site’s media library: ' + ', '.join(f'“{t}”' for t in missing) + '.' if missing else '')


def check_links():
    """The links between posts go to the posts' new addresses."""
    if not moved():
        return False, 'No posts moved.'
    broken = []
    for t, *_, target in POSTS:
        if not target or t not in moved():
            continue
        hrefs = [urllib.parse.urljoin(SITE + '/', html.unescape(h)) for h in re.findall(r'<a\b[^>]*href="([^"]+)"', main_content(moved()[t][1]))]
        ok = False
        for h in hrefs:
            if urllib.parse.urlparse(h).netloc != urllib.parse.urlparse(SITE).netloc:
                continue
            s, body = get(h)
            if s == 200 and norm(target) in norm(text(main_content(body)))[:400]:
                ok = True
        if not ok:
            broken.append(t)
    return (not broken), ('Links to other posts don’t go to them on the new site in: ' + ', '.join(f'“{t}”' for t in broken) + '.' if broken else '')


CHECKS = [('posts', 'Every blog post is on the new site', check_posts),
          ('dates', 'With its original date', check_dates),
          ('authors', 'Credited to who wrote it', check_authors),
          ('photos', 'With its photo, in the site’s media library', check_photos),
          ('links', 'Links between posts go to their new addresses', check_links)]
