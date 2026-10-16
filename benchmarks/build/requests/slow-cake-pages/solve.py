# Switch off the plugin that waits on the courier on every page, and show the photos in each cake's description at
# the large size WordPress already made of each one, instead of the camera originals.

def solve():
    call('POST', '/wp/v2/plugins/sunnyside-delivery/sunnyside-delivery', {'status': 'inactive'})
    for slug in ('chocolate-celebration-cake', 'victoria-sponge', 'lemon-drizzle-loaf'):
        product = call('GET', f'/wc/v3/products?slug={slug}')[0]
        desc = product['description']
        for src in set(re.findall(r'<img[^>]*src="([^"]+)"', desc)):
            media = call('GET', '/wp/v2/media?search=' + urllib.parse.quote(src.rsplit('/', 1)[-1].rsplit('.', 1)[0]))
            sizes = media[0]['media_details']['sizes'] if media else {}
            smaller = (sizes.get('large') or sizes.get('medium_large') or sizes.get('medium') or {}).get('source_url')
            if smaller:
                desc = desc.replace(src, smaller)
        call('PUT', f"/wc/v3/products/{product['id']}", {'description': desc})
