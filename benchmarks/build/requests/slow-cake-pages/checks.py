# The cake pages are quick again: they don't take seconds to come back, and they don't load megabytes of photos.
# How is up to the agent (smaller photos, switching off or replacing what makes them slow, caching); the cakes are
# still for sale, with their photos.

import time

CAKES = ['chocolate-celebration-cake', 'victoria-sponge', 'lemon-drizzle-loaf']
# The delivery-date plugin can be switched off: the pages say "Delivery or collection" without it.
ALLOW = {'deactivated': {'sunnyside-delivery/sunnyside-delivery.php'}, 'changed': CAKES}
SECONDS, MEGABYTES = 1.5, 1.5


@cache
def page(slug):
    """(status, html, seconds) for a cake's page as a visitor gets it."""
    p = find(state(), 'product', slug=slug)
    if not p:
        return 0, '', 0
    start = time.time()
    s, body = get(f"/?post_type=product&p={p[0]['id']}")
    return s, body, time.time() - start


@cache
def size(url):
    s, body = get(url)
    return len(body.encode('latin-1', 'replace')) if s == 200 else 0


def check_fast():
    slow = [f"{slug} ({page(slug)[2]:.1f}s)" for slug in CAKES if page(slug)[2] > SECONDS or page(slug)[0] != 200]
    return (not slow), ('Still slow to come back: ' + ', '.join(slow) + '.' if slow else '')


def check_light():
    heavy = []
    for slug in CAKES:
        s, body, _ = page(slug)
        mb = sum(size(u) for u in set(images(main_content(body)))) / 1e6
        if mb > MEGABYTES:
            heavy.append(f'{slug} ({mb:.1f} MB of photos)')
    return (not heavy), ('Still heavy: ' + ', '.join(heavy) + '.' if heavy else '')


def check_still_selling():
    problems = []
    for slug in CAKES:
        s, body, _ = page(slug)
        t = text(main_content(body))
        if s != 200 or '£' not in t:
            problems.append(f'{slug} (no price)')
        elif not any(in_uploads(u) for u in images(main_content(body))):
            problems.append(f'{slug} (no photo)')
    return (not problems), ('Not right any more: ' + ', '.join(problems) + '.' if problems else '')


CHECKS = [('fast', 'The cake pages come back quickly', check_fast),
          ('light', 'The cake pages don’t load megabytes of photos', check_light),
          ('selling', 'The cakes are still for sale, with their photos', check_still_selling)]
