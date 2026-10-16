# A booking form (Contact Form 7, already on the site) asking for the times the owner gives, on its own page,
# emailed to the owner; the header menu lists the site's pages, so it's there too, and the front page links to it.

OWNER_EMAIL = 'ruth@kellowgardens.test'


def solve():
    form = call('POST', '/contact-form-7/v1/contact-forms', {
        'context': 'save',
        'title': 'Book a free chat',
        'form': ('<label> Your name\n    [text* your-name autocomplete:name] </label>\n\n'
                 '<label> Your email\n    [email* your-email autocomplete:email] </label>\n\n'
                 '<label> Phone number\n    [tel* your-phone] </label>\n\n'
                 '<label> When suits you?\n    [select your-slot "Tuesday afternoon" "Thursday afternoon"] </label>\n\n'
                 '<label> Tell me a little about your garden\n    [textarea your-message] </label>\n\n[submit "Book my chat"]'),
        'mail': {'subject': 'Free chat booking from [your-name]', 'sender': f'Ruth Kellow Garden Design <{OWNER_EMAIL}>',
                 'recipient': OWNER_EMAIL, 'additional_headers': 'Reply-To: [your-email]',
                 'body': 'From: [your-name] <[your-email]>\nPhone: [your-phone]\nWhen: [your-slot]\n\n[your-message]'},
    })
    content = ('<!-- wp:paragraph -->\n<p>Book a free 15-minute phone call to talk about your garden. I’m free on Tuesday '
               'and Thursday afternoons, between 1 and 5: pick the day that suits you and I’ll ring you to fix a time.</p>\n'
               '<!-- /wp:paragraph -->\n\n'
               f'<!-- wp:shortcode -->\n[contact-form-7 id="{form["id"]}" title="Book a free chat"]\n<!-- /wp:shortcode -->')
    page = call('POST', '/wp/v2/pages', {'title': 'Book a free chat', 'slug': 'book', 'status': 'publish', 'content': content})
    home = one('page', 'home')
    link = f'\n\n<!-- wp:paragraph -->\n<p><a href="{page["link"]}">Book a free 15-minute chat</a></p>\n<!-- /wp:paragraph -->'
    call('POST', f"/wp/v2/pages/{home['id']}", {'content': home['content']['raw'] + link})
