# A What's on page from the volunteer's list, a day at a time, with the walking football's field and the notes
# that go with each; linked from the front page. Tuesday's yoga is at 7pm, as the follow-up has it.

WEEK = [
    ('Monday', [('Toddler group', '10am to 11.30am', 'Tea, toys and a sing-song at the end. £2 a family.')]),
    ('Tuesday', [('Yoga with Sian', '7pm', 'Bring a mat if you’ve got one; there are a few spare.')]),
    ('Wednesday', [('Walking football', '10am', 'At King George’s Field, not the hall.'),
                   ('Bingo', '7.30pm', 'Eyes down at 7.45pm.')]),
    ('Thursday', [('Short mat bowls', '2pm to 4pm', '')]),
    ('Friday', [('Youth club', '6.30pm to 8.30pm', 'For ages 11 to 16.')]),
    ('Saturday', [('Coffee morning', '10am to 12 noon', 'Cakes, bric-a-brac and a raffle, all for the hall roof fund.')]),
    ('Sunday', [('Tea dance', '2pm to 4pm', '')]),
]


def solve():
    para = lambda t: f'<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->\n\n'
    content = para('Everything’s at the hall unless it says otherwise. There’s no need to book: just turn up.')
    for day, items in WEEK:
        content += f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{day}</h2>\n<!-- /wp:heading -->\n\n'
        for name, when, note in items:
            content += para(f'<strong>{name}</strong>, {when}' + (f'<br>{note}' if note else ''))
    content += para('Anything else, ring Jan on 01632 960587.')
    page = call('POST', '/wp/v2/pages', {'title': 'What’s on', 'slug': 'whats-on', 'status': 'publish', 'content': content})
    home = one('page', 'home')
    raw = home['content']['raw'] + f'\n\n<!-- wp:paragraph -->\n<p><a href="{page["link"]}">See what’s on each week</a></p>\n<!-- /wp:paragraph -->'
    call('POST', f"/wp/v2/pages/{home['id']}", {'content': raw})
