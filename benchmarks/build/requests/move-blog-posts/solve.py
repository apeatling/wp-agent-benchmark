# Every post from the old blog's two listing pages, as posts with their dates, their photos uploaded, the author
# named on the post, and links to other old posts pointed at their new addresses.

import tempfile

OLD = 'http://www.tregennafarm.test'


def fetch(path):
    with urllib.request.urlopen(OLD + path, timeout=60) as r:
        return r.read()


def solve():
    slugs = []
    for listing in ('/blog/', '/blog/page/2/'):
        slugs += re.findall(r'<h2><a href="/blog/([^/]+)/">', fetch(listing).decode())
    made = {}
    for slug in reversed(slugs):  # oldest first, so links to earlier posts can be pointed at them
        markup = fetch(f'/blog/{slug}/').decode()
        title = html.unescape(re.search(r'<h1>(.*?)</h1>', markup).group(1))
        date = re.search(r'datetime="([^"]+)"', markup).group(1)
        author = re.search(r'Posted by (\w+)', markup).group(1)
        paras = re.findall(r'<p>(.*?)</p>', re.search(r'<article>(.*)</article>', markup, flags=re.S).group(1), flags=re.S)
        body = ''
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)"', markup)
        if img:
            path = Path(tempfile.mkdtemp()) / img.group(1).rsplit('/', 1)[-1]
            path.write_bytes(fetch(img.group(1)))
            m = upload(path, alt=html.unescape(img.group(2)))
            body += (f'<!-- wp:image {{"id":{m["id"]},"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large">'
                     f'<img src="{m["source_url"]}" alt="{img.group(2)}" class="wp-image-{m["id"]}"/></figure>\n<!-- /wp:image -->\n\n')
        for p in paras:
            p = re.sub(r'href="/blog/([^/]+)/"', lambda m: f'href="{made[m.group(1)]}"', p)
            body += f'<!-- wp:paragraph -->\n<p>{p}</p>\n<!-- /wp:paragraph -->\n\n'
        body += f'<!-- wp:paragraph -->\n<p><em>Posted by {author}</em></p>\n<!-- /wp:paragraph -->'
        post = call('POST', '/wp/v2/posts', {'title': title, 'slug': slug, 'status': 'publish', 'date': f'{date}T09:00:00', 'content': body})
        made[slug] = post['link']
