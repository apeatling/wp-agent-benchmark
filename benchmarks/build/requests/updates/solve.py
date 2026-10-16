# The owner's way: the dashboard's Updates screen. WordPress first, then the plugins and the theme.

def solve():
    d = dashboard()
    form = re.search(r'<form[^>]+action="update-core.php\?action=do-core-upgrade".*?</form>', d.get('/wp-admin/update-core.php'), re.S)
    if not form:
        raise SystemExit('no WordPress update offered on the Updates screen')
    nonce = re.search(r'name="_wpnonce" value="([^"]+)"', form.group(0))
    version = re.search(r'name="version" value="([^"]+)"', form.group(0))
    d.post('/wp-admin/update-core.php?action=do-core-upgrade',
           {'_wpnonce': nonce.group(1), 'version': version.group(1), 'locale': 'en_US', 'upgrade': 'Update to version ' + version.group(1)})
    # The Updates screen again, now WordPress is done: tick every plugin, then every theme, and follow the frame
    # the update runs in.
    for kind, action in (('plugins', 'do-plugin-upgrade'), ('themes', 'do-theme-upgrade')):
        page = d.get('/wp-admin/update-core.php')
        form = re.search(rf'<form[^>]+action="update-core.php\?action={action}".*?</form>', page, re.S)
        if not form:
            continue
        nonce = re.search(r'name="_wpnonce" value="([^"]+)"', form.group(0)).group(1)
        ticked = re.findall(r'name="checked\[\]"[^>]*value="([^"]+)"', form.group(0))
        fields = [('_wpnonce', nonce), *[('checked[]', t) for t in ticked], ('upgrade', 'Update')]
        with d.web.open(SITE + f'/wp-admin/update-core.php?action={action}', data=urllib.parse.urlencode(fields).encode(), timeout=600) as r:
            out = r.read().decode('utf-8', 'replace')
        frame = re.search(r'<iframe[^>]+src="([^"]+)"', out)
        if not frame:
            raise SystemExit(f'no update frame for the {kind}')
        d.get('/wp-admin/' + html.unescape(frame.group(1)).split('/wp-admin/')[-1])
