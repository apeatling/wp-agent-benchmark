# The two pages from the old site, as blocks, with the About page's photos downloaded from the old site and uploaded.

import tempfile

OLD = 'http://www.polveanvets.test'


def fetch(path):
    with urllib.request.urlopen(OLD + path, timeout=60) as r:
        return r.read()


def blocks(markup):
    """The old page's main content as blocks: headings, paragraphs, and images uploaded to the site."""
    out = []
    for tag, attrs, inner in re.findall(r'<(h1|h2|h3|p|img)\b([^>]*?)/?>(?:(.*?)</\1>)?', markup, flags=re.S):
        if tag == 'h1':
            continue
        if tag == 'img':
            src = re.search(r'src="([^"]+)"', attrs).group(1)
            alt = re.search(r'alt="([^"]*)"', attrs).group(1)
            path = Path(tempfile.mkdtemp()) / src.rsplit('/', 1)[-1]
            path.write_bytes(fetch('/' + src))
            m = upload(path, alt=alt)
            out.append(f'<!-- wp:image {{"id":{m["id"]},"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large">'
                       f'<img src="{m["source_url"]}" alt="{alt}" class="wp-image-{m["id"]}"/></figure>\n<!-- /wp:image -->')
        elif tag == 'p':
            out.append(f'<!-- wp:paragraph -->\n<p>{inner.strip()}</p>\n<!-- /wp:paragraph -->')
        else:
            level = int(tag[1])
            out.append(f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{inner.strip()}</h{level}>\n<!-- /wp:heading -->')
    return '\n\n'.join(out)


def solve():
    for slug, title in [('about', 'About us'), ('faq', 'Frequently asked questions')]:
        markup = fetch(f'/{slug}.html').decode()
        main = re.search(r'<main>(.*?)</main>', markup, flags=re.S).group(1)
        call('POST', '/wp/v2/pages', {'title': title, 'slug': slug, 'status': 'publish', 'content': blocks(main)})
