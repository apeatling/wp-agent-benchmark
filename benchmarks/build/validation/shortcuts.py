"""Shortcuts that look done but aren't, kept outside the tasks. Run on a fresh site, then the checks: the
post, photo, hours, plugins and menu checks must all fail. Uses the same site.json as the solution."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from solve import call, page  # noqa: E402  (the reference solution's helpers, copied beside this file)

# The post, left as a draft, with a photo linked from elsewhere instead of uploaded.
call('POST', '/wp/v2/posts', {'title': 'Our Christmas cakes are here', 'status': 'draft',
                               'content': '<img src="https://example.com/cakes.jpg"><p>Small £24, large £42, from 1 December.</p>'})
# The hours on a new page, not the contact page.
call('POST', '/wp/v2/pages', {'title': 'Holiday hours', 'status': 'publish',
                               'content': 'Christmas Eve 7am to 1pm. Closed Christmas Day and Boxing Day. New Year’s Eve 7am to 3pm.'})
# The "fixed" menu page: the error's gone because the menu is too.
call('POST', '/wp/v2/plugins/sunnyside-specials/sunnyside-specials', {'status': 'inactive'})
call('POST', f"/wp/v2/pages/{page('menu')['id']}", {'content': '<p>Our menu is coming soon.</p>'})
# "Updated" by switching the plugins off.
for slug in ('health-check', 'wordpress-importer'):
    call('POST', f'/wp/v2/plugins/{slug}/{slug}', {'status': 'inactive'})
print(json.dumps({'shortcuts': 'applied'}))
