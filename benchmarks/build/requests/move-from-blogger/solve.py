# The backup's published posts created through the API (WordPress's Blogger importer needs Blogger's own login and
# has no API), with their dates and labels, each photo fetched from Blogger's image host at full size and uploaded,
# and readers' comments on them. The template, settings and drafts are left out. The site named; the examples gone.

import tempfile
import xml.etree.ElementTree as ET

A = '{http://www.w3.org/2005/Atom}'
KIND = 'http://schemas.google.com/blogger/2008/kind#'


def kind(e):
    return next((c.get('term')[len(KIND):] for c in e.findall(A + 'category') if c.get('scheme') == 'http://schemas.google.com/g/2005#kind'), '')


def local(stamp):
    """Blogger's timestamp as the site's local time (Europe/London, the blog's own time zone)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/London')).strftime('%Y-%m-%dT%H:%M:%S')


def solve():
    entries = ET.parse(next(Path('/app').glob('blog-*.xml'))).getroot().findall(A + 'entry')
    made, tags = {}, {}
    for e in entries:
        if kind(e) != 'post' or e.find('.//{http://purl.org/atom/app#}draft') is not None:
            continue
        body = e.find(A + 'content').text
        # Each photo is a small copy linked to the full-size one: upload the full size, and point both at it.
        for m in re.finditer(r'<a href="([^"]+/s1600/[^"]+)"[^>]*><img [^>]*src="([^"]+)"', body):
            big, small = m.groups()
            path = Path(tempfile.mkdtemp()) / big.rsplit('/', 1)[-1]
            with urllib.request.urlopen(big, timeout=60) as r:
                path.write_bytes(r.read())
            url = upload(path)['source_url']
            body = body.replace(big, url).replace(small, url)
        labels = [c.get('term') for c in e.findall(A + 'category') if c.get('scheme') == 'http://www.blogger.com/atom/ns#']
        for label in labels:
            if label not in tags:
                tags[label] = call('POST', '/wp/v2/tags', {'name': label})['id']
        link = next(l.get('href') for l in e.findall(A + 'link') if l.get('rel') == 'alternate')
        post = call('POST', '/wp/v2/posts', {'title': e.find(A + 'title').text, 'content': body, 'status': 'publish',
                                             'slug': link.rsplit('/', 1)[-1].removesuffix('.html'),
                                             'date': local(e.find(A + 'published').text), 'tags': [tags[l] for l in labels]})
        made[e.find(A + 'id').text] = post['id']
    for e in entries:
        reply = e.find('{http://purl.org/syndication/thread/1.0}in-reply-to')
        if kind(e) == 'comment' and reply is not None and reply.get('ref') in made:
            who = e.find(A + 'author')
            call('POST', '/wp/v2/comments', {'post': made[reply.get('ref')], 'author_name': who.find(A + 'name').text,
                                             'author_email': who.find(A + 'email').text, 'content': e.find(A + 'content').text,
                                             'date': local(e.find(A + 'published').text), 'status': 'approved'})
    call('POST', '/wp/v2/settings', {'title': 'Wool and Waves',
                                     'description': 'Knitting, yarn and the odd walk on the cliffs, from West Cornwall.'})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
