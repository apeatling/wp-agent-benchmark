# The prices live in the page's Elementor data (_elementor_data, which the REST API exposes as page meta): change
# them there, keeping the layout, then clear Elementor's cache so the page is rebuilt. Then the call-out fee.

def solve():
    page = one('page', 'services')
    data = json.loads(page['meta']['_elementor_data'])
    new = {'£85': '£95', '£70': '£80', '£60': '£70', '£55': '£65'}

    def walk(elements):
        for el in elements:
            title = el.get('settings', {}).get('title')
            if title in new:
                el['settings']['title'] = new[title]
            walk(el.get('elements', []))
    walk(data)
    call('POST', f"/wp/v2/pages/{page['id']}", {'meta': {'_elementor_data': json.dumps(data)}})
    call('DELETE', '/elementor/v1/cache')
