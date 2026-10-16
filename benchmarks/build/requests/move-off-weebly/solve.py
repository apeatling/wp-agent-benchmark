# Each Weebly page's titles, text and photos as blocks on a page (the photos uploaded; the contact form left out,
# as the page's phone number and email do its job); the pages in the old menu's order, which the theme's menu
# lists, so the rooms page is in it; the home page as the front page; the site named; the example content gone.

import tempfile

OLD = 'http://www.penhallowbnb.test'
PAGES = [('index', 'home', 'Home'), ('rooms', 'rooms', 'Rooms'), ('breakfast', 'breakfast', 'Breakfast'),
         ('find-us', 'find-us', 'Find us'), ('contact', 'contact', 'Contact')]


def fetch(path):
    with urllib.request.urlopen(OLD + path, timeout=60) as r:
        return r.read()


def solve():
    ids = {}
    for order, (name, slug, title) in enumerate(PAGES):
        markup = fetch(f'/{name}.html').decode()
        content = re.search(r'<div id="wsite-content"[^>]*>(.*?)<div class="footer-wrap">', markup, flags=re.S).group(1)
        content = re.sub(r'<form\b.*?</form>', '', content, flags=re.S)
        blocks = []
        for m in re.finditer(r'<h2 class="wsite-content-title">(.*?)</h2>|<div class="paragraph"[^>]*>(.*?)</div>|<img src="([^"?]+)[^"]*"', content, flags=re.S):
            heading, para, src = m.groups()
            if heading:
                blocks.append(f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{heading}</h2>\n<!-- /wp:heading -->')
            elif para:
                for p in re.split(r'<br>\s*<br>', para):
                    blocks.append(f'<!-- wp:paragraph -->\n<p>{p.strip()}</p>\n<!-- /wp:paragraph -->')
            else:
                path = Path(tempfile.mkdtemp()) / src.rsplit('/', 1)[-1].replace('_orig', '')
                path.write_bytes(fetch(src))
                alt = path.stem.replace('-', ' ').capitalize()
                media = upload(path, alt=alt)
                blocks.append(f'<!-- wp:image {{"id":{media["id"]},"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large">'
                              f'<img src="{media["source_url"]}" alt="{alt}" class="wp-image-{media["id"]}"/></figure>\n<!-- /wp:image -->')
        ids[slug] = call('POST', '/wp/v2/pages', {'title': title, 'slug': slug, 'status': 'publish', 'menu_order': order,
                                                   'content': '\n\n'.join(blocks)})['id']
    call('POST', '/wp/v2/settings', {'title': 'Penhallow B&B', 'description': 'Bed and breakfast in Mousehole, Cornwall',
                                     'show_on_front': 'page', 'page_on_front': ids['home']})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
