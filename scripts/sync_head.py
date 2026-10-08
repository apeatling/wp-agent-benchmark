"""Copy the shared <head> lines in templates/head.html into every page in site/.

The site is plain HTML with no build step, so each page carries its own copy of the shared head, between
<!-- shared head --> and <!-- /shared head -->. Edit templates/head.html (for example to bump a ?v= number),
then run this. Lines marked data-section="choose" only go into pages under site/choose/. Everything else in
a page's head (its title, page-only styles) stays in the page.

    python3 scripts/sync_head.py            update every page
    python3 scripts/sync_head.py --check    exit 1 if any page is out of date (CI runs this)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
START, END = '<!-- shared head: edit templates/head.html, then run scripts/sync_head.py -->', '<!-- /shared head -->'
# Pages kept locally and never published or committed.
SKIP = ('site/build/', 'site/data-local/', 'site/choose/_')


def block(page):
    lines = (ROOT / 'templates' / 'head.html').read_text().strip().splitlines()
    section = page.relative_to(SITE).parts[0]
    keep = [re.sub(r' data-section="[^"]*"', '', l) for l in lines
            if 'data-section=' not in l or f'data-section="{section}"' in l]
    return '\n'.join([START, *keep, END])


def pages():
    for page in sorted(SITE.rglob('*.html')):
        rel = page.relative_to(ROOT).as_posix()
        if not rel.startswith(SKIP):
            yield page


def synced(page):
    """The page with its shared head replaced, or None if it has no markers."""
    text = page.read_text()
    found = re.search(re.escape(START) + r'.*?' + re.escape(END), text, flags=re.S)
    return text[:found.start()] + block(page) + text[found.end():] if found else None


def main():
    check, stale, missing = '--check' in sys.argv, [], []
    for page in pages():
        new = synced(page)
        if new is None:
            missing.append(page)
        elif new != page.read_text():
            stale.append(page)
            if not check:
                page.write_text(new)
    for page in missing:
        print(f'No shared head markers in {page.relative_to(ROOT)}')
    if check and stale:
        print('Out of date (run python3 scripts/sync_head.py):\n  ' + '\n  '.join(str(p.relative_to(ROOT)) for p in stale))
    elif stale:
        print(f'Updated {len(stale)} pages.')
    return 1 if missing or (check and stale) else 0


if __name__ == '__main__':
    sys.exit(main())
