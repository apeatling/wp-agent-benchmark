# The Christmas cake as a new product, with its photo, through WooCommerce's REST API.

def solve():
    media = upload('/app/christmas-cake.jpg', alt='Christmas cake')
    cakes = next(c for c in call('GET', '/wc/v3/products/categories?per_page=100') if c['slug'] == 'seasonal')
    call('POST', '/wc/v3/products', {
        'name': 'Christmas cake', 'type': 'simple', 'status': 'publish', 'regular_price': '28',
        'description': '<p>Our rich fruit cake, 8 inches, with marzipan and royal icing.</p>',
        'short_description': 'Order by 20 December, collect from the 21st.',
        'categories': [{'id': cakes['id']}], 'images': [{'id': media['id']}],
    })
