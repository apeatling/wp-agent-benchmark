# Enquiries sent through the contact form reach office@harbourplumbing.test. Found out by sending one, the way a
# visitor's browser does, and looking in the inbox.

import secrets as _secrets
import time

OFFICE = 'office@harbourplumbing.test'


def contact_form():
    """(page path, form html) for the form on the contact page, or on another page if it moved."""
    pages = sorted(find(state(), 'page'), key=lambda p: p['slug'] != 'contact')
    for p in pages:
        path = f"/?page_id={p['id']}"
        s, body = get(path)
        for form in re.findall(r'<form\b.*?</form>', body, flags=re.S | re.I):
            if re.search(r'<textarea\b', form, flags=re.I):
                return path, form
    return None, None


def send_enquiry(path, form, message):
    """Fill in every field and send it as the browser does. WPForms forms set to submit by AJAX (its default) are
    sent to admin-ajax.php with action=wpforms_submit, like its script; other forms to their action."""
    data = {}
    for tag in re.finditer(r'<(input|textarea|select)\b([^>]*)>', form, flags=re.I):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag.group(2)))
        name, kind = attrs.get('name'), (attrs.get('type') or tag.group(1)).lower()
        if not name or kind in ('submit', 'button', 'file') or '[hp]' in name or 'honeypot' in name.lower():
            continue
        value = html.unescape(attrs.get('value', ''))
        label = re.search(rf'<label[^>]*for="{re.escape(attrs.get("id", "-"))}"[^>]*>(.*?)</label>', form, flags=re.S | re.I)
        words = (name + ' ' + attrs.get('placeholder', '') + ' ' + (label.group(1) if label else '')).lower()
        if kind == 'hidden':
            pass
        elif kind == 'email' or 'email' in words:
            value = 'sam.tregear@example.test'
        elif kind == 'textarea' or 'message' in words or 'help' in words:
            value = message
        elif kind == 'tel' or 'phone' in words:
            value = '01632 960555'
        elif kind in ('checkbox', 'radio'):
            value = attrs.get('value', '1')
        elif kind == 'select':
            continue
        else:
            value = 'Sam Tregear'
        data.setdefault(name, value)
    for sel in re.finditer(r'<select\b[^>]*name="([^"]+)"[^>]*>(.*?)</select>', form, flags=re.S | re.I):
        opts = re.findall(r'<option[^>]*value="([^"]+)"', sel.group(2))
        if opts:
            data[sel.group(1)] = html.unescape(opts[0])
    head = re.match(r'<form\b[^>]*>', form, flags=re.I).group(0)
    if 'wpforms-ajax-form' in head:
        url, data['action'] = SITE + '/wp-admin/admin-ajax.php', 'wpforms_submit'
    else:
        action = html.unescape((re.search(r'action="([^"]*)"', head) or [None, ''])[1])
        url = urllib.parse.urljoin(SITE + path, action or path)
    return get(url, method='POST', data=urllib.parse.urlencode(data).encode(),
               headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': SITE + path, 'X-Requested-With': 'XMLHttpRequest'})


def check_enquiry():
    path, form = contact_form()
    if not form:
        return False, 'There’s no contact form on the site any more.'
    token = 'leaking radiator ' + _secrets.token_hex(4)
    status, body = send_enquiry(path, form, f'Hello, we have a {token} in the back bedroom, could someone come and look?')
    if status >= 400 or status == 0:
        return False, f'Sending the contact form failed ({status}).'
    for _ in range(10):
        if any(token in m['text'] for m in mail_to(OFFICE)):
            return True, ''
        time.sleep(1)
    return False, f'An enquiry sent through the contact form didn’t reach {OFFICE}.'


CHECKS = [('enquiry', 'An enquiry sent through the contact form reaches the office', check_enquiry, True)]
