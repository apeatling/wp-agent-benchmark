# The export's pages and posts created through the API (WordPress's importer has no API), with each image fetched
# from Squarespace's image host and uploaded; the home page on the front; the site named; the examples gone.

import tempfile
import xml.etree.ElementTree as ET

NS = {'wp': 'http://wordpress.org/export/1.2/', 'content': 'http://purl.org/rss/1.0/modules/content/'}


def solve():
    root = ET.parse(next(Path('/app').glob('*.xml'))).getroot()
    home = None
    for item in root.iter('item'):
        kind = item.find('wp:post_type', NS).text
        if kind not in ('page', 'post'):
            continue
        body = item.find('content:encoded', NS).text
        for src in dict.fromkeys(re.findall(r'<img src="([^"]+)"', body)):
            path = Path(tempfile.mkdtemp()) / src.rsplit('/', 1)[-1]
            with urllib.request.urlopen(src, timeout=60) as r:
                path.write_bytes(r.read())
            body = body.replace(src, upload(path)['source_url'])
        made = call('POST', f"/wp/v2/{kind}s", {'title': item.find('title').text, 'slug': item.find('wp:post_name', NS).text,
                                                'status': 'publish', 'content': body,
                                                'date': item.find('wp:post_date', NS).text.replace(' ', 'T')})
        if item.find('wp:post_name', NS).text == 'home':
            home = made['id']
    call('POST', '/wp/v2/settings', {'title': 'Saltwater Yoga', 'show_on_front': 'page', 'page_on_front': home})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
