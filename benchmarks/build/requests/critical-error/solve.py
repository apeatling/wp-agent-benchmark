# The site fails on every request, the REST API included, so nothing can be done through it until recovery mode
# pauses the broken plugin. The owner has the recovery-mode link WordPress emailed them, and forwards it if asked.

class Recovery(Dashboard):
    """The owner's dashboard login, through the recovery-mode link (the link sets a cookie the login needs)."""

    def __init__(self, link):
        self.jar = http.cookiejar.CookieJar()
        self.web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.open(link)
        self.open('/wp-login.php')  # the first page in recovery mode pauses the failing plugin
        self.open('/wp-login.php', {'log': CONFIG['user'], 'pwd': CONFIG['admin_password'], 'wp-submit': 'Log In',
                                    'redirect_to': SITE + '/wp-admin/', 'testcookie': '1'})

    def open(self, path, fields=None):
        """Open a page; an error page's text instead of an exception (the site still fails until it's fixed)."""
        data = urllib.parse.urlencode(fields).encode() if fields else None
        try:
            with self.web.open(path if path.startswith('http') else SITE + path, data=data, timeout=600) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.read().decode('utf-8', 'replace')


LINK = SITE + '/wp-login.php?action=enter_recovery_mode&rm_token=wpabrecovery&rm_key=Kp3vQ8sLx2RmT7wN4yZ6bD'


def solve():
    # The owner forwards the recovery-mode email when asked (requests.toml). Its link sets a cookie that pauses
    # the broken plugin for this session, so the REST API answers again, and the plugin can be switched off.
    jar = http.cookiejar.CookieJar()
    web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    for url in (LINK, SITE + '/'):
        try:
            web.open(url, timeout=60).read()
        except urllib.error.HTTPError:
            pass
    req = urllib.request.Request(SITE + '/wp-json/wp/v2/plugins/sunnyside-specials/sunnyside-specials', method='POST',
                                 data=json.dumps({'status': 'inactive'}).encode(),
                                 headers={'Authorization': AUTH, 'Content-Type': 'application/json'})
    with web.open(req, timeout=60) as r:
        if json.loads(r.read())['status'] != 'inactive':
            raise SystemExit('the specials plugin is still active')
