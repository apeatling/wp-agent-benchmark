# One front page with the hours, the address and the parking, as the owner gives them when asked; the site named,
# and WordPress's example post and page taken down.

def solve():
    para = lambda t: f'<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->\n\n'
    content = ('<!-- wp:heading -->\n<h2 class="wp-block-heading">Opening hours</h2>\n<!-- /wp:heading -->\n\n'
               + para('Monday to Saturday: 8:30am to 5:30pm<br>Sunday: 10am to 2pm')
               + '<!-- wp:heading -->\n<h2 class="wp-block-heading">How to find us</h2>\n<!-- /wp:heading -->\n\n'
               + para('3 Quay Road, Portwen PW1 4QT')
               + para('There’s free parking behind the shop: you get to it from Back Lane.')
               + para('Call us on 01632 960271.'))
    home = call('POST', '/wp/v2/pages', {'title': 'Penrose Hardware', 'slug': 'home', 'status': 'publish', 'content': content})
    call('POST', '/wp/v2/settings', {'title': 'Penrose Hardware', 'show_on_front': 'page', 'page_on_front': home['id']})
    call('DELETE', f"/wp/v2/posts/{one('post', 'hello-world')['id']}")
    call('DELETE', f"/wp/v2/pages/{one('page', 'sample-page')['id']}")
