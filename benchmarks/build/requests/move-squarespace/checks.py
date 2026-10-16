# The Squarespace site moved onto WordPress, from the export the owner downloaded: its pages and blog posts, with
# their photos in the site's own media library (in the export they're only links to Squarespace's image host,
# which goes when the subscription ends).

OLD_HOSTS = ('www.saltwateryoga.test', 'images.squarespace-cdn.test')
PAGES = {'Home': ['fistral beach', 'mats, blocks and blankets'], 'About': ['nina polglase', 'e-ryt 500'],
         'Timetable': ['sunrise flow', 'yin and restore', 'beach yoga'], 'Prices': ['£14', '£60', '£85'],
         'Contact': ['headland road', 'tr7 1hy']}
# Title, date, whether it has a photo.
POSTS = [('Beach yoga is back', '2024-05-02', True), ('What is yin yoga?', '2024-09-14', False),
         ('New six-week pregnancy course', '2025-01-08', True), ('Meet our new teacher, Tom', '2025-04-22', True),
         ('Studio closed for a week in February', '2025-02-03', False)]
PHOTO_PAGES = ['Home', 'About']
ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower()).strip()


@cache
def pages():
    return {name: best_match(words, types=('page', 'post')) for name, words in PAGES.items()}


@cache
def posts():
    out = {}
    for p in state()['posts']:
        if p['type'] == 'post' and p['status'] == 'publish':
            for title, *_ in POSTS:
                if norm(p['title']) == norm(title) and title not in out:
                    s, body = get(f"/?p={p['id']}")
                    out[title] = (p, body if s == 200 else '')
    return out


def check_pages():
    missing = [f"{name} ({', '.join(m[2])})" for name, m in pages().items() if m[2]]
    return (not missing), ('Not moved, or missing text: ' + '; '.join(missing) + '.' if missing else '')


def check_posts():
    missing = [t for t, *_ in POSTS if t not in posts()]
    wrong = [t for t, date, _ in POSTS if t in posts() and not posts()[t][0]['date'].startswith(date)]
    problems = ([f"not moved: {', '.join(missing)}"] if missing else []) + ([f"not dated as before: {', '.join(wrong)}"] if wrong else [])
    return (not problems), ('Blog posts ' + '; '.join(problems) + '.' if problems else '')


def check_photos():
    shown, missing = [], []
    for name in PHOTO_PAGES:
        p, body, gaps = pages()[name]
        found = images(main_content(body)) if p and not gaps else []
        shown += found
        if not any(in_uploads(u) for u in found):
            missing.append(f'the {name} page')
    for title, _, photo in POSTS:
        found = images(main_content(posts()[title][1])) if title in posts() else []
        shown += found
        if photo and not any(in_uploads(u) for u in found):
            missing.append(f'“{title}”')
    old = [u for u in shown if urllib.parse.urlparse(u).netloc in OLD_HOSTS]
    if old:
        return False, f'{len(old)} photo(s) are still loaded from Squarespace.'
    return (not missing), ('Without their photo from the site’s media library: ' + ', '.join(missing) + '.' if missing else '')


CHECKS = [('pages', 'The pages are on the new site, with their text', check_pages),
          ('posts', 'The blog posts are, with their dates', check_posts),
          ('photos', 'The photos are in the site’s media library', check_photos),
          *new_site('saltwater')]
