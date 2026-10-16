"""Reference solutions: what's shared. Each request's solution (benchmarks/build/requests/<id>/solve.py) is
appended to this file when tasks are built, into one solution/solve.py, and defines solve().

A solution uses what the agent is given: the site's address, the owner's application password and the files in
/app, through the REST API. Where WordPress offers no way through the API (requests marked outside_api), it
uses what the owner has instead: their own dashboard login (dashboard()) and the site's emails to them
(inbox()). The facts the owner gives when asked
are written in, as the owner would tell them. Every check must pass after it.
"""
import base64
import html
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG = json.loads((Path(__file__).parent / 'site.json').read_text())
SITE = CONFIG['url'].rstrip('/')
AUTH = 'Basic ' + base64.b64encode(f"{CONFIG['user']}:{CONFIG['password']}".encode()).decode()


def call(method, path, body=None, raw=None, headers=None):
    """A REST API request with the owner's application password; the decoded answer."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {'Authorization': AUTH, **({'Content-Type': 'application/json'} if body is not None else {}), **(headers or {})}
    req = urllib.request.Request(SITE + '/wp-json' + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path}: {e.code} {e.read()[:400]!r}')


def upload(path, alt=''):
    """A file from /app into the media library."""
    p = Path(path)
    mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.pdf': 'application/pdf'}[p.suffix.lower()]
    media = call('POST', '/wp/v2/media', raw=p.read_bytes(),
                 headers={'Content-Type': mime, 'Content-Disposition': f'attachment; filename="{p.name}"'})
    if alt:
        call('POST', f"/wp/v2/media/{media['id']}", {'alt_text': alt})
    return media


def one(type, slug):
    """A post, page or other type by slug, with its raw content."""
    rest = {'post': 'posts', 'page': 'pages', 'product': 'product'}.get(type, type)
    found = call('GET', f'/wp/v2/{rest}?slug={slug}&context=edit&status=any')
    if not found:
        raise SystemExit(f'no {type} {slug}')
    return found[0]


class Dashboard:
    """The owner's own login to wp-admin, for what the API can't do: a browser, without the browser."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.web.open(SITE + '/wp-login.php', timeout=60)
        self.post('/wp-login.php', {'log': CONFIG['user'], 'pwd': CONFIG['admin_password'], 'wp-submit': 'Log In',
                                    'redirect_to': SITE + '/wp-admin/', 'testcookie': '1'})

    def get(self, path):
        with self.web.open(SITE + path, timeout=600) as r:
            return r.read().decode('utf-8', 'replace')

    def post(self, path, fields):
        with self.web.open(SITE + path, data=urllib.parse.urlencode(fields).encode(), timeout=600) as r:
            return r.read().decode('utf-8', 'replace')

    def nonce(self, page, pattern):
        """A nonce from a dashboard page: the first value that follows pattern."""
        m = re.search(pattern, self.get(page))
        if not m:
            raise SystemExit(f'no nonce on {page}')
        return html.unescape(m.group(1))


def dashboard():
    return Dashboard()


def inbox(address):
    """What the owner's inbox has from the site (the mail catcher), newest first: [{'subject', 'text'}]. The
    owner would forward these if asked."""
    auth = 'Basic ' + base64.b64encode(f"checks:{CONFIG['mail_password']}".encode()).decode()
    def get(path):
        with urllib.request.urlopen(urllib.request.Request(CONFIG['mail'] + path, headers={'Authorization': auth}), timeout=60) as r:
            return json.loads(r.read())
    out = []
    for m in get('/api/v1/search?query=' + urllib.parse.quote('to:' + address)).get('messages', []):
        full = get(f"/api/v1/message/{m['ID']}")
        out.append({'subject': m.get('Subject', ''), 'text': full.get('Text') or full.get('HTML', '')})
    return out

