# Leaving Wix without losing the site's place in Google: every address on the old site (its sitemap) works on the
# new one, serving the same page or sending visitors and search engines there with a permanent redirect.
# Taking the domain across is for later: the old addresses are tried on the new site's address.

OLD_PAGES = json.loads('[{"path": "/", "slug": "home", "kind": "page", "title": "Learn to surf at Trevone"}, {"path": "/about-us", "slug": "about", "kind": "page", "title": "About us"}, {"path": "/lessons-1", "slug": "lessons", "kind": "page", "title": "Lessons"}, {"path": "/prices", "slug": "prices", "kind": "page", "title": "Prices"}, {"path": "/contact-8", "slug": "contact", "kind": "page", "title": "Contact"}, {"path": "/blog", "slug": "blog", "kind": "blog", "title": "Blog"}, {"path": "/post/best-beaches-for-beginners", "slug": "best-beaches-for-beginners", "kind": "post", "title": "The best beaches for beginners near Padstow"}, {"path": "/post/what-to-wear-surfing-in-cornwall", "slug": "what-to-wear-surfing-in-cornwall", "kind": "post", "title": "What to wear surfing in Cornwall"}, {"path": "/post/our-new-surf-van", "slug": "our-new-surf-van", "kind": "post", "title": "Our new surf van"}]')
ALLOW = {'changed': [p['slug'] for p in OLD_PAGES]}


def follow(path):
    """Follow an address on the site the way a search engine does: [(status, location)] for each step."""
    class Stop(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a):
            return None
    opener = urllib.request.build_opener(Stop)
    steps, url = [], SITE + path
    for _ in range(6):
        try:
            with opener.open(urllib.request.Request(url, headers={'X-WPAB-Monitor': '1'}), timeout=60) as r:
                steps.append((r.status, url, r.read().decode('utf-8', 'replace')))
                return steps
        except urllib.error.HTTPError as e:
            location = e.headers.get('Location')
            steps.append((e.code, url, ''))
            if e.code not in (301, 302, 303, 307, 308) or not location:
                return steps
            url = urllib.parse.urljoin(url, location)
    return steps


def check_old_addresses():
    broken = []
    for p in OLD_PAGES:
        steps = follow(p['path'])
        status, _, body = steps[-1]
        title = p['title'].lower()
        shows = status == 200 and (title in text(main_content(body)) or (p['kind'] == 'blog' and all(
            q['title'].lower() in text(body) for q in OLD_PAGES if q['kind'] == 'post')))
        temporary = [s for s, *_ in steps[:-1] if s not in (301, 308)]
        if not shows:
            broken.append(f"{p['path']} ({'doesn’t lead to “' + p['title'] + '”' if status == 200 else status})")
        elif temporary:
            broken.append(f"{p['path']} (a temporary {temporary[0]} redirect)")
    n = len(OLD_PAGES)
    return (not broken), (f'{n - len(broken)} of {n} old addresses work; not: ' + ', '.join(broken) + '.' if broken else '')


CHECKS = [('old_addresses', 'Every old address leads to the same page on the new site, permanently', check_old_addresses)]
