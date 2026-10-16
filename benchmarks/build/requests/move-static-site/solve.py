# Each old page's content as a page (the classic editor's content, as the old HTML is mostly tables and text),
# with its photos uploaded; the home page as the front page; the site named; the example content gone; then Jo.

import tempfile

OLD = 'http://www.quaysidephysio.test'
PAGES = [('index', 'home', 'Welcome to Quayside Physiotherapy'), ('about', 'about', 'About the clinic'), ('treatments', 'treatments', 'Treatments'),
         ('team', 'our-team', 'Our team'), ('prices', 'prices', 'Prices'), ('contact', 'contact', 'Contact us')]


def fetch(path):
    with urllib.request.urlopen(OLD + path, timeout=60) as r:
        return r.read()


def solve():
    ids = {}
    for name, slug, title in PAGES:
        markup = fetch(f'/{name}.html').decode()
        content = re.search(r'<div id="content">(.*)</div>\s*<div id="footer">', markup, flags=re.S).group(1)
        content = re.sub(r'<h1>.*?</h1>', '', content, flags=re.S)
        for src in dict.fromkeys(re.findall(r'<img[^>]*src="([^"]+)"', content)):
            path = Path(tempfile.mkdtemp()) / src.rsplit('/', 1)[-1]
            path.write_bytes(fetch('/' + src))
            alt = re.search(rf'src="{re.escape(src)}"[^>]*alt="([^"]*)"', content).group(1)
            content = content.replace(f'src="{src}"', f'src="{upload(path, alt=alt)["source_url"]}"')
        ids[slug] = call('POST', '/wp/v2/pages', {'title': title, 'slug': slug, 'status': 'publish', 'content': content.strip()})['id']
    call('POST', '/wp/v2/settings', {'title': 'Quayside Physiotherapy', 'show_on_front': 'page', 'page_on_front': ids['home']})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
    team = one('page', 'our-team')
    jo = '\n<p><b>Jo Penhale</b><br>Sports massage therapist. Jo joined us in September.</p>'
    call('POST', f"/wp/v2/pages/{team['id']}", {'content': team['content']['raw'] + jo})
