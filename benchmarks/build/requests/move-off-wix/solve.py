# Permanent redirects from the old Wix addresses (its sitemap) to the same pages on WordPress, with the
# Redirection plugin, set up through its own API (its first-run database step included).

OLD = 'http://www.trevonesurf.test'


def solve():
    with urllib.request.urlopen(OLD + '/sitemap.xml', timeout=60) as r:
        paths = [urllib.parse.urlparse(u).path for u in re.findall(r'<loc>([^<]+)</loc>', r.read().decode())]
    call('POST', '/wp/v2/plugins', {'slug': 'redirection', 'status': 'active'})
    for _ in range(10):
        if call('POST', '/redirection/v1/plugin/data', {}).get('status') == 'ok':
            break
    call('POST', '/redirection/v1/plugin/finish', {})
    # Each old page's title, from the old site, finds it on the new one.
    content = call('GET', '/wp/v2/pages?per_page=100') + call('GET', '/wp/v2/posts?per_page=100')
    for path in paths:
        if path in ('/', '/blog', '/prices'):
            continue  # the same address on WordPress
        with urllib.request.urlopen(OLD + path, timeout=60) as r:
            title = html.unescape(re.search(r'<h1[^>]*>(.*?)</h1>', r.read().decode()).group(1))
        target = next(p for p in content if html.unescape(p['title']['rendered']) == title)
        call('POST', '/redirection/v1/redirect', {'url': path, 'action_data': {'url': urllib.parse.urlparse(target['link']).path},
                                                  'action_type': 'url', 'match_type': 'url', 'group_id': 1, 'action_code': 301, 'regex': False})
