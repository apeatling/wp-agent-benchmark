# The menu as a page of text, from the PDF, linked from the front page in place of the PDF (which stays, as a
# download); then the flat white at £3.40.

MENU = [
    ('Coffee', [('Espresso', '2.40'), ('Americano', '2.90'), ('Flat white', '3.40'), ('Cappuccino', '3.30'),
                ('Latte', '3.50'), ('Mocha', '3.70')]),
    ('Tea and more', [('Pot of tea', '2.60'), ('Hot chocolate', '3.50')]),
    ('Breakfast (until 11.30)', [('Bacon roll', '4.50'), ('Sausage sandwich', '4.80'), ('Avocado on sourdough', '7.50'),
                                 ('Porridge with berries', '4.90'), ('Full Corner breakfast', '9.50')]),
    ('Lunch', [('Soup of the day with bread', '6.20'), ('Cheese toastie', '5.80'), ('Ham and mustard toastie', '6.40')]),
    ('Cakes', [('Scone with jam and cream', '3.80'), ('Slice of cake', '3.60')]),
]


def solve():
    content = ''
    for section, items in MENU:
        content += f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{section}</h2>\n<!-- /wp:heading -->\n\n'
        rows = ''.join(f'<tr><td>{name}</td><td>£{price}</td></tr>' for name, price in items)
        content += f'<!-- wp:table -->\n<figure class="wp-block-table"><table><tbody>{rows}</tbody></table></figure>\n<!-- /wp:table -->\n\n'
    content += '<!-- wp:paragraph -->\n<p>Oat, soya and almond milk at no extra charge. Please ask about allergens.</p>\n<!-- /wp:paragraph -->'
    menu = call('POST', '/wp/v2/pages', {'title': 'Menu', 'slug': 'menu', 'status': 'publish', 'content': content})
    home = one('page', 'home')
    raw = home['content']['raw'].replace('See our menu</a>', 'Download the menu (PDF)</a>')
    link = f'<!-- wp:paragraph -->\n<p><a href="{menu["link"]}">See our menu</a></p>\n<!-- /wp:paragraph -->\n\n'
    at = raw.find('<!-- wp:file')
    call('POST', f"/wp/v2/pages/{home['id']}", {'content': raw[:at] + link + raw[at:]})
