# The Blogger blog moved onto WordPress, from the backup the owner downloaded (Blogger's Atom export, which also
# holds the blog's template, its settings, two unpublished drafts and readers' comments): every published post,
# with its date, and its photos in the site's own media library rather than still loaded from Blogger's image host.
# The dates are in the export and the owner says she wants them kept if asked, so they're required.

OLD_HOSTS = ('woolandwaves.blogspot.test', 'blogger.googleusercontent.test')
# Title, date, a phrase from its text, whether it has a photo.
POSTS = [('My first pair of socks', '2017-01-15', 'turned a heel', True),
         ('Knitting on the beach', '2017-06-04', 'porthmeor', False),
         ('A gansey for Dad', '2018-02-11', 'polperro pattern', True),
         ('Wool shop crawl in Falmouth', '2019-09-22', 'three wool shops', True),
         ('Lockdown blanket, square by square', '2020-04-05', 'forty-two squares', True),
         ('Christmas jumper pattern, free to download', '2021-11-28', 'fair isle yoke', False),
         ('Dyeing yarn with gorse flowers', '2023-03-19', 'soft yellow', True),
         ('Ten years of Wool and Waves', '2025-08-10', 'here is to the next ten', True)]
# Drafts in the backup, never published on Blogger: title and a phrase from each.
DRAFTS = [('Rock Pool shawl, a pattern review', 'chart for row 37'), ('Selling my spinning wheel?', 'ashford wheel')]
# Readers' comments: the post they're on, and a phrase from each.
COMMENTS = [('My first pair of socks', 'nobody ever notices'), ('A gansey for Dad', 'my grandad had one'),
            ('Ten years of Wool and Waves', 'happy blogiversary')]
# The blog's template, as it reads if it's made into a post or page.
TEMPLATE = ('template wool and waves', 'b:skin', 'b:section', 'b:widget', 'data:blog', 'simple: wool and waves')
ALLOW = {'removed': ['hello-world', 'sample-page'], 'theme': True}
# The comments are readers', not the owner's: bringing them is noticed, not required.
OPTIONAL = {'comments', 'title', 'defaults'}  # the owner never asked to rename the site or remove WordPress's examples


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower().replace('’', "'").replace("'", '')).strip()


@cache
def moved():
    """{title: (post, html as a visitor sees it)} for each Blogger post that's a published post here."""
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
    empty = [t for t, _, phrase, _ in POSTS if t in moved() and phrase not in text(main_content(moved()[t][1]))]
    problems = ([f"not moved: {', '.join(f'“{t}”' for t in missing)}"] if missing else []) + \
               ([f"without their text: {', '.join(f'“{t}”' for t in empty)}"] if empty else [])
    return (not problems), ('Blog posts ' + '; '.join(problems) + '.' if problems else '')


def check_dates():
    if not moved():
        return False, 'No posts moved.'
    wrong = [t for t, date, *_ in POSTS if t in moved() and not moved()[t][0]['date'].startswith(date)]
    return (not wrong), ('Not dated as on Blogger: ' + ', '.join(f'“{t}”' for t in wrong) + '.' if wrong else '')


def check_photos():
    if not moved():
        return False, 'No posts moved.'
    missing, old = [], 0
    for t, _, _, photo in POSTS:
        if t in moved():
            shown = images(main_content(moved()[t][1]))
            old += sum(1 for u in shown if urllib.parse.urlparse(u).netloc in OLD_HOSTS)
            if photo and not any(in_uploads(u) for u in shown):
                missing.append(t)
    if old:
        return False, f'{old} photo(s) are still loaded from Blogger.'
    return (not missing), ('Without their photo from the site’s media library: ' + ', '.join(f'“{t}”' for t in missing) + '.' if missing else '')


@cache
def published():
    """Every published post and page, with its visible text."""
    out = []
    for p in state()['posts']:
        if p['type'] in ('post', 'page') and p['status'] == 'publish':
            s, body = get(f"/?page_id={p['id']}" if p['type'] == 'page' else f"/?p={p['id']}")
            out.append((p, text(main_content(body)) if s == 200 else ''))
    return out


def check_drafts():
    """The drafts in the backup aren't published (kept as drafts is fine)."""
    out = [t for t, phrase in DRAFTS if any(norm(p['title']) == norm(t) or phrase in body for p, body in published())]
    return (not out), ('Published, though they were only drafts on Blogger: ' + ', '.join(f'“{t}”' for t in out) + '.' if out else '')


def check_nothing_else():
    """The backup's template, settings (untitled entries) and comments didn't become posts or pages of their own."""
    titles = {norm(t) for t, *_ in POSTS}
    odd = []
    for p, body in published():
        t = norm(p['title'])
        if t in titles or (p['type'], p['slug']) in (('post', 'hello-world'), ('page', 'sample-page')):
            continue
        if not t or t == TEMPLATE[0] or any(w in body or w in raw_content(p).lower() for w in TEMPLATE[1:]) or any(phrase in body for _, phrase in COMMENTS):
            odd.append(p['title'] or f"an untitled {p['type']}")
    return (not odd), ('Made into posts or pages from the backup’s template, settings or comments: ' + ', '.join(f'“{t}”' for t in odd) + '.' if odd else '')


def check_comments():
    if not moved():
        return False, 'No posts moved.'
    missing = []
    for title, phrase in COMMENTS:
        found = api(f"/wp/v2/comments?post={moved()[title][0]['id']}&per_page=100") if title in moved() else []
        if not any(phrase in text(c['content']['rendered']) for c in found):
            missing.append(title)
    return (not missing), ('Readers’ comments not on: ' + ', '.join(f'“{t}”' for t in missing) + '.' if missing else '')


CHECKS = [('posts', 'Every published Blogger post is a post on the new site, with its text', check_posts),
          ('dates', 'With its original date', check_dates),
          ('photos', 'With its photos in the site’s media library, not loaded from Blogger', check_photos),
          ('drafts', 'The unpublished drafts weren’t published', check_drafts),
          ('nothing_else', 'The template, settings and comments didn’t become posts', check_nothing_else),
          ('comments', 'Readers’ comments came across', check_comments),
          *new_site('wool')]
