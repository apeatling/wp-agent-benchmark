# Visitors can book a free 15-minute chat with the owner on the website: a page that offers it, where they can ask
# for one, and the request reaches the owner's inbox.

import time

OWNER_EMAIL = 'ruth@kellowgardens.test'


def links(markup):
    return [urllib.parse.urljoin(SITE + '/', html.unescape(h)).split('#')[0]
            for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup, flags=re.I)]


def has_form(markup):
    return bool(re.search(r'<form\b(?![^>]*role="search")[^>]*>.*?</form>', main_content(markup), flags=re.S | re.I))


@cache
def booking_page():
    """Where visitors book: the front page, or a page on the site linked from it (content, menu or footer), that
    offers the 15-minute chat and has a form. Its path, or None."""
    s, body = get('/')
    if s != 200:
        return None
    host = urllib.parse.urlparse(SITE).netloc
    for url in dict.fromkeys(['/'] + [u for u in links(body) if urllib.parse.urlparse(u).netloc == host]):
        s, b = (200, body) if url == '/' else get(url)
        t = text(main_content(b)) if s == 200 else ''
        if re.search(r'\b15[- ]?(minute|min)', t) and has_form(b):
            parts = urllib.parse.urlparse(url)
            return (parts.path or '/') + ('?' + parts.query if parts.query else '')
    return None


def check_page():
    if booking_page():
        return True, ''
    return False, 'No page offering the free 15-minute chat with a form to book it, on the front page or linked from it.'


def check_booking_sent():
    """Book as a visitor would; the owner should get the request at her email address."""
    path = booking_page()
    if not path:
        return False, 'No booking form to send.'
    clear_mail()
    marker = 'a north-facing back garden in Truro'
    fields = {'name': 'Sam Visitor', 'email': 'sam.visitor@example.test', 'phone': '01632 960 111', 'tel': '01632 960 111',
              'subject': 'Free chat', 'message': f'Hello, I would love a chat about {marker}.', 'garden': marker,
              'about': marker, 'details': marker, 'comment': marker, 'date': '2026-11-17', 'time': '14:00'}
    status, _ = submit_form(path, fields)
    if status not in (200, 201, 302, 303):
        return False, f'Sending the booking failed ({status}).'
    for _ in range(10):
        mails = mail_to(OWNER_EMAIL)
        if any(marker in m['text'] or 'sam.visitor@example.test' in m['text'] for m in mails):
            return True, ''
        time.sleep(1)
    if mails:
        return False, f'Booking emailed {OWNER_EMAIL}, but without what the visitor wrote.'
    return False, f'Booking didn’t email {OWNER_EMAIL}.'


CHECKS = [('page', 'There’s a page to book the free 15-minute chat', check_page),
          ('booking_sent', f'A booking from the site reaches {OWNER_EMAIL}', check_booking_sent, True)]
