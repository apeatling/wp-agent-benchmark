# A front page with the owner's six photos in a gallery, captioned from her notes, and the line about
# commissions at the top (her follow-up); the site named, and WordPress's example post and page taken down.

def solve():
    pieces = [('oak dresser', 'A 1920s oak dresser, stripped of its magnolia paint, with new back boards, and waxed'),
              ('pine blanket box', 'A pine blanket box, its split lid glued and cleated, with new hinges'),
              ('walnut writing desk', 'A walnut writing desk, its lifting veneer relaid and French polished'),
              ('mahogany side table', 'A mahogany side table, water rings gone and the wobbly leg fixed'),
              ('ladderback chairs', 'A set of four ladderback chairs with their rush seats redone'),
              ('elm chest of drawers', 'An elm chest of drawers with new runners and cleaned-up handles')]
    photos = [{**upload(f'/app/{name}.jpg', alt=alt), 'alt_text': alt, 'caption': name.capitalize()} for name, alt in pieces]
    image = lambda m: (f'<!-- wp:image {{"id":{m["id"]},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                       f'<figure class="wp-block-image size-large"><img src="{m["source_url"]}" alt="{m["alt_text"]}" class="wp-image-{m["id"]}"/>'
                       f'<figcaption class="wp-element-caption">{m["caption"]}</figcaption></figure>\n<!-- /wp:image -->\n\n')
    para = lambda t: f'<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->\n\n'
    content = (para('<strong>I take commissions: if you have a piece that needs some love, '
                    '<a href="mailto:tamsin@tamsinrestores.test">email me</a>.</strong>')
               + para('I’m Tamsin, and I restore old furniture in Portwen. Here are some of my favourite pieces.')
               + '<!-- wp:gallery {"linkTo":"none"} -->\n<figure class="wp-block-gallery has-nested-images columns-default is-cropped">'
               + ''.join(image(p) for p in photos) + '</figure>\n<!-- /wp:gallery -->')
    home = call('POST', '/wp/v2/pages', {'title': 'Tamsin Restores', 'slug': 'home', 'status': 'publish', 'content': content})
    call('POST', '/wp/v2/settings', {'title': 'Tamsin Restores', 'description': 'Furniture restoration in Portwen',
                                     'show_on_front': 'page', 'page_on_front': home['id']})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
