# A front page with everything from the owner's notes and photos, the prices on it, the site named, and
# WordPress's example post and page taken down.

def solve():
    photos = [{**upload(f'/app/{name}', alt=alt), 'alt_text': alt} for name, alt in [
        ('shop front.jpg', 'Scruffs Dog Grooming on Mill Lane'), ('IMG_2041.jpg', 'A freshly groomed dog'),
        ('IMG_2077.jpg', 'A dog after a bath and brush')]]
    image = lambda m: (f'<!-- wp:image {{"id":{m["id"]},"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large">'
                       f'<img src="{m["source_url"]}" alt="{m["alt_text"]}" class="wp-image-{m["id"]}"/></figure>\n<!-- /wp:image -->\n\n')
    para = lambda t: f'<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->\n\n'
    prices = ''.join(f'<!-- wp:list-item -->\n<li>{t}</li>\n<!-- /wp:list-item -->' for t in [
        'Full groom, small dog: £35', 'Full groom, medium dog: £42', 'Full groom, large dog: £50', 'Bath and brush: £25',
        'Puppy intro groom (under 6 months): £20', 'Nail clip: £8'])
    content = (image(photos[0]) + para('Friendly dog grooming in Portwen. One dog at a time, no cages and no rushing.')
               + '<!-- wp:heading -->\n<h2 class="wp-block-heading">Prices</h2>\n<!-- /wp:heading -->\n\n'
               + f'<!-- wp:list -->\n<ul class="wp-block-list">{prices}</ul>\n<!-- /wp:list -->\n\n'
               + para('Walk-ins welcome for nail clips; everything else is by appointment.')
               + image(photos[1]) + image(photos[2])
               + '<!-- wp:heading -->\n<h2 class="wp-block-heading">Find us</h2>\n<!-- /wp:heading -->\n\n'
               + para('Unit 2, Mill Lane, Portwen PW2 3HB, round the back of the garden centre, with parking right outside.')
               + para('Open Tuesday to Saturday, 9am to 5pm. Call 01632 960412 or email hello@scruffsgrooming.test.')
               + para('Kerry Nance has been grooming for 12 years and is City &amp; Guilds Level 3 qualified.'))
    home = call('POST', '/wp/v2/pages', {'title': 'Scruffs Dog Grooming', 'slug': 'home', 'status': 'publish', 'content': content})
    call('POST', '/wp/v2/settings', {'title': 'Scruffs Dog Grooming', 'description': 'Dog grooming in Portwen',
                                     'show_on_front': 'page', 'page_on_front': home['id']})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
