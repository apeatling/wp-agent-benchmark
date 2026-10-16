# New prices on the services page, which is built with Elementor; then (the owner's follow-up) the call-out fee.
# Prices are read as a visitor sees the page: the first price after each service's name. The page has to stay
# an Elementor page with its layout, not be flattened into plain content (Elementor would then show the old
# copy it keeps, or the owner couldn't edit it in Elementor any more).

ALLOW = {'changed': {'services'}}

SERVICES = {  # name: (how the page names it, old price, new price)
    'boiler service': (r'boiler servic', 85, 95),
    'gas safety certificate': (r'gas safety', 70, 80),
    'hourly rate': (r'hourly rate|per hour|an hour', 60, 70),
    'call-out fee': (r'call[- ]?out (fee|charge)', 55, 65),
}


def services_page():
    page = find(baseline(), 'page', slug='services')[0]
    now = next((p for p in state(meta=('_elementor_edit_mode', '_elementor_data'))['posts'] if p['id'] == page['id']), None)
    return page, now


def prices():
    """{service: the first price shown after its name, or None}, as a visitor sees the services page."""
    page, now = services_page()
    if not now or now['status'] != 'publish':
        raise RuntimeError('the services page is no longer published')
    status, t = visit(now)
    if status != 200:
        raise RuntimeError(f'the services page returned {status}')
    found = {}
    for name, (label, _, _) in SERVICES.items():
        m = re.search(label, t)
        price = re.search(r'£\s?(\d+(?:\.\d\d)?)', t[m.end():m.end() + 300]) if m else None
        found[name] = float(price.group(1)) if price else None
    return found


def price_check(names):
    shown = prices()
    wrong = []
    for name in names:
        _, old, new = SERVICES[name]
        if shown[name] != new:
            wrong.append(f"{name} shows {'£%g' % shown[name] if shown[name] is not None else 'no price'} (should be £{new})")
    return (not wrong), ('On the services page: ' + '; '.join(wrong) + '.' if wrong else '')


def check_prices():
    return price_check(['boiler service', 'gas safety certificate', 'hourly rate'])


def check_call_out():
    return price_check(['call-out fee'])


def check_elementor():
    page, now = services_page()
    if not now:
        return False, 'The services page is gone.'
    meta = now.get('meta', {})
    if meta.get('_elementor_edit_mode') != 'builder':
        return False, 'The services page is no longer edited with Elementor.'
    try:
        data = json.loads(meta.get('_elementor_data') or '[]')
    except ValueError:
        return False, 'The services page’s Elementor data is broken.'
    flat = json.dumps(data, ensure_ascii=False)
    if not data or now.get('builder_length', 0) < 0.6 * page.get('builder_length', 0):
        return False, 'The services page lost most of its Elementor layout.'
    if not re.search(r'£\s?95\b', flat):
        return False, 'The new prices aren’t in the page’s Elementor content (where Elementor shows them from and where the owner edits them).'
    s, body = get(f"/?page_id={now['id']}")
    if f'data-elementor-id="{now["id"]}"' not in body:
        return False, 'The services page isn’t shown by Elementor any more.'
    return True, ''


# Asked for only in the owner's follow-up, which comes once the agent says it's done.
FOLLOW_UP = {'call_out'}

CHECKS = [('prices', 'The services page shows the new prices', check_prices),
          ('elementor', 'The services page is still an Elementor page, with its layout', check_elementor),
          ('call_out', 'The services page shows the new call-out fee (the follow-up)', check_call_out)]
