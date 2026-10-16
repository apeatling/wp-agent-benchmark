# A shop: WooCommerce, in pounds, with the ten candles from the spreadsheet in stock, UK shipping at £3.95 a parcel,
# and a link to the shop on the front page. Payments are left for the owner to choose.

import csv


def solve():
    call('POST', '/wp/v2/plugins', {'slug': 'woocommerce', 'status': 'active'})
    for key, value in [('woocommerce_currency', 'GBP'), ('woocommerce_default_country', 'GB'),
                       ('woocommerce_specific_allowed_countries', ['GB']), ('woocommerce_allowed_countries', 'specific')]:
        call('PUT', f'/wc/v3/settings/general/{key}', {'value': value})
    zone = call('POST', '/wc/v3/shipping/zones', {'name': 'UK'})
    call('PUT', f"/wc/v3/shipping/zones/{zone['id']}/locations", [{'code': 'GB', 'type': 'country'}])
    method = call('POST', f"/wc/v3/shipping/zones/{zone['id']}/methods", {'method_id': 'flat_rate'})
    call('PUT', f"/wc/v3/shipping/zones/{zone['id']}/methods/{method['instance_id']}", {'settings': {'cost': '3.95', 'title': 'Royal Mail'}})
    with open('/app/candles.csv', newline='') as f:
        for row in csv.DictReader(f):
            call('POST', '/wc/v3/products', {
                'name': row['Candle'], 'type': 'simple', 'status': 'publish', 'regular_price': row['Price'].lstrip('£'),
                'description': f"<p>Scented with {row['Scent']}. A {row['Size']}, burns for about {row['Burn time']}.</p>",
                'short_description': f"{row['Size']}, about {row['Burn time']}.",
                'manage_stock': True, 'stock_quantity': int(row["How many we've got"])})
    shop = call('GET', '/wp/v2/pages?slug=shop')[0]
    home = one('page', 'home')
    link = f'\n\n<!-- wp:paragraph -->\n<p><a href="{shop["link"]}">Shop our candles</a></p>\n<!-- /wp:paragraph -->'
    call('POST', f"/wp/v2/pages/{home['id']}", {'content': home['content']['raw'] + link})
